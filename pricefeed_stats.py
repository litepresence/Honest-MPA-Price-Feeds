"""
This script monitors all of the price feeds for HONEST MPAs

Program Flow:

Every hour:
 > Loop through all MPAs
 > > Get median settlement price 
 > > Loop through all producers
 > > > If producer is stale by more than an hour and a half...
 > > > or the settlement price is different from the median by more than 5%
 > > > > Take note of this producer and the reason for taking note in a dictionary
 > Print all notes taken, and a list of all producers affected.

This script is entirely self contained, aside from the websocket-client dependency,
meaning that it can be run as its own file completely separate from the rest of the
HONEST codebase.
"""
# pylint: disable=broad-exception-caught

# STANDARD MODULES
import json
import time
from collections import defaultdict
from statistics import median

# THIRD PARTY MODULES
from websocket import create_connection as wss

# List of valid nodes
NODES = [
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


# List of HONEST MPAS
MPAS = {
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


def read(file):
    """
    Read JSON-formatted data in a file.
    """
    with open(file, "r", encoding="utf-8") as handle:
        data = handle.read()
        handle.close()
    return json.loads(data)


def write(file, data):
    """
    Write JSON data to file.
    """
    with open(file, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(data))
        handle.close()


def wss_handshake():
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


def wss_query(rpc, params):
    """
    Send and receive websocket requests.
    """
    query = json.dumps({"method": "call", "params": params, "jsonrpc": "2.0", "id": 1})
    rpc.send(query)
    ret = json.loads(rpc.recv())
    try:
        ret = ret["result"]  # if there is result key take it
    except Exception:
        print(ret)
    return ret


def get_objects(rpc, object_ids):
    """
    Return data about objects in 1.7.x, 2.4.x, 1.3.x, etc. format.
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


def precision(rpc, object_id):
    """
    Get asset precision, requesting from RPC is required, otherwise reading from cache.
    """
    try:
        precs = json.loads(read("precisions.txt"))
    except FileNotFoundError:
        precs = {}
    prec = None
    if object_id in precs:
        prec = precs[object_id]
    else:
        print(object_id)
        prec = int(get_objects(rpc, [object_id])[object_id]["precision"])
        precs[object_id] = prec
        write("precisions.txt", json.dumps(precs))
    return prec


def from_iso_date(date):
    """
    Returns unix epoch given bitshares formatted time string.
    """
    return int(time.mktime(time.strptime(str(date), "%Y-%m-%dT%H:%M:%S")))


def settlement_price(rpc, data):
    """
    Calculate settlement price from a given data set.
    """
    if (
        data["settlement_price"]["base"]["amount"]
        and data["settlement_price"]["quote"]["amount"]
    ):
        return (
            int(data["settlement_price"]["base"]["amount"])
            / 10 ** precision(rpc, data["settlement_price"]["base"]["asset_id"])
        ) / (
            int(data["settlement_price"]["quote"]["amount"])
            / 10 ** precision(rpc, data["settlement_price"]["quote"]["asset_id"])
        )
    return -1


def convert_seconds(seconds):
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    weeks = days // 7
    months = int(days / 30.44)  # Average days in a month
    years = int(days / 365.25)  # Average days in a year

    if years:
        return f"{years} years"
    elif months:
        return f"{months} months"
    elif weeks:
        return f"{weeks} weeks"
    elif days:
        return f"{days} days"
    else:
        return f"{hours} hours"


def gradient(shade):
    shade = min(max(shade, 0), 255)
    if shade < 128:  # Black to white
        intensity = shade / 128
        r = int(255 * intensity)
        g = int(255 * intensity)
        b = int(255 * intensity)
    else:  # White to red
        intensity = (shade - 128) / 128
        r = 255
        g = int(255 * (1 - intensity))
        b = int(255 * (1 - intensity))
    return f"\033[38;2;{r:03};{g:03};{b:03}m"


def main():
    """
    Every hour:
     > Loop through all MPAs
     > > Get median settlement price
     > > Loop through all producers
     > > > If producer is stale by more than an hour and a half...
     > > > or the settlement price is different from the median by more than 10%
     > > > > Take note of this producer and the reason for taking note in a dictionary
     > Print all notes taken, and a list of all producers affected.
    """
    inv_mpas = {v: k for k, v in MPAS.items()}
    while True:
        rpc = wss_handshake()
        time_start = time.time()
        bitasset_ids = {
            v["bitasset_data_id"]: k
            for k, v in get_objects(rpc, list(MPAS.values())).items()
        }
        feed_data = {
            inv_mpas[bitasset_ids[k]]: v["feeds"]
            for k, v in get_objects(rpc, list(bitasset_ids.keys())).items()
        }
        producers_in_error = defaultdict(list)
        producers = []
        for token, token_data in feed_data.items():
            median_price = median(
                [
                    i
                    for i in [
                        settlement_price(rpc, producer[1][1]) for producer in token_data
                    ]
                    if i >= 0
                ]
            )
            for producer in token_data:
                producers.append(producer[0])
                if (stale := (time_start - from_iso_date(producer[1][0]))) > 5400:
                    producers_in_error[producer[0]].append(
                        [
                            token,
                            " stale by ",
                            convert_seconds(int(stale)),
                            (stale / 5400) * 255,
                        ]
                    )
                else:
                    percent_off = (
                        settlement_price(rpc, producer[1][1]) / median_price
                    ) - 1
                    producers_in_error[producer[0]].append(
                        [
                            token,
                            " off by ",
                            str(int(percent_off * 1000) / 10),
                            " percent",
                            (abs(percent_off)) * 2550,
                        ]
                    )
        # account id to name
        producers = {i["id"]: i["name"] for i in get_objects(rpc, producers).values()}
        producers_in_error = dict(
            zip(
                [producers[i] for i in producers_in_error.keys()],
                producers_in_error.values(),
            )
        )
        tokens_in_error = defaultdict(list)
        for p, errs in producers_in_error.items():
            for err in errs:
                tokens_in_error[err[0]].append(
                    gradient(err[-1]) + "".join([p, *err[1:-1]]) + "\033[m"
                )

        ntie = {}
        for token, errs in tokens_in_error.items():
            ntie[token] = sorted(
                [*errs, *[" "] * (len(producers) - len(errs))],
                key=lambda x: tuple(
                    idx if x.split()[:1] == [i] else 0
                    for idx, i in enumerate(producers.values())
                ),
            )
        tokens_in_error = ntie

        print("\033c")
        # print(ntie)

        table = []

        for token, errs in tokens_in_error.items():
            table.append([token, *["".join(i) for i in errs]])

        maxes = [max(map(len, i)) for i in list(zip(*table))]

        for row in table:
            print("  |  ".join([i.ljust(maxes[idx]) for idx, i in enumerate(row)]))

        # for i in range(256):
        #     print(gradient(i), "asdf")

        time.sleep(3600)


if __name__ == "__main__":
    main()
