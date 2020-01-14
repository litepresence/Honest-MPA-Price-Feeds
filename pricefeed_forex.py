"""
+==============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║ 
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
 MARKET PEGGED ASSET PRICEFEEDS
+==============================+


USD:FOREX data aggregation script

litepresence 2019

"""
# STANDARD PYTHON MODULES
from pprint import pprint
from statistics import median
from json import dumps as json_dumps

# PRICE FEED MODULES
from fxcm import fxcm
from wocu import wocu
from oanda import oanda
from liveusd import liveusd
from fxempire import fxempire
from bitcoinaverage import bitcoinaverage
from freeforex import freeforex
from finviz import finviz
from yahoo import yahoo
from wsj import wsj
from duckduckgo import duckduckgo
from bloomberg import bloomberg

# ADDITIONAL PROPRIETARY MODULES
from utilities import process_request, it, sigfig
from utilities import race_write, ret_markets, race_read_json

TIMEOUT = 10


def refresh_forex_rates():
    """
    make process wrapped external calls 
    """
    # start processes
    processes = {}
    processes["fxcm"] = process_request("fxcm", fxcm)
    processes["bitcoinaverage"] = process_request("bitcoinaverage", bitcoinaverage)
    processes["wocu"] = process_request("wocu", wocu)
    processes["oanda"] = process_request("oanda", oanda)
    processes["liveusd"] = process_request("liveusd", liveusd)
    processes["fxempire"] = process_request("fxempire", fxempire)
    processes["freeforex"] = process_request("freeforex", freeforex)
    processes["finviz"] = process_request("finviz", finviz)
    processes["yahoo"] = process_request("yahoo", yahoo)
    processes["wsj"] = process_request("wsj", wsj)
    processes["duckduckgo"] = process_request("duckduckgo", duckduckgo)
    processes["bloomberg"] = process_request("bloomberg", bloomberg)
    # join, timeout, and terminate processes
    for site in processes.keys():
        processes[site].join(TIMEOUT)
        processes[site].terminate()
    # read the text pipe ipc results
    sources = {}
    for site in processes.keys():
        sources[site] = race_read_json(f"{site}_forex.txt")

    return sources


def aggregate_rates():
    """
    sort and aggregate data from external sources
    calculate medians

    """
    sources = refresh_forex_rates()
    aggregate = {}
    for source, prices in sources.items():
        for pair, price in prices.items():
            if pair in aggregate.keys():
                aggregate[pair].append((price, source))
            else:
                aggregate[pair] = [(price, source)]
    medians = {
        k: (
            sigfig(median([i[0] for i in v])),
            len([i[0] for i in v]),
            [i[1] for i in v],
        )
        for k, v in aggregate.items()
    }
    forex = {
        "sources": sources,
        "aggregate": aggregate,
        "medians": medians,
    }
    race_write(doc="pricefeed_forex.txt", text=json_dumps(forex))
    return forex


def print_results(forex):

    print("\033c")
    print("gathering forex rates...")
    print("markets")
    print(ret_markets(), "\n")
    for k, v in forex["sources"].items():
        print(it("yellow", k))
        pprint(v)
    print("\n", it("purple", "aggregates"))
    pprint(forex["aggregate"])
    print("\n", it("blue", "medians"))
    for k, v in forex["medians"].items():
        print(k, str(v[0]).ljust(13), str(v[1]).ljust(3), v[2])


if __name__ == "__main__":

    forex = aggregate_rates()
    print_results(forex)
