#!/usr/bin/env python3
"""
HONEST MPA fee + claimable revenue report.

Queries the BitShares chain live over websocket RPC and writes a markdown
report to OUT_PATH (defaults to ../docs/honest_fees_report.md).

Per asset it collects:
  - maker fee (market_fee_percent) and taker fee (taker_fee_percent ext)
  - max_market_fee and the charge_market_fee flag
  - claimable revenue: accumulated_fees (in the asset itself) and
    accumulated_collateral_fees (in BTS for these BTS-collateralized MPAs),
    both converted to an approximate BTS value via each MPA's median feed
  - market fee sharing vestings on the issuer account (honest-quorum)

Reference for the revenue pattern: tools/calculate_fees.py
"""

import json
import os
import sys
from datetime import datetime, timezone

import websocket

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config_nodes import public_nodes  # noqa: E402
from config_tokens import MPAS  # noqa: E402

OUT_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "docs", "honest_fees_report.md")
)

NETWORK_ASSET_ID = "1.3.0"
NETWORK_PRECISION = 5

# BTC-collateralized MPAs have a median feed denominated in HONEST.BTC, not
# BTS. To value their accumulated fees we reuse the BTS per-asset factor of
# their BTS-backed counterpart (same underlying, BTS-collateralized).
FEED_COUNTERPARTS = {
    "HONEST.ETH1": "HONEST.ETH",
    "HONEST.XRP1": "HONEST.XRP",
}


def md_table(headers, rows):
    """
    Render a markdown table with consistently padded (fixed-width) columns.

    Every cell is padded to the width of the widest entry in its column so
    columns line up in monospace-rendered output.
    """
    table = [list(headers)] + [list(r) for r in rows]
    widths = []
    for col in range(len(headers)):
        widths.append(max(len(str(cells[col])) for cells in table))
    lines = []
    lines.append(
        "| "
        + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(table[0]))
        + " |"
    )
    lines.append(
        "| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |"
    )
    for row in table[1:]:
        lines.append(
            "| "
            + " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(row))
            + " |"
        )
    return lines


class RPC:
    """Minimal websocket JSON-RPC wrapper for a BitShares node."""

    def __init__(self, ws):
        self.ws = ws
        self._id = 0
        self.database = None  # type: int | None

    def call(self, api, method, params):
        self._id += 1
        mid = self._id
        self.ws.send(
            json.dumps({"id": mid, "method": "call", "params": [api, method, params]})
        )
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == mid:
                return msg.get("result")

    def db(self, method, params):
        if self.database is None:
            raise RuntimeError("database api id not resolved")
        return self.call(self.database, method, params)


def connect():
    """Return an (RPC, node_url) pair with the database api id discovered."""
    for url in public_nodes():
        try:
            ws = websocket.create_connection(url, timeout=20, header={"User-Agent": "wscat"})
        except Exception:
            continue
        rpc = RPC(ws)
        try:
            rpc.call(1, "login", ["", ""])
        except Exception:
            ws.close()
            continue
        for probe in range(0, 14):
            try:
                r = rpc.call(probe, "get_assets", [["1.3.0"]])
                if r and r[0] and r[0].get("symbol") == "BTS":
                    rpc.database = probe
                    return rpc, url
            except Exception:
                continue
        ws.close()
    raise SystemExit("no working public node")


def get_objects(rpc, object_ids):
    """Chunked get_objects returning id -> object dict."""
    out = {}
    ids = list(object_ids)
    for i in range(0, len(ids), 90):
        chunk = ids[i : i + 90]
        res = rpc.db("get_objects", [chunk])
        for idx, obj in enumerate(res or []):
            if obj:
                out[chunk[idx]] = obj
    return out


def get_feed_bts_per_asset(rpc, asset_id, bitasset_data_id):
    """
    Return (bts_per_asset, found) using the MPA's median oracle feed.
    """
    try:
        data = get_objects(rpc, [bitasset_data_id]).get(bitasset_data_id)
        if not data:
            return None, False
        feed = (data.get("median_feed") or {}).get("settlement_price")
        if not feed:
            return None, False
        prices = {}
        for side in (feed["base"], feed["quote"]):
            a_id = side["asset_id"]
            obj = get_objects(rpc, [a_id]).get(a_id)
            if obj:
                prices[a_id] = int(side["amount"]) / 10 ** obj["precision"]
        if NETWORK_ASSET_ID in prices and asset_id in prices:
            return prices[NETWORK_ASSET_ID] / prices[asset_id], True
    except Exception:
        return None, False
    return None, False


def to_units(amount, precision):
    return amount / 10 ** precision


def main():
    rpc, node_url = connect()

    symbols = sorted(MPAS.keys())
    assets = {}
    for i in range(0, len(symbols), 25):
        res = rpc.db("lookup_asset_symbols", [symbols[i : i + 25]])
        for obj in res or []:
            if obj:
                assets[obj["symbol"]] = obj

    dyn_ids = [assets[s]["dynamic_asset_data_id"] for s in symbols]
    bit_ids = [
        assets[s]["bitasset_data_id"]
        for s in symbols
        if assets[s].get("bitasset_data_id")
    ]
    dyn = get_objects(rpc, dyn_ids)
    bit = get_objects(rpc, list(dict.fromkeys(bit_ids)))

    # Precompute BTS-per-asset feed factor for every MPA that has a BTS feed.
    feed_factor = {}
    for s in symbols:
        a = assets[s]
        if not a.get("bitasset_data_id"):
            continue
        f, ok = get_feed_bts_per_asset(rpc, a["id"], a["bitasset_data_id"])
        if ok:
            feed_factor[s] = f

    rows = []
    for s in symbols:
        a = assets[s]
        opt = a["options"]
        mfp = opt.get("market_fee_percent", 0)
        ext = opt.get("extensions") or {}
        tfp = ext.get("taker_fee_percent")
        maker = mfp / 100
        taker = (tfp if tfp is not None else mfp) / 100
        charge_fee = bool(opt.get("flags", 0) & 0x01)
        max_fee = opt.get("max_market_fee")

        data = dyn.get(a["dynamic_asset_data_id"]) or {}
        accum_asset = int(data.get("accumulated_fees") or 0)
        accum_collat = int(data.get("accumulated_collateral_fees") or 0)

        bts_per_asset = feed_factor.get(s)
        feed_note = None
        if bts_per_asset is None:
            counterpart = FEED_COUNTERPARTS.get(s)
            if counterpart in feed_factor:
                bts_per_asset = feed_factor[counterpart]
                feed_note = f"via {counterpart}"

        bts_value = None
        if bts_per_asset is not None:
            bts_value = to_units(accum_asset, a["precision"]) * bts_per_asset
        collat_h = to_units(accum_collat, NETWORK_PRECISION)

        rows.append(
            {
                "symbol": s,
                "id": a["id"],
                "precision": a["precision"],
                "maker_bp": mfp,
                "taker_bp": tfp,
                "maker": maker,
                "taker": taker,
                "explicit_taker": tfp is not None,
                "charge_fee": charge_fee,
                "max_fee": max_fee,
                "accum_asset_sat": accum_asset,
                "accum_asset_h": to_units(accum_asset, a["precision"]),
                "accum_collat_h": collat_h,
                "feed_found": feed_note is None,
                "feed_note": feed_note,
                "bts_value": bts_value,
            }
        )

    issuer = assets[symbols[0]].get("issuer")
    vesting = {}
    vesting_node = None

    def fetch_vesting(rpc_conn, url):
        nonlocal vesting, vesting_node
        try:
            bal = rpc_conn.db("get_vesting_balances", [issuer])
        except Exception:
            return
        if bal is None:
            return
        for v in bal:
            bal_obj = v.get("balance") or {}
            if "asset_id" not in bal_obj:
                continue
            vesting[bal_obj["asset_id"]] = int(bal_obj.get("amount") or 0)
        vesting_node = url

    fetch_vesting(rpc, node_url)
    if not vesting:
        try:
            v_rpc, v_url = connect()
        except SystemExit:
            v_rpc = None
            v_url = None
        if v_rpc:
            fetch_vesting(v_rpc, v_url)
            try:
                v_rpc.ws.close()
            except Exception:
                pass

    head_obj = get_objects(rpc, ["2.1.0"]).get("2.1.0")
    head = head_obj.get("head_block_number") if head_obj else None

    L = []
    L.append("# HONEST Market Pegged Assets — Fees & Claimable Revenue")
    L.append("")
    L.append(
        f"Generated {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')} UTC "
        f"from live blockchain data (head block {head} via {node_url})."
    )
    L.append("")
    L.append(
        "Fee semantics (BSIP-81): `market_fee_percent` = **maker** fee, "
        "`taker_fee_percent` (asset extension) = **taker** fee. When "
        "`taker_fee_percent` is unset the taker fee falls back to the maker "
        "rate. Percent values are stored in hundredths of a percent (100 == 1%)."
    )
    L.append("")

    L.append("## 1. Maker / Taker Fees")
    L.append("")
    L.append(
        "Columns uniformly padded by `md_table` helper so the table lines up "
        "even in fixed-width output."
    )
    L.append("")
    headers = ["Asset", "Maker", "Taker", "taker explicit", "max_market_fee", "fee enabled"]
    body = [
        [
            r["symbol"],
            f"{r['maker']:.2f}%",
            f"{r['taker']:.2f}%",
            "yes" if r["explicit_taker"] else "no (same as maker)",
            str(r["max_fee"]),
            "yes" if r["charge_fee"] else "NO",
        ]
        for r in rows
    ]
    L.extend(md_table(headers, body))
    L.append("")

    L.append("## 2. Claimable / Accumulated Fees (unclaimed revenue)")
    L.append("")
    L.append(
        "`accumulated_fees` sit in each asset's dynamic object and are claimable "
        "by the issuer (e.g. via `asset_claim_fees`) _in that asset_. "
        "`accumulated_collateral_fees` are BTS collected from margin calls. "
        "The `~value (BTS)` column converts the on-chain `accumulated_fees` "
        "from MPA units into BTS using the MPA's live median feed: "
        "`value = accumulated_fees/10^precision * (feed_quote_BTS / feed_base_MPA)`."
    )
    L.append("")
    L.append(
        "**BTC-collateralized MPAs (HONEST.ETH1, HONEST.XRP1) have a feed "
        "denominated in HONEST.BTC, not BTS.** For those, the BTS per-asset "
        "factor of their BTS-backed counterpart (HONEST.ETH / HONEST.XRP) is "
        "used instead; this is shown in the `feed` column as `via <counterpart>`."
    )
    L.append("")
    headers = ["Asset", "accumulated_fees (asset units)", "~value (BTS)", "accumulated_collat (BTS)", "feed"]
    body = []
    for r in rows:
        asset_str = f"{r['accum_asset_h']:.4f}"
        bts_v = f"{r['bts_value']:.2f}" if r["bts_value"] is not None else "n/a"
        feed = "yes" if r["feed_found"] else (r["feed_note"] if r["feed_note"] else "no")
        body.append([r["symbol"], asset_str, bts_v, f"{r['accum_collat_h']:.2f}", feed])
    L.extend(md_table(headers, body))
    L.append("")

    total_asset = sum((r["bts_value"] or 0) for r in rows)
    total_collat = sum(r["accum_collat_h"] for r in rows)
    L.append("### Totals")
    L.append("")
    L.append(f"- **accumulated fees (BTS value, approx):** {total_asset:,.2f} BTS")
    L.append(f"- **accumulated collateral fees:** {total_collat:,.2f} BTS")
    L.append(f"- **combined claimable (approx):** {total_asset + total_collat:,.2f} BTS")
    L.append("")

    L.append("## 3. Issuer Market-Fee-Sharing Vestings")
    L.append("")
    if vesting:
        id_to_sym = {a["id"]: s for s, a in assets.items()}
        ids = list(vesting.keys())
        if len(ids) <= 90:
            objs = get_objects(rpc, ids)
        else:
            objs = get_objects(rpc, ids[:90])
        for aid, amt in sorted(vesting.items(), key=lambda kv: -kv[1]):
            obj = objs.get(aid)
            name = obj["symbol"] if obj else id_to_sym.get(aid, aid)
            prec = obj["precision"] if obj else 0
            L.append(f"- `{name}` (`{aid}`): {amt / 10 ** prec:.2f} ({amt} satoshis)")
        if vesting_node:
            L.append(f"*(via {vesting_node})*")
    else:
        L.append("None returned by any node.")
    L.append("")

    L.append("---")
    L.append("Generated by `honest/fee_report.py`. Read-only; does not modify the chain.")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
