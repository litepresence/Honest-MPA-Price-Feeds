"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

USD:FOREX data aggregation script

litepresence2020
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
from fscapi import fscapi
from fixerio import fixerio
from barchart import barchart
from fxmarket import fxmarket
from currencyconverter import currencyconverter
from openexchangerates import openexchangerates

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
    processes["fscapi"] = process_request("fscapi", fscapi)
    processes["fixerio"] = process_request("fixerio", fixerio)
    processes["barchart"] = process_request("barchart", barchart)
    processes["fxmarket"] = process_request("fxmarket", fxmarket)
    processes["openexchangerates"] = process_request(
        "openexchangerates", openexchangerates
    )
    processes["currencyconverter"] = process_request(
        "currencyconverter", currencyconverter
    )
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
    return {
        "sources": sources,
        "aggregate": aggregate,
        "medians": medians,
    }


def print_results(forex):
    """
    pretty print the forex price data to terminal
    """
    print("\nForeign Exchange Rates\n")
    print("markets")
    print(ret_markets(), "\n")
    for key, val in forex["sources"].items():
        print(it("yellow", key))
        pprint(val)
    print("\n", it("purple", "aggregates"))
    pprint(forex["aggregate"])
    print("\n", it("blue", "medians"))
    for key, val in forex["medians"].items():
        print(key, str(val[0]).ljust(13), str(val[1]).ljust(3), val[2])


def pricefeed_forex():
    """
    create a forex price feed, write it to disk, and return it
    """
    forex = aggregate_rates()
    race_write(doc="pricefeed_forex.txt", text=json_dumps(forex))
    return forex


def main():
    """
    initializing forex rates...
    """
    print(main.__doc__)
    forex = pricefeed_forex()
    print_results(forex)


if __name__ == "__main__":

    main()
