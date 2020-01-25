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
import time
from pprint import pprint
from statistics import median
from json import dumps as json_dumps
from multiprocessing import Process

# PRICE FEED MODULES
from forex_api import fixerio, openexchangerates, fscapi
from forex_api import barchart, currencyconverter, fxmarket
from forex_scrape import liveusd, freeforex, finviz, yahoo, wsj
from forex_scrape import reuters, duckduckgo, wocu, oanda
from forex_cfscrape import bitcoinaverage, bloomberg, fxcm, fxempire
from utilities import race_write, ret_markets, race_read_json, it, sigfig

# GLOBAL CONSTANTS
TIMEOUT = 15


def refresh_forex_rates():
    """
    make process wrapped external calls; IPC via text pipe
    """
    methods = [
        barchart,
        bitcoinaverage, # SOMETIMES FAILS / SLOW TO LOAD / CLOUDFARE ??
        bloomberg,
        currencyconverter, # NOT COMPATIBLE WITH VPN / DYNAMIC IP
        duckduckgo,
        finviz,
        fixerio,
        freeforex,
        fscapi,
        fxcm,
        fxempire,
        fxmarket,
        liveusd,
        oanda,
        openexchangerates,
        reuters,
        wocu,
        wsj,
        yahoo,
    ]
    # initialize each external call method as a process
    processes = {}
    for method in methods:
        site = method.__name__
        race_write(f"{site}_forex.txt", {})
        processes[site] = Process(target=method, args=(site,))
        processes[site].daemon = False
        processes[site].start()
        # FIXME: FOR DEPLOYMENT ON LOW COST WEB HOSTING SERVICES
        # FIXME: ALTERNATIVE RAM SAVINGS 0.5GB, WITH ADDED EXECUTION TIME OF 4 MINUTES
        # FIXME: **INCLUDE** NEXT 3 LINES FOR LOW RAM ALTERNATIVE
        # processes[site].join(TIMEOUT)
        # processes[site].terminate()
        # time.sleep(5)
    # FIXME: **EXCLUDE** NEXT 4 LINES FOR LOW RAM ALTERNATIVE
    for site in processes.keys(): 
        processes[site].join(TIMEOUT)
    for site in processes.keys(): 
        processes[site].terminate()
    # read the text pipe ipc results of each process
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
