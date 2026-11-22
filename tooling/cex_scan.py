"""
Measure live CEX source coverage for HONEST coins against BTC, USD, and USDT.

Reads the coin universe from honest/exchanges.py, queries ccxt exchanges, and
renders a coverage table plus an accuracy plot. Nothing here modifies the feed;
the feed's own source table is only read.
"""

import argparse
import asyncio
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ccxt.async_support as ccxt_async

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "honest"))

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from exchanges import BLACKLIST, EXCHANGES
from utilities import correct_pair

HERE = Path(__file__).resolve().parent

QUOTES = ["BTC", "USD", "USDT"]
TARGET_SOURCES = 5


def coins_from_exchanges(exchanges):
    """Base coins the feed needs, from its pair table."""
    return sorted({pair.split(":")[0] for pair in exchanges})


def candidate_symbols(exchange, coin, quote):
    """Symbols to try, in order, for one coin and quote on one exchange."""
    literal = f"{coin}/{quote}"
    corrected = correct_pair(exchange, literal)
    return [literal] if corrected == literal else [corrected, literal]


def prices_from_tickers(tickers, chosen):
    """Honest-pair -> last price, dropping None, zero, and missing tickers."""
    prices = {}
    for pair, symbol in chosen.items():
        last = (tickers.get(symbol) or {}).get("last")
        if last is not None and last > 0:
            prices[pair] = last
    return prices


def _float(value):
    """A float, or None when the value is missing or not numeric."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def volumes_from_tickers(tickers, chosen):
    """Honest-pair -> 24h base-coin volume, from baseVolume or quoteVolume/last."""
    volumes = {}
    for pair, symbol in chosen.items():
        row = tickers.get(symbol) or {}
        base = _float(row.get("baseVolume"))
        if base is not None and base > 0:
            volumes[pair] = base
            continue
        quote = _float(row.get("quoteVolume"))
        last = _float(row.get("last"))
        if quote is not None and last is not None and quote > 0 and last > 0:
            volumes[pair] = quote / last
    return volumes


def live_sources(results, coins, quotes):
    """Coin -> quote -> sorted exchanges with a live price."""
    sources = {coin: {quote: [] for quote in quotes} for coin in coins}
    for exchange, row in results.items():
        if not row.get("ok"):
            continue
        for pair, price in row.get("prices", {}).items():
            coin, _, quote = pair.partition(":")
            if price and coin in sources and quote in sources[coin]:
                sources[coin][quote].append(exchange)
    for coin in sources:
        for quote in sources[coin]:
            sources[coin][quote].sort()
    return sources


def tier_reach(sources, quotes=QUOTES, target=TARGET_SOURCES):
    """First quote in preference order at which unique sources reach target."""
    seen = set()
    for quote in quotes:
        seen.update(sources.get(quote, []))
        if len(seen) >= target:
            return quote
    return "MISSING"


def deviations(results):
    """Exchange -> percent deviation from each (coin, quote) group median."""
    groups = {}
    for exchange, row in results.items():
        if not row.get("ok"):
            continue
        for pair, price in row.get("prices", {}).items():
            if not price:
                continue
            coin, _, quote = pair.partition(":")
            groups.setdefault((coin, quote), []).append((exchange, price))
    out = {}
    for values in groups.values():
        if len(values) < 2:
            continue
        median = statistics.median(price for _, price in values)
        for exchange, price in values:
            out.setdefault(exchange, []).append((price / median - 1) * 100)
    return out


def _cumulative_counts(sources, quotes):
    seen = set()
    for quote in quotes:
        seen.update(sources.get(quote, []))
        yield len(seen)


def _fixed_table(header, rows):
    """A fenced, column-padded table that reads as columns in any editor."""
    table = [list(header)] + [list(row) for row in rows]
    widths = [max(len(str(row[i])) for row in table) for i in range(len(header))]
    lines = [
        "  ".join(str(cell).ljust(width) for cell, width in zip(row, widths))
        for row in table
    ]
    return "```\n" + "\n".join(lines) + "\n```"


def coin_volumes(results):
    """Coin -> exchange -> summed 24h base volume across its live quote markets."""
    volumes = {}
    for exchange, row in results.items():
        if not row.get("ok"):
            continue
        for pair, volume in row.get("volumes", {}).items():
            if not volume or volume <= 0:
                continue
            coin = pair.partition(":")[0]
            bucket = volumes.setdefault(coin, {})
            bucket[exchange] = bucket.get(exchange, 0.0) + volume
    return volumes


def shares_by_coin(volumes):
    """Coin -> exchange -> percent of that coin's reported volume."""
    shares = {}
    for coin, by_exchange in volumes.items():
        total = sum(by_exchange.values())
        if total <= 0:
            continue
        shares[coin] = {
            name: volume / total * 100 for name, volume in by_exchange.items()
        }
    return shares


def format_table(results, coins, quotes, unreachable, blacklist):
    """Three fixed-width price tables (BTC, USD, USDT base) plus summary lines.

    Each table: exchanges as rows, coins as columns, price as the cell.
    Only exchanges with at least one live price in that base are listed.
    """
    blocked = set(blacklist)
    sections = []

    for quote in quotes:
        # Coins with at least one live price in this quote base
        coins_with_quote = []
        for coin in coins:
            has_price = False
            for row in results.values():
                if not row.get("ok"):
                    continue
                price = row.get("prices", {}).get(f"{coin}:{quote}")
                if price is not None and price > 0:
                    has_price = True
                    break
            if has_price:
                coins_with_quote.append(coin)

        if not coins_with_quote:
            continue

        # Exchanges with at least one live price in this quote base
        exchange_rows = []
        for exchange, row in results.items():
            if not row.get("ok") or exchange in blocked:
                continue
            prices = row.get("prices", {})
            if any(
                prices.get(f"{coin}:{quote}") is not None
                and prices.get(f"{coin}:{quote}") > 0
                for coin in coins_with_quote
            ):
                exchange_rows.append(exchange)

        header = ["exchange"] + coins_with_quote
        rows = []
        for exchange in sorted(exchange_rows):
            prices = results[exchange].get("prices", {})
            row = [exchange]
            for coin in coins_with_quote:
                price = prices.get(f"{coin}:{quote}")
                if price is not None and price > 0:
                    row.append(f"{price:g}")
                else:
                    row.append("-")
            rows.append(row)

        sections.append(f"### {quote} base\n\n" + _fixed_table(header, rows))

    # Summary: coins below target sources across all quotes
    missing = []
    for coin in coins:
        total = 0
        for q in quotes:
            seen = set()
            for exchange, row in results.items():
                if not row.get("ok") or exchange in seen:
                    continue
                price = row.get("prices", {}).get(f"{coin}:{q}")
                if price is not None and price > 0:
                    seen.add(exchange)
            total += len(seen)
        if total < TARGET_SOURCES:
            missing.append(coin)

    text = "\n\n".join(sections)
    text += "\n\n"
    text += "blacklisted: " + (", ".join(sorted(blocked)) if blocked else "none")
    text += "\nunreachable: " + (", ".join(unreachable) if unreachable else "none")
    text += "\nmissing: " + (", ".join(missing) if missing else "none")
    return text


def _format_volume(volume):
    """Two decimals above one coin; scientific below, so tiny volumes never read 0.00."""
    if volume >= 1:
        return f"{volume:,.2f}"
    return f"{volume:.2e}"


def format_volume_sections(volumes, shares, coins, blacklist):
    """One fixed-width section per coin, exchanges sorted by volume descending."""
    blocked = set(blacklist)
    sections = []
    for coin in coins:
        by_exchange = {
            name: volume
            for name, volume in volumes.get(coin, {}).items()
            if name not in blocked
        }
        body = [
            [name, _format_volume(volume), f"{shares[coin][name]:.1f}%"]
            for name, volume in sorted(
                by_exchange.items(), key=lambda item: (-item[1], item[0])
            )
            if name in shares.get(coin, {})
        ]
        section = [f"### {coin}", ""]
        if body:
            section.append(_fixed_table(["exchange", "volume", "share"], body))
        else:
            section.append("no reported 24 h volume")
        sections.append("\n".join(section))
    header = (
        "volume: 24 h base-coin volume per exchange, descending; "
        "blacklisted exchanges are omitted here and included in the volume figure."
    )
    return header + "\n\n" + "\n\n".join(sections)


def _default_exchange(name):
    return getattr(ccxt_async, name)({"enableRateLimit": True, "timeout": 20000})


async def _fetch_tickers(exchange, symbols, request_timeout):
    """One batched request, falling back to individual fetches when rejected."""
    try:
        return await asyncio.wait_for(exchange.fetch_tickers(symbols), request_timeout)
    except ccxt_async.NotSupported:
        pass
    except Exception as error:
        if "symbol" not in str(error).lower():
            raise
    tickers = {}
    for symbol in symbols:
        tickers[symbol] = await asyncio.wait_for(
            exchange.fetch_ticker(symbol), request_timeout
        )
    return tickers


async def _scan_one(
    name,
    coins,
    quotes,
    semaphore,
    make_exchange,
    request_timeout,
    exchange_deadline,
):
    async with semaphore:
        started = time.time()
        exchange = None
        try:
            exchange = make_exchange(name)

            async def work():
                await exchange.load_markets()
                chosen = {}
                for coin in coins:
                    for quote in quotes:
                        for symbol in candidate_symbols(name, coin, quote):
                            if symbol in exchange.markets:
                                chosen[f"{coin}:{quote}"] = symbol
                                break
                if not chosen:
                    return {}, {}
                tickers = await _fetch_tickers(
                    exchange, list(chosen.values()), request_timeout
                )
                return (
                    prices_from_tickers(tickers, chosen),
                    volumes_from_tickers(tickers, chosen),
                )

            prices, volumes = await asyncio.wait_for(work(), exchange_deadline)
            return {
                "ok": True,
                "error": None,
                "seconds": round(time.time() - started, 1),
                "prices": prices,
                "volumes": volumes,
            }
        except Exception as error:
            return {
                "ok": False,
                "error": type(error).__name__,
                "seconds": round(time.time() - started, 1),
                "prices": {},
                "volumes": {},
            }
        finally:
            if exchange is not None:
                try:
                    await exchange.close()
                except Exception:
                    pass


async def scan(
    exchange_names,
    coins,
    quotes,
    concurrency=20,
    request_timeout=20,
    exchange_deadline=90,
    make_exchange=None,
):
    """Query every exchange concurrently; failures are recorded, never zeroed."""
    make_exchange = make_exchange or _default_exchange
    semaphore = asyncio.Semaphore(concurrency)
    rows = await asyncio.gather(
        *(
            _scan_one(
                name,
                coins,
                quotes,
                semaphore,
                make_exchange,
                request_timeout,
                exchange_deadline,
            )
            for name in exchange_names
        )
    )
    return {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "coins": list(coins),
        "quotes": list(quotes),
        "exchanges": dict(zip(exchange_names, rows)),
    }


def save_cache(path, cache):
    """Write the scan cache as indented JSON."""
    Path(path).write_text(json.dumps(cache, indent=2))


def load_cache(path):
    """Read a cache written by save_cache."""
    return json.loads(Path(path).read_text())


QUOTE_COLORS = {"BTC": "#f7931a", "USD": "#1f77b4", "USDT": "#17becf"}


def make_plot(results, sources, coins, quotes, path):
    """Coverage bars per coin and per-exchange deviation boxes, to PNG."""
    blocked = set(BLACKLIST)
    plot_sources = {
        coin: {
            quote: [e for e in sources[coin].get(quote, []) if e not in blocked]
            for quote in quotes
        }
        for coin in coins
    }
    totals = {
        coin: len({e for quote in quotes for e in plot_sources[coin][quote]})
        for coin in coins
    }
    ordered = sorted(coins, key=lambda coin: (totals[coin], coin))

    figure, (left, right) = plt.subplots(
        1,
        2,
        figsize=(16, max(6, 0.3 * len(coins) + 4)),
        gridspec_kw={"width_ratios": [1, 1.4]},
    )

    for row, coin in enumerate(ordered):
        start = 0
        seen = set()
        for quote in quotes:
            fresh = set(plot_sources[coin][quote]) - seen
            seen |= fresh
            if fresh:
                left.barh(
                    row,
                    len(fresh),
                    left=start,
                    color=QUOTE_COLORS[quote],
                    edgecolor="white",
                )
                start += len(fresh)
    left.axvline(TARGET_SOURCES, color="red", linestyle="--", linewidth=1)
    left.annotate(
        f"{TARGET_SOURCES} sources",
        xy=(TARGET_SOURCES, 0.99),
        xycoords=("data", "axes fraction"),
        ha="left",
        va="top",
        fontsize=8,
        color="red",
    )
    left.set_yticks(range(len(ordered)))
    left.set_yticklabels(ordered)
    left.set_xlabel("live sources")
    left.set_title("live sources per coin, by quote (blacklist excluded)")
    left.legend(
        handles=[Patch(color=QUOTE_COLORS[q], label=q) for q in quotes],
        title="quote",
        loc="lower right",
    )
    left.grid(axis="x", alpha=0.3)

    dev = deviations(results)
    plotted = {name: vals for name, vals in dev.items() if len(vals) >= 3}
    if len(plotted) >= 2:
        names = sorted(
            plotted,
            key=lambda name: statistics.median(abs(v) for v in plotted[name]),
            reverse=True,
        )
        right.boxplot(
            [plotted[name] for name in names],
            orientation="horizontal",
            tick_labels=names,
            showfliers=True,
        )
        right.axvline(0, color="black", linewidth=1)
        pooled = [value for values in plotted.values() for value in values]
        low, high = (
            statistics.quantiles(pooled, n=100)[0],
            statistics.quantiles(pooled, n=100)[-1],
        )
        span = max(high - low, 2.0)
        low, high = low - 0.1 * span, high + 0.1 * span
        outside = sum(1 for value in pooled if not low <= value <= high)
        right.set_xlim(low, high)
        right.set_xlabel("% deviation from the (coin, quote) median")
        right.set_title(
            f"{len(names)} exchanges with 3+ observations, "
            f"sorted by median absolute deviation "
            f"({outside} points outside the axis)"
        )
        right.tick_params(axis="y", labelsize=7)
        right.grid(axis="x", alpha=0.3)
    else:
        right.axis("off")
        right.set_title("not enough exchanges with 3+ observations")

    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def make_volume_plot(results, coins, path):
    """Per-exchange share of each coin's volume, boxed, largest share at the top."""
    shares = shares_by_coin(coin_volumes(results))
    pooled = {}
    for coin in coins:
        for exchange, share in shares.get(coin, {}).items():
            pooled.setdefault(exchange, []).append(share)
    plotted = {name: values for name, values in pooled.items() if len(values) >= 3}

    figure, axis = plt.subplots(figsize=(14, max(6, 0.25 * len(plotted) + 2)))
    if len(plotted) >= 2:
        names = sorted(plotted, key=lambda name: statistics.median(plotted[name]))
        axis.boxplot(
            [plotted[name] for name in names],
            orientation="horizontal",
            tick_labels=names,
            showfliers=True,
        )
        axis.set_xlim(0, 102)
        axis.set_xlabel("% of the coin's 24 h volume")
        axis.set_title(f"{len(names)} exchanges with 3+ coin shares, by median share")
        axis.tick_params(axis="y", labelsize=7)
        axis.grid(axis="x", alpha=0.3)
    else:
        axis.axis("off")
        axis.set_title("not enough exchanges with 3+ coin shares")

    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Measure live CEX source coverage per HONEST coin."
    )
    parser.add_argument("--exchanges", help="comma separated ccxt names")
    parser.add_argument("--quotes", default=",".join(QUOTES))
    parser.add_argument("--from-json", help="render from a saved cache, no network")
    parser.add_argument("--json", help="cache path (default: tooling/cex_sources.json)")
    parser.add_argument("--png", default=str(HERE / "cex_sources.png"))
    parser.add_argument(
        "--volume-png", default=str(HERE / "cex_volume.png"), help="volume figure"
    )
    parser.add_argument("--md", default=str(HERE / "cex_sources.md"))
    args = parser.parse_args(argv)

    quotes = [q.strip().upper() for q in args.quotes.split(",") if q.strip()]
    if args.from_json:
        cache = load_cache(args.from_json)
        coins = cache["coins"]
        quotes = cache["quotes"]
    else:
        coins = coins_from_exchanges(EXCHANGES)
        names = (
            [n.strip() for n in args.exchanges.split(",")]
            if args.exchanges
            else list(ccxt_async.exchanges)
        )
        cache = asyncio.run(scan(names, coins, quotes))

    results = cache["exchanges"]
    sources = live_sources(results, coins, quotes)
    unreachable = sorted(name for name, row in results.items() if not row["ok"])
    text = format_table(results, coins, quotes, unreachable, BLACKLIST)
    volumes = coin_volumes(results)
    shares = shares_by_coin(volumes)
    text += "\n\n" + format_volume_sections(volumes, shares, coins, BLACKLIST)

    print(text)
    if not args.from_json or args.json:
        save_cache(args.json or str(HERE / "cex_sources.json"), cache)
    Path(args.md).write_text(text + "\n")
    make_plot(results, sources, coins, quotes, args.png)
    make_volume_plot(results, coins, args.volume_png)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
