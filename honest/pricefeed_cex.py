"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

CEX BTC:USD and BTS:BTC data aggregation script

litepresence2020
"""
# STANDARD MODULES
import os
import time
from calendar import timegm
from collections import defaultdict
from datetime import datetime
from json import dumps as json_dumps
from multiprocessing import Process, Value
from pprint import pprint
from random import random
from statistics import median

# THIRD PARTY MODULES
import ccxt
import requests
# HONEST MODULES
from exchanges import EXCHANGES
from proxy_list import ProxyManager
from utilities import PATH, it, race_read_json, race_write, trace, correct_pair

# GLOBAL CONSTANTS
TIMEOUT = 30
ATTEMPTS = 20
DETAIL = False
BEGIN = int(time.time())
USE_PROXY = ["binance", "bybit"]
# what to multiply ATTEMPTS and TIMEOUT by when an exchange uses a proxy
PROXY_SCALE = 5


# FORMATING & TYPESETTING
def print_results(cex):
    """
    log the cex price feed to terminal
    """
    runtime = int(time.time() - BEGIN)
    print(f"Centralized Exchange", time.ctime(), "runtime:", runtime)
    pprint(cex)


# PRIMARY EVENT METHODS
def get_price(proxy_manager, exchange, pairs):
    """
    Last Price as float
    """
    if not hasattr(get_price, "exchange_cache"):
        get_price.exchange_cache = {}

    doc = exchange + ".txt"
    race_write(doc, {})

    # fetch the exchange object from the cache if possible, else create a new one
    exchange_obj = get_price.exchange_cache.get(exchange, getattr(ccxt, exchange)())
    assert exchange_obj.has[
        "fetchTickers"
    ], f"{exchange} does not support fetch_tickers"
    # reformat from HONEST style to CCXT style
    pairs = [pair.replace(":", "/") for pair in pairs]

    use_proxy = exchange in USE_PROXY

    # get a proxy if required
    if use_proxy:
        proxy = proxy_manager.get_proxy()
        exchange_obj.socksProxy = f"socks5://{proxy}"
    idx = 0
    individual = False
    while True:
        # allow for more attempts when using proxies
        if idx > ATTEMPTS * (PROXY_SCALE if use_proxy else 1):
            print(it("yellow", "CEX: "), exchange, it("red", "failed!"))
            return
        try:
            # fetch tickers
            if individual:
                tickers = {}
                for pair in pairs:
                    tickers[pair] = exchange_obj.fetch_ticker(correct_pair(exchange, pair))
                    time.sleep(0.5)
            else:
                tickers = exchange_obj.fetch_tickers([correct_pair(exchange, pair) for pair in pairs])
            # get the last price from each, moving back from CCXT style to HONEST style
            data = {correct_pair(exchange, i["symbol"], reverse=True).replace("/", ":"): i["last"] for i in tickers.values()}
            break
        except ccxt.errors.BadSymbol as error:
            badsymbol = error.args[0].rsplit(" ", 1)[1]
            if badsymbol != (corrected_bad_sym:=correct_pair(exchange, badsymbol, reverse=True)):
                corrected_bad_sym, badsymbol = badsymbol, corrected_bad_sym
            else:
                corrected_bad_sym = ""
            pairs.pop(pairs.index(badsymbol))
            print(
                it("yellow", "CEX: "),
                exchange,
                f"declares {badsymbol}{f' (aka {corrected_bad_sym})' if corrected_bad_sym else ''} is a",
                it("red", "bad symbol."),
                " Retrying without it...",
            )
        except Exception as error:
            if "cannot contain more than 1 symbol" in str(error):
                individual = True
                print(
                    it("yellow", "CEX: "),
                    exchange,
                    "does not allow multi-symbol queries.  Falling back to individual...",
                )
                time.sleep(1)
                continue
            print(
                it("yellow", "CEX: "),
                exchange,
                f"failed{' with proxy' if use_proxy else ''}, retrying:",
                error,
                type(error),
            )
            idx += 1
            if use_proxy:
                proxy_manager.blacklist_proxy(proxy)
            time.sleep(1)

    data["time"] = int(time.time())
    print(it("yellow", "CEX: "), "writing", doc)
    race_write(doc, json_dumps(data))


def aggregate(exchanges):
    """
    post process data from all exchanges to extract medians and means
    """
    data = {}
    for exchange in exchanges:
        try:
            doc = exchange + ".txt"
            print(it("yellow", "CEX: "), "reading", doc)
            json_data = race_read_json(doc)
            if json_data:
                data[exchange] = json_data
        except Exception as error:
            print(it("yellow", "CEX: "), error.args)

    pairs = defaultdict(list)
    exchange_pairs = defaultdict(dict)
    for exchange, datapoints in data.items():
        try:
            if int(time.time()) - datapoints["time"] < 300:
                for pair, price in datapoints.items():
                    if pair == "time":
                        continue
                    pairs[pair].append(price)
                    exchange_pairs[pair][exchange] = price
        except Exception as error:
            print(it("yellow", "CEX: "), error)
    median_price = {pair: median(prices) for pair, prices in pairs.items()}
    mean_price = {pair: sum(prices) / len(prices) for pair, prices in pairs.items()}
    return {
        pair: {
            "mean": mean_price[pair],
            "median": median_price[pair],
            "data": exchange_pairs[pair],
        }
        for pair in pairs
    }


def fetch(proxy_manager, exchanges, by_pairs):
    """
    multiprocess wrap external request for durability
    """
    processes = {}
    for exchange, pairs in exchanges.items():
        processes[exchange] = Process(
            target=get_price,
            args=(
                proxy_manager,
                exchange,
                pairs,
            ),
        )
        processes[exchange].daemon = False
        processes[exchange].start()
    for exchange in exchanges:
        processes[exchange].join(
            TIMEOUT if exchange not in USE_PROXY else TIMEOUT * PROXY_SCALE
        )
        processes[exchange].terminate()
    return aggregate(exchanges)


def pricefeed_cex(proxy_manager):
    """
    "HONEST.ADA", # Cardano
    "HONEST.DOT", # Polkadot
    "HONEST.LTC", # Litecoin
    "HONEST.SOL", # Solana
    "HONEST.XMR", # Monero
    "HONEST.ATOM", # Cosmos
    "HONEST.XLM", # Stellar
    "HONEST.ALGO", # Algorand
    "HONEST.FIL", # Filecoin
    "HONEST.EOS", # EOS
    "HONEST.BTC"
    "HONEST.USD"
    "HONEST.XRP"
    create a cex price feed, write it to disk, and return it
    """
    rotated = defaultdict(list)
    for pair, exchanges in EXCHANGES.items():
        for exchange in exchanges:
            rotated[exchange].append(pair)

    cex = fetch(proxy_manager, rotated, EXCHANGES)

    race_write("pricefeed_cex.txt", cex)
    print(it("yellow", "CEX: "), it("green", "DONE!"))
    return cex


def main():
    """
    demo a single cex pricefeed
    """
    print("initializing cex feeds...")
    proxy_manager = ProxyManager()
    proxy_manager.get_proxy_list()

    cex = pricefeed_cex(proxy_manager)
    print_results(cex)


if __name__ == "__main__":
    main()
