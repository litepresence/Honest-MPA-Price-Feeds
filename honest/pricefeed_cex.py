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
from pprint import pprint
from json import dumps as json_dumps
from multiprocessing import Process, Value
from statistics import median
from datetime import datetime
from calendar import timegm
from random import random

# THIRD PARTY MODULES
import requests

# PROPRIETARY MODULES
from exchanges import EXCHANGES
from utilities import race_write, race_read_json, trace

# GLOBAL CONSTANTS
TIMEOUT = 15
ATTEMPTS = 10
DETAIL = False
BEGIN = int(time.time())
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def return_urls():
    """
    dictionary of api domain names
    """
    return {
        "gateio": "https://api.gateio.ws",
        "coinbase": "https://api.pro.coinbase.com",
        "bittrex": "https://api.bittrex.com",
        "bitfinex": "https://api-pub.bitfinex.com",
        "kraken": "https://api.kraken.com",
        "poloniex": "https://www.poloniex.com",
        "binance": "https://api.binance.com",
        "bitstamp": "https://www.bitstamp.net",
        "huobi": "https://api.huobi.pro",
        "hitbtc": "https://api.hitbtc.com",
    }


# FORMATING & TYPESETTING
def print_results(cex):
    """
    log the cex price feed to terminal
    """
    runtime = int(time.time() - BEGIN)
    print(f"Centralized Exchange", time.ctime(), "runtime:", runtime)
    pprint(cex)


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
        if asset == "DOGE":
            asset = "XDG"
    if exchange == "poloniex":
        if asset == "XLM":
            asset = "STR"
        if currency == "USD":
            currency = "USDT"
        if asset == "BCH":
            asset = "BCHABC"
    if exchange == "binance" and currency == "USD":
        currency = "USDT"
    if exchange == "bitfinex":
        if asset == "BCH":
            asset = "BAB"
        if asset == "DASH":
            asset = "DSH"
    symbols = {
        "gateio": (asset + "_" + currency),
        "bittrex": (asset + "-" + currency),
        "bitfinex": (asset + currency),
        "binance": (asset + currency),
        "poloniex": (currency + "_" + asset),
        "coinbase": (asset + "-" + currency),
        "kraken": (asset.lower() + currency.lower()),
        "bitstamp": (asset.lower() + currency.lower()),
        "huobi": (asset.lower() + currency.lower()),
        "hitbtc": (asset + currency),
    }

    symbol = symbols[exchange]
    print(symbol, exchange)
    return symbol


# SUBPROCESS REMOTE PROCEDURE CALL
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
    try:
        data = resp.json()
    except:
        print(resp.text)
    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10**6 * api["nonce"]))
        + "_{}_public.txt".format(api["exchange"])
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
        time.sleep(i**2)
    # the doc was created by the subprocess; read and destroy it
    doc = (
        api["exchange"]
        + api["pair"]
        + str(int(10**6 * api["nonce"]))
        + "_{}_public.txt".format(api["exchange"])
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


# PRIMARY EVENT METHODS
def get_price(api):
    """
    Last Price as float
    """
    doc = api["exchange"] + api["pair"] + ".txt"
    race_write(doc, {})
    exchange = api["exchange"]
    symbol = symbol_syntax(exchange, api["pair"])
    endpoints = {
        "gateio": "/api/v4/spot/tickers",
        "bittrex": "/v3/markets/tickers",
        "bitfinex": "/v2/ticker/t{}".format(symbol),
        "binance": "/api/v1/ticker/allPrices",
        "poloniex": "/public",
        "coinbase": "/products/{}/ticker".format(symbol),
        "kraken": "/0/public/Ticker",
        "bitstamp": f"/api/v2/ticker/{symbol}",  # "bitstamp": "/api/ticker",
        "huobi": "/market/trade",
        "hitbtc": f"/api/2/public/ticker/{symbol}",
    }
    params = {
        "gateio": {},
        "bittrex": {},
        "bitfinex": {"market": symbol},
        "binance": {},
        "poloniex": {"command": "returnTicker"},
        "coinbase": {"market": symbol},
        "kraken": {"pair": [symbol]},
        "bitstamp": {},
        "huobi": {"symbol": symbol},
        "hitbtc": {},
    }
    api["endpoint"] = endpoints[exchange]
    api["params"] = params[exchange]
    while 1:
        try:
            data = process_request(api)
            if exchange == "gateio":
                data = {d["currency_pair"]: float(d["last"]) for d in data}
                last = float(data[symbol])
            elif exchange == "bittrex":
                data = {d["symbol"]: float(d["lastTradeRate"]) for d in data}
                last = float(data[symbol])
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
            elif exchange == "huobi":
                last = float(data["tick"]["data"][-1]["price"])
            elif exchange == "hitbtc":
                last = float(data["last"])
        except Exception as error:
            print(trace(error), {k: v for k, v in api.items() if k != "secret"})
        break
    now = int(time.time())
    print("writing", doc)
    data = {"last": last, "time": now}
    race_write(doc, json_dumps(data))


def aggregate(exchanges, api):
    """
    post process data from all exchanges to extract medians and means
    """
    data = {}
    for exchange in exchanges:
        try:
            doc = exchange + api["pair"] + ".txt"
            print("reading", doc)
            json_data = race_read_json(doc)
            if json_data:
                data[exchange] = json_data
        except Exception as error:
            print(error.args)
    prices = []
    for _, val in data.items():
        try:
            if int(time.time()) - val["time"] < 300:
                prices.append(val["last"])
        except Exception as error:
            print(error.args)
    median_price = median(prices)
    mean_price = sum(prices) / len(prices)
    return {
        "mean": mean_price,
        "median": median_price,
        "data": data,
    }


def fetch(exchanges, api):
    """
    multiprocess wrap external request for durability
    """
    urls = return_urls()
    processes = {}
    for exchange in exchanges:
        api["url"] = urls[exchange]
        api["exchange"] = exchange
        processes[exchange] = Process(target=get_price, args=(api,))
        processes[exchange].daemon = False
        processes[exchange].start()
    for exchange in exchanges:
        processes[exchange].join(20)
        processes[exchange].terminate()
    return aggregate(exchanges, api)


def pricefeed_cex():
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
    cex = {}

    for pair in EXCHANGES:
        cex[pair] = fetch(EXCHANGES[pair], {"pair": pair})

    race_write("pricefeed_cex.txt", cex)
    return cex


def main():
    """
    demo a single cex pricefeed
    """
    print("initializing cex feeds...")
    cex = pricefeed_cex()
    print_results(cex)


if __name__ == "__main__":

    main()
