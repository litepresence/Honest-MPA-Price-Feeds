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
from collections import defaultdict
from json import dumps as json_dumps
from multiprocessing import Process
from pprint import pprint
from statistics import median

# PRICE FEED MODULES
from forex.api_source import (barchart, currencyconverter, fixerio, fscapi,
                              fxmarket, openexchangerates)
from forex.bts_source import cmc, cryptocomp, google
from forex.cfscrape_source import fxcm, fxempire1
from forex.commodities import (arincen, bitpanda, businessinsider, cnbc,
                               commoditycom, mql5)
from forex.scrape_source import (aastock, currencyme, duckduckgo, forexrates,
                                 ino, liveusd, oanda, ratewidget, wocu, yahoo)
from utilities import it, race_read_json, race_write, ret_markets, sigfig

# GLOBAL CONSTANTS
TIMEOUT = 15
SAVE_RAM = False  # True for deployment on low cost web hosting; saves 0.5G RAM


def refresh_forex_rates():
    """
    make process wrapped external calls; IPC via text pipe
    """
    methods = [
        aastock,  # DARKWEB API; MORNINGSTAR (GOOGLE FINANCE) BACKDOOR
        # barchart,  # KEYED
        # currencyconverter,  # KEYED, NOT COMPATIBLE WITH VPN / DYNAMIC IP
        currencyme,  # DARKWEB API
        duckduckgo,  # XML SCRAPING, XE BACKDOOR
        ratewidget,  # XML SCRAPING
        # fixerio,  # KEYED
        forexrates,  # XML SCRAPING
        # fscapi,  # KEYED
        fxcm,  # CLOUDFARE SPOOFING; HEADER REQUIRED; ALMOST JSON RESPONSE
        fxempire1,  # XIGNITE BACKDOOR; HEADER REQUIRED; CLOUDFARE SPOOFING
        # fxmarket,  # KEYED
        ino,  # DARKWEB API
        liveusd,  # DARKWEB API
        oanda,  # DARKWEB API; RC4 ECRYPTION OF LATIN ENCODING
        # openexchangerates,  # KEYED
        wocu,  # XML SCRAPING
        yahoo,  # YAHOO FINANCE V7 DARKWEB API
        cmc,
        cryptocomp,
        google,
        cnbc,
        arincen,
        bitpanda,
        commoditycom,
        businessinsider,
        mql5,
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
    Sort and aggregate data from external sources and calculate medians.

    This function retrieves foreign exchange rates from various sources,
    aggregates the prices for each currency pair, and calculates the median
    price along with the count of prices and the sources from which they were obtained.

    Returns:
        dict: A dictionary containing the following keys:
        - "sources" (dict): A dictionary of the raw forex rates from each source.
        - "aggregate" (defaultdict): A dictionary aggregating prices for each currency pair,
          where each key is a currency pair and the value is a list of tuples containing
          the price and the source.
        - "medians" (dict): A dictionary where each key is a currency pair and the value is a tuple
          containing:
            - median price (float): The median price of the currency pair.
            - count (int): The number of prices aggregated for the currency pair.
            - sources (list): A list of sources from which the prices were obtained.

    Example:
        {
            "sources": {
                "source1": {"EUR:USD": 1.1, "GBP:USD": 1.3},
                "source2": {"EUR:USD": 1.2, "GBP:USD": 1.4},
            },
            "aggregate": {
                "EUR:USD": [(1.1, "source1"), (1.2, "source2")],
                "GBP:USD": [(1.3, "source1"), (1.4, "source2")],
            },
            "medians": {
                "EUR:USD": (1.15, 2, ["source1", "source2"]),
                "GBP:USD": (1.35, 2, ["source1", "source2"]),
            }
        }
    """
    sources = refresh_forex_rates()
    aggregate = defaultdict(list)
    for source, prices in sources.items():
        for pair, price in prices.items():
            aggregate[pair].append((price, source))

    medians = {
        pair: (
            sigfig(median([price for price, _ in prices])),
            len([price for price, _ in prices]),
            [source for _, source in prices],
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
    print(it("purple", "FOREX: "), it("green", "DONE!"))
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
