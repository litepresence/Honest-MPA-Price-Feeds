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
from forex_scrape import reuters, duckduckgo, wocu, oanda, aastock, fxempire2, ino
from forex_scrape import fxrate, forextime, currencyme, forexrates, exchangeratewidget
from forex_cfscrape import bitcoinaverage, bloomberg, fxcm, fxempire1, investing
from utilities import race_write, ret_markets, race_read_json, it, sigfig

# GLOBAL CONSTANTS
TIMEOUT = 15
SAVE_RAM = False  # True for deployment on low cost web hosting; saves 0.5G RAM


def refresh_forex_rates():
    """
    make process wrapped external calls; IPC via text pipe
    """
    methods = [
        aastock,  # DARKWEB API; MORNINGSTAR (GOOGLE FINANCE) BACKDOOR
        barchart,  # KEYED
        bitcoinaverage,  # MAY ADD CAPTCHA; HEADER REQUIRED; CLOUDFARE SPOOFING
        bloomberg,  # MAY ADD CAPTCHA; HEADER REQUIRED; CLOUDFARE SPOOFING
        currencyconverter,  # KEYED, NOT COMPATIBLE WITH VPN / DYNAMIC IP
        currencyme,  # DARKWEB API
        duckduckgo,  # XML SCRAPING, XE BACKDOOR
        exchangeratewidget,  # XML SCRAPING
        finviz,  # DARKWEB API
        fixerio,  # KEYED
        forexrates,  # XML SCRAPING
        forextime,  # DARKWEB API
        freeforex,  # FREE API
        fscapi,  # KEYED
        fxcm,  # CLOUDFARE SPOOFING; HEADER REQUIRED; ALMOST JSON RESPONSE
        fxempire1,  # XIGNITE BACKDOOR; HEADER REQUIRED; CLOUDFARE SPOOFING
        fxempire2,  # TRADINGVIEW BACKDOOR
        fxmarket,  # KEYED
        fxrate,  # XML SCRAPING
        ino,  # DARKWEB API
        investing,  # CLOUDFARE SPOOFING, XML SCRAPING
        liveusd,  # DARKWEB API
        oanda,  # DARKWEB API; RC4 ECRYPTION OF LATIN ENCODING
        openexchangerates,  # KEYED
        reuters,  # REFINITIV BACKDOOR, DARKWEB API
        wocu,  # XML SCRAPING
        wsj,  # MARKETWATCH BACKDOOR, DARKWEB API
        yahoo,  # YAHOO FINANCE V7 DARKWEB API
    ]
    # initialize each external call method as a process
    processes = {}
    for method in methods:
        site = method.__name__
        race_write(f"{site}_forex.txt", {})
        processes[site] = Process(target=method, args=(site,))
        processes[site].daemon = False
        processes[site].start()
        if SAVE_RAM:
            processes[site].join(TIMEOUT)
            processes[site].terminate()
            time.sleep(5)
    if not SAVE_RAM:
        for value in processes.values():
            value.join(TIMEOUT)
        for value_ in processes.values():
            value_.terminate()
    return {site: race_read_json(f"{site}_forex.txt") for site in processes}


def aggregate_rates():
    """
    sort and aggregate data from external sources
    calculate medians
    """
    sources = refresh_forex_rates()
    aggregate = {}
    for source, prices in sources.items():
        for pair, price in prices.items():
            aggregate.setdefault(pair, []).append((price, source))

    medians = {
        pair: (
            sigfig(median([price for price, _ in prices])),
            len([price for price, _ in prices]),
            [source for _, source in prices]
        )
        for pair, prices in aggregate.items()
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
