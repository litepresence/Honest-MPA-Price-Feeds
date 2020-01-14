"""
+==============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║ 
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
 MARKET PEGGED ASSET PRICEFEEDS
+==============================+


CEX BTC:USD and BTS:BTC data aggregation script

litepresence 2019

"""
# STANDARD MODULES
# ======================================================================
import os
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value
from statistics import median
from datetime import datetime
from calendar import timegm
from math import ceil
import traceback
from random import random

# THIRD PARTY MODULES
# ======================================================================
import numpy as np
import requests

# PROPRIETARY MODULES
# ======================================================================
from utilities import race_write, race_read_json

# GLOBAL USER DEFINED CONSTANTS
# ======================================================================
TIMEOUT = 30
ATTEMPTS = 10
DETAIL = False
BEGIN = int(time.time())
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def return_urls():
    """
    dictionary of api domain names
    """
    return {
        "coinbase": "https://api.pro.coinbase.com",
        "bittrex": "https://bittrex.com",
        "bitfinex": "https://api-pub.bitfinex.com",
        "kraken": "https://api.kraken.com",
        "poloniex": "https://www.poloniex.com",
        "binance": "https://api.binance.com",
        "bitstamp": "https://www.bitstamp.net",
    }


# FORMATING
# ======================================================================
def from_iso_date(date):
    """
    ISO to UNIX conversion
    """
    return int(timegm(time.strptime(str(date), "%Y-%m-%dT%H:%M:%S")))


def to_iso_date(unix):
    """
    iso8601 datetime given unix epoch
    """
    return datetime.utcfromtimestamp(int(unix)).isoformat()


def symbol_syntax(exchange, symbol):
    """
    translate ticker symbol to each exchange's local syntax
    """
    asset, currency = symbol.upper().split(":")
    # ticker symbol colloquialisms
    if exchange == "kraken":
        if asset == "BTC":
            asset = "XBT"
        if currency == "BTC":
            currency = "XBT"
    if exchange == "poloniex":
        if asset == "XLM":
            asset = "STR"
        if currency == "USD":
            currency = "USDT"
    if exchange == "binance":
        if currency == "USD":
            currency = "USDT"
    symbols = {
        "bittrex": (currency + "-" + asset),
        "bitfinex": (asset + currency),
        "binance": (asset + currency),
        "poloniex": (currency + "_" + asset),
        "coinbase": (asset + "-" + currency),
        "kraken": (asset.lower() + currency.lower()),
        "bitstamp":(asset + ":" + currency),
    }
    symbol = symbols[exchange]
    return symbol


def trace(error):
    """
    Stack Trace Message Formatting
    """
    msg = str(type(error).__name__) + str(error.args) + str(traceback.format_exc())
    return msg


def it(style, text):  # DONE
    """
    Color printing in terminal
    """
    emphasis = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
    }
    return ("\033[%sm" % emphasis[style]) + str(text) + "\033[0m"


# SUBPROCESS REMOTE PROCEDURE CALL
# ======================================================================


def request(api, signal):
    """
    GET remote procedure call to public exchange API
    """
    urls = return_urls()

    api["method"] = "GET"
    api["headers"] = {}
    api["data"] = ""
    api["key"] = ""
    api["passphrase"] = ""
    api["secret"] = ""
    api["url"] = urls[api["exchange"]]

    url = api["url"] + api["endpoint"]

    # print(api)

    time.sleep(10 * random())

    resp = requests.request(
        method=api["method"],
        url=url,
        data=api["data"],
        params=api["params"],
        headers=api["headers"],
    )

    data = resp.json()

    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10 ** 6 * api["nonce"]))
        + "_{}_private.txt".format(api["exchange"])
    )
    race_write(doc, json_dumps(data))
    signal.value = 1


def process_request(api):
    """
    Multiprocessing Durability Wrapper for External Requests
    interprocess communication via durable text pipe
    """
    begin = time.time()
    # multiprocessing completion signal
    signal = Value("i", 0)
    # several iterations of external requests until satisfied with response
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        # multiprocessing text file name nonce
        api["nonce"] = time.time()
        i += 1

        if i > 1:
            print(
                "{} {} PUBLIC attempt:".format(api["exchange"], api["pair"]),
                i,
                time.ctime(),
                int(time.time()),
            )
        child = Process(target=request, args=(api, signal))
        child.daemon = False
        child.start()
        child.join(TIMEOUT)
        child.terminate()
        time.sleep(i ** 2)
    # the doc was created by the subprocess; read and destroy it
    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10 ** 6 * api["nonce"]))
        + "_{}_private.txt".format(api["exchange"])
    )
    data = race_read_json(doc)
    path = PATH + "pipe/"
    if os.path.isfile(path + doc):
        os.remove(path + doc)
    if i > 1:
        print(
            "{} {} PUBLIC elapsed:".format(api["exchange"], api["pair"]),
            ("%.2f" % (time.time() - begin)),
        )
    return data


# METHODS
# ======================================================================
def get_price(api):
    """
    Last Price as float
    """
    exchange = api["exchange"]
    symbol = symbol_syntax(exchange, api["pair"])
    endpoints = {
        "bittrex": "/api/v1.1/public/getticker",
        "bitfinex": "/v2/ticker/t{}".format(symbol),
        "binance": "/api/v1/ticker/allPrices",
        "poloniex": "/public",
        "coinbase": "/products/{}/ticker".format(symbol),
        "kraken": "/0/public/Ticker",
        "bitstamp": "/api/ticker",
    }
    params = {
        "bittrex": {"market": symbol},
        "bitfinex": {"market": symbol},
        "binance": {},
        "poloniex": {"command": "returnTicker"},
        "coinbase": {"market": symbol},
        "kraken": {"pair": [symbol]},
        "bitstamp":{},
    }
    api["endpoint"] = endpoints[exchange]
    api["params"] = params[exchange]
    while 1:

        try:
            data = process_request(api)
            if exchange == "bittrex":
                last = float(data["result"]["Last"])
            elif exchange == "bitfinex":
                last = float(data[6])
            elif exchange == "binance":
                data = {d["symbol"]: float(d["price"]) for d in data}
                last = float(data[symbol])
            elif exchange == "poloniex":
                last = float(data[symbol]["last"])
            elif exchange == "coinbase":
                last = float(data["price"])
            elif exchange == "kraken":
                data = data["result"]
                data = data[list(data)[0]]
                last = float(data["c"][0])
            elif exchange == "bitstamp":
                last = float(data["last"])
        except Exception as error:
            print(trace(error), {k: v for k, v in api.items() if k != "secret"})
        break

    now = int(time.time())

    doc = api["exchange"] + ".txt"
    data = {"last": last, "time": now}

    race_write(doc, json_dumps(data))

    # print (last, api["exchange"])


def aggregate(exchanges):

    data = {}
    for exchange in exchanges:
        try:
            doc = exchange + ".txt"
            data[exchange] = race_read_json(doc)
        except Exception as e:
            print(e.args)

    prices = []
    for k, v in data.items():
        if int(time.time()) - v["time"] < 300:
            prices.append(v["last"])
    median_price = median(prices)
    mean_price = sum(prices) / len(prices)

    for k, v in data.items():

        mad = abs(data[k]["last"] - median_price)
        data[k]["mad"] = mad
        data[k]["percent_mad"] = 100 * mad / median_price


    runtime = int(time.time() - BEGIN)
    print("\033c")
    print("Centralized Exchange BTC:USD", time.ctime(), "runtime:", runtime)
    print("\n", exchanges, "\n")
    pprint(data)
    print("")
    print("median   ", median_price)
    print("mean     ", mean_price)
    print("sources  ", len(prices))
    print("next update in 60 seconds...")

    pricefeed_cex = {
        "mean": mean_price,
        "median": median_price,
        "data": data,
    }

    race_write("pricefeed_cex.txt", median_price)


def fetch(exchanges):

    urls = return_urls()
    # while True:
    processes = {}
    for exchange in exchanges:
        api = {"url": urls[exchange], "exchange": exchange}
        api["pair"] = "BTC:USD"
        processes[exchange] = Process(target=get_price, args=(api,))
        processes[exchange].daemon = False
        processes[exchange].start()
        processes[exchange].join(20)
        processes[exchange].terminate()
    aggregate(exchanges)


def main():

    exchanges = return_urls().keys()

    print("\033c", "initializing cex feeds...")

    while 1:

        fetch(exchanges)
        time.sleep(60)


if __name__ == "__main__":
    main()
