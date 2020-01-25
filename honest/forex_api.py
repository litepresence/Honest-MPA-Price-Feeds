"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

free keyed forex API methods from 7 sources:

barchart, currencyconverter, datadt, fxmarket, fscapi, fixerio, openexchangerates

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys


def barchart(site):
    """
    https://ondemand.websol.barchart.com/getQuote.json?apikey=key&symbols=AAPL%2CGOOG
    limit 400 per day
    """
    key = api_keys()[site]
    url = "https://marketdata.websol.barchart.com/getQuote.json"
    symbols = "^USDEUR,^USDJPY,^USDGBP,^USDCNY,^USDKRW,^USDRUB"
    params = {"symbols": symbols, "apikey": key}
    try:
        ret = requests.get(url, params=params, timeout=(15, 15)).json()["results"]
        data = {}
        for item in ret:
            try:
                data[item["symbol"].replace("^USD", "USD:")] = float(item["lastPrice"])
            except:
                pass
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def currencyconverter(site):
    """
    https://free.currconv.com/api/v7/convert?q=USD_PHP&compact=ultra&apikey=key
    100/hour two pairs per request
    """
    key = api_keys()[site]
    url = "https://free.currconv.com/api/v7/convert"
    symbols = ["USD_EUR,USD_GBP", "USD_CNY,USD_KRW", "USD_JPY,USD_RUB"]
    try:
        data = {}
        for symbol in symbols:
            try:
                params = {"compact": "y", "apikey": key, "q": symbol}
                ret = requests.get(url, params=params, timeout=(15, 15)).json()
                for key, val in ret.items():
                    data[key.replace("_", ":")] = float(val["val"])
            except:
                pass
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def fxmarket(site):
    """
    https://fixer.io/documentation
    https://fxmarketapi.com/apilive?api_key=key&currency=EURUSD,GBPUSD
    1000 / month
    """
    key = api_keys()[site]
    url = "https://fxmarketapi.com/apilive"
    symbols = "USDEUR,USDGBP,USDCNY,USDKRW,USDRUB,USDJPY"
    params = {"currency": symbols, "api_key": key}
    try:
        ret = requests.get(url, params=params, timeout=(15, 15)).json()["price"]
        data = {k.replace("USD", "USD:"): float(v) for k, v in ret.items()}
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def fscapi(site):
    """
    https://fcsapi.com/document/forex-api
    https://fcsapi.com/api/forex/latest?symbol=USD/JPY&access_key=key
    limit 10 per minute
    """
    key = api_keys()[site]
    url = "https://fcsapi.com/api/forex/latest"
    symbols = "USD/EUR,USD/JPY,USD/GBP,USD/CNY,USD/KRW,USD/RUB"
    params = {"symbol": symbols, "access_key": key}
    try:
        ret = requests.get(url, params=params, timeout=(15, 15)).json()["response"]
        data = {}
        for item in ret:
            try:
                data[item["symbol"].replace("/", ":")] = float(item["price"])
            except:
                pass
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def fixerio(site):
    """
    http://data.fixer.io/api/latest?access_key=key&base=USD&symbols=AUD,CAD
    limit 1000 per month (hourly updates)
    """
    key = api_keys()[site]
    url = "http://data.fixer.io/api/latest"
    symbols = "USD,RUB,GBP,CNY,KRW,JPY"
    params = {"symbols": symbols, "access_key": key}
    try:
        ret = requests.get(url, params=params, timeout=(15, 15)).json()["rates"]
        eurusd = float(ret["USD"])
        usdeur = 1 / eurusd
        data = {
            "USD:EUR": usdeur,
            "USD:RUB": float(ret["RUB"]) * usdeur,
            "USD:GBP": float(ret["GBP"]) * usdeur,
            "USD:CNY": float(ret["CNY"]) * usdeur,
            "USD:KRW": float(ret["KRW"]) * usdeur,
            "USD:JPY": float(ret["JPY"]) * usdeur,
        }
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def openexchangerates(site):
    """
    https://docs.openexchangerates.org/
    https://openexchangerates.org/api/latest.json?app_id=key
    limit 1000 per month (hourly updates)
    """
    key = api_keys()[site]
    url = "https://openexchangerates.org/api/latest.json"
    params = {"app_id": key}
    symbols = ["EUR", "RUB", "GBP", "KRW", "CNY", "JPY"]
    try:
        ret = requests.get(url, params=params, timeout=(15, 15)).json()["rates"]
        data = {}
        for key, val in ret.items():
            if key in symbols:
                data["USD:" + key] = float(val)
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")
