"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

A stand alone app to monitor feed producers

litepresence2024
"""

from typing import Any, Dict, List, Tuple
import json
import time
from collections import defaultdict
from statistics import median
from websocket import create_connection as wss

# List of valid nodes
NODES: List[str] = [
    "wss://api.bts.mobi/wss",
    "wss://newyork.bitshares.im/ws",
    "wss://api.bitshares.info",
    "wss://bts.open.icowallet.net/ws",
    "wss://api.dex.trading/wss",
    "wss://eu.nodes.bitshares.ws/wss",
    "wss://api-us.61bts.com/wss",
    "wss://cloud.xbts.io/ws",
    "wss://dex.iobanker.com/wss",
    "wss://hongkong.bitshares.im/wss",
    "wss://bts.mypi.win/wss",
    "wss://public.xbts.io/wss",
    "wss://node.xbts.io/wss",
    "wss://btsws.roelandp.nl/wss",
    "wss://singapore.bitshares.im/wss",
    "wss://api.bts.btspp.io:10100/wss",
    "wss://api.btslebin.com/wss",
]

# List of HONEST MPAs
MPAS: Dict[str, str] = {
    "HONEST.CNY": "1.3.5641",
    "HONEST.USD": "1.3.5649",
    "HONEST.BTC": "1.3.5650",
    "HONEST.XAU": "1.3.5651",
    "HONEST.XAG": "1.3.5652",
    "HONEST.ETH": "1.3.5659",
    "HONEST.XRP": "1.3.5660",
    "HONEST.ETH1": "1.3.5661",
    "HONEST.XRP1": "1.3.5662",
    "HONEST.USDSHORT": "1.3.6289",
    "HONEST.BTCSHORT": "1.3.6290",
    "HONEST.ADA": "1.3.6304",
    "HONEST.DOT": "1.3.6305",
    "HONEST.LTC": "1.3.6306",
    "HONEST.SOL": "1.3.6307",
    "HONEST.XMR": "1.3.6308",
    "HONEST.ATOM": "1.3.6309",
    "HONEST.XLM": "1.3.6310",
    "HONEST.ALGO": "1.3.6311",
    "HONEST.FIL": "1.3.6312",
    "HONEST.EOS": "1.3.6313",
    "HONEST.RUB": "1.3.6314",
    "HONEST.EUR": "1.3.6315",
    "HONEST.GBP": "1.3.6316",
    "HONEST.JPY": "1.3.6317",
    "HONEST.KRW": "1.3.6318",
    "HONEST.ADASHORT": "1.3.6319",
    "HONEST.DOTSHORT": "1.3.6320",
    "HONEST.LTCSHORT": "1.3.6321",
    "HONEST.SOLSHORT": "1.3.6322",
    "HONEST.XMRSHORT": "1.3.6323",
    "HONEST.ATOMSHORT": "1.3.6324",
    "HONEST.XLMSHORT": "1.3.6325",
    "HONEST.ALGOSHORT": "1.3.6326",
    "HONEST.FILSHORT": "1.3.6327",
    "HONEST.EOSSHORT": "1.3.6328",
    "HONEST.RUBSHORT": "1.3.6329",
    "HONEST.EURSHORT": "1.3.6330",
    "HONEST.GBPSHORT": "1.3.6331",
    "HONEST.JPYSHORT": "1.3.6332",
    "HONEST.KRWSHORT": "1.3.6333",
    "HONEST.XRPSHORT": "1.3.6334",
    "HONEST.ETHSHORT": "1.3.6335",
    "HONEST.XAUSHORT": "1.3.6336",
    "HONEST.XAGSHORT": "1.3.6337",
    "HONEST.CNYSHORT": "1.3.6338",
}


def read(file: str) -> Any:
    """
    Read JSON-formatted data from a file.

    :param file: The path to the file to read.
    :returns: The loaded JSON data.
    """
    with open(file, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    return data


def write(file: str, data: Any) -> None:
    """
    Write JSON data to a file.

    :param file: The path to the file to write.
    :param data: The data to write.
    """
    with open(file, "w", encoding="utf-8") as handle:
        json.dump(data, handle)


def wss_handshake() -> wss:
    """
    Create a websocket handshake.
    """
    nodes = NODES[::]
    while True:
        node = nodes[0]
        start = time.time()
        try:
            rpc = wss(node, timeout=3)
        except Exception:
            nodes.append(nodes.pop(0))
            continue
        if time.time() - start < 3:
            break
    return rpc


def wss_query(rpc: wss, params: List[Any]) -> Dict[str, Any]:
    """
    Send and receive websocket requests.

    :param rpc: The websocket connection.
    :param params: The parameters to send.
    :returns: The response received.
    """
    query = json.dumps({"method": "call", "params": params, "jsonrpc": "2.0", "id": 1})
    rpc.send(query)
    ret = json.loads(rpc.recv())
    try:
        ret = ret["result"]  # if there is result key take it
    except Exception:
        print(ret)
    return ret


def get_objects(rpc: wss, object_ids: List[str]) -> Dict[str, Any]:
    """
    Return data about objects.

    :param rpc: The websocket connection.
    :param object_ids: The IDs of the objects to retrieve.
    :returns: The retrieved objects.
    """
    if len(object_ids) < 90:
        ret = wss_query(rpc, ["database", "get_objects", [object_ids]])
    else:
        ret = []
        i = 0
        while i < len(object_ids):
            ret.extend(
                wss_query(rpc, ["database", "get_objects", [object_ids[i : i + 90]]])
            )
            i += 90
    return {object_ids[idx]: item for idx, item in enumerate(ret) if item is not None}


def precision(rpc: wss, object_id: str) -> int:
    """
    Get asset precision.

    :param rpc: The websocket connection.
    :param object_id: The ID of the object.
    :returns: The precision of the asset.
    """
    try:
        precs = read("precisions.txt")
    except FileNotFoundError:
        precs = {}
    prec = precs.get(object_id)
    if prec is None:
        prec = int(get_objects(rpc, [object_id])[object_id]["precision"])
        precs[object_id] = prec
        write("precisions.txt", precs)
    return prec


def from_iso_date(date: str) -> int:
    """
    Convert a Bitshares formatted time string to Unix epoch.

    :param date: The Bitshares formatted time string.
    :returns: The Unix epoch time.
    """
    return int(time.mktime(time.strptime(str(date), "%Y-%m-%dT%H:%M:%S")))


def settlement_price(rpc: wss, data: Dict[str, Any]) -> float:
    """
    Calculate settlement price from given data.

    :param rpc: The websocket connection.
    :param data: The data containing settlement price.
    :returns: The calculated settlement price.
    """
    ret = -1
    base_amount = int(data["settlement_price"]["base"]["amount"])
    quote_amount = int(data["settlement_price"]["quote"]["amount"])
    if base_amount and quote_amount:
        base_precision = precision(rpc, data["settlement_price"]["base"]["asset_id"])
        quote_precision = precision(rpc, data["settlement_price"]["quote"]["asset_id"])
        ret = (base_amount / 10**base_precision) / (
            quote_amount / 10**quote_precision
        )
    return ret


def main() -> None:
    """
    Every hour:
     > Loop through all MPAs
     > > Get median settlement price
     > > Loop through all producers
     > > > If producer is stale by more than an hour and a half...
     > > > or the settlement price is different from the median by more than 5%
     > > > > Take note of this producer and the reason for taking note in a dictionary
     > Print all notes taken, and a list of all producers affected.
    """
    inv_mpas = {v: k for k, v in MPAS.items()}
    while True:
        rpc = wss_handshake()
        bitasset_ids = {
            v["bitasset_data_id"]: k
            for k, v in get_objects(rpc, list(MPAS.values())).items()
        }
        feed_data = {
            inv_mpas[bitasset_ids[k]]: v["feeds"]
            for k, v in get_objects(rpc, list(bitasset_ids.keys())).items()
        }
        producers_in_error: Dict[str, List[List[str]]] = defaultdict(list)
        for token, token_data in feed_data.items():
            median_price = median(
                [settlement_price(rpc, producer[1][1]) for producer in token_data]
            )
            for producer in token_data:
                if time.time() - from_iso_date(producer[1][0]) > 5400:
                    producers_in_error[producer[0]].append(
                        [
                            token,
                            "stale by",
                            str(int(time.time() - from_iso_date(producer[1][0]))),
                            "secs",
                        ]
                    )
                elif (
                    offcent := abs(
                        (settlement_price(rpc, producer[1][1]) / median_price) - 1
                    )
                ) > 0.05:
                    producers_in_error[producer[0]].append(
                        [token, "bad feed by", str(int(offcent * 100)), "%"]
                    )
        producers_in_error = dict(
            zip(
                [
                    i["name"]
                    for i in get_objects(rpc, list(producers_in_error.keys())).values()
                ],
                producers_in_error.values(),
            )
        )
        npie = {}
        for (
            p,
            errs,
        ) in producers_in_error.items():
            err_t = list(zip(*errs))
            if list(MPAS.keys()) != list(err_t[0]) or not all(
                err_t[1][0] == i for i in err_t[1]
            ):
                npie[p] = errs
            else:
                npie[p] = [
                    f"ALL TOKENS {errs[0][1]} {min(err_t[2])}-{max(err_t[2])} {errs[0][3]}"
                ]
        producers_in_error = npie
        print("\033c")

        for producer, errs in producers_in_error.items():
            print(
                producer, ":", [" ".join(i) if isinstance(i, list) else i for i in errs]
            )
            print()
        print()
        print(list(producers_in_error.keys()))
        time.sleep(3600)


if __name__ == "__main__":
    main()
