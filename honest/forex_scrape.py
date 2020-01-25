"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from 8 sources:

liveusd, freeforex, finviz, yahoo, wsj, duckduckgo (xe), wocu, oanda

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps
from json import loads as json_loads

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data


def liveusd(site):
    """
    live forex rates scraped from liveusd.com
    """
    url = "http://liveusd.com/veri/refresh/total.php"
    try:
        ret = requests.get(url, timeout=(15, 15)).text
        ret = ret.replace(" ", "").split("\n")
        data = {}
        for item in ret:
            if item:
                try:
                    pair = item.split(":")[0].replace("USD", "USD:")
                    price = item.split(":")[1]
                    data[pair] = float(price)
                except:
                    pass
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def freeforex(site):
    """
    live forex rates scraped from freeforexapi.com
    """
    url = "https://www.freeforexapi.com/api/live?pairs="
    currencies = "EURUSD,EURGBP,GBPUSD,USDJPY,AUDUSD,USDCHF,NZDUSD,USDCAD,USDZAR"
    url += currencies
    try:
        ret = requests.get(url, timeout=(15, 15)).json()["rates"]
        data = {}
        for key, val in ret.items():
            symbol = key[:3] + ":" + key[-3:]
            data[symbol] = float(val["rate"])
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def finviz(site):
    """
    live forex rates scraped from finviz.com
    """
    url = "https://finviz.com/api/forex_all.ashx?timeframe=m5"
    try:
        ret = requests.get(url, timeout=(15, 15)).json()
        data = {}
        data["AUD:USD"] = float(ret["AUDUSD"]["last"])
        data["EUR:GBP"] = float(ret["EURGBP"]["last"])
        data["EUR:USD"] = float(ret["EURUSD"]["last"])
        data["GBP:JPY"] = float(ret["GBPJPY"]["last"])
        data["GBP:USD"] = float(ret["GBPUSD"]["last"])
        data["USD:CAD"] = float(ret["USDCAD"]["last"])
        data["NZD:USD"] = float(ret["NZDUSD"]["last"])
        data["USD:CHF"] = float(ret["USDCHF"]["last"])
        data["USD:JPY"] = float(ret["USDJPY"]["last"])
        data["XAG:USD"] = float(ret["SI"]["last"])
        data["XAU:USD"] = float(ret["GC"]["last"])
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def yahoo(site):
    """
    live forex rates scraped from yahoo finance
    """
    uri = "https://query1.finance.yahoo.com/v7/finance/spark?symbols=USD"
    try:
        currencies = ["EUR", "CNY", "RUB", "KRW", "JPY"]
        data = {}
        for currency in currencies:
            endpoint = f"{currency}%3DX&range=1m&interval=1m"
            url = uri + endpoint
            raw = requests.get(url, timeout=(15, 15)).json()
            ret = raw["spark"]["result"][0]["response"][0]["meta"]["regularMarketPrice"]
            data["USD:" + currency] = float(ret)
            time.sleep(1)
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def wsj(site):
    """
    live forex rates scraped from wsj.com
    """
    uri = "https://api.wsj.net/api/deltoro-mw/marketwatchsite/quote/currency/convert"
    try:
        currencies = ["EUR", "CNY", "RUB", "KRW", "JPY"]
        data = {}
        for currency in currencies:
            endpoint = f"?from=USD&to={currency}USD&amount=1.00"
            url = uri + endpoint
            raw = requests.get(url, timeout=(15, 15)).text
            data["USD:" + currency] = float(raw)
            time.sleep(1)
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def duckduckgo(site):
    """
    live forex rates scraped from XE via duckduckgo.com
    """
    uri = "https://duckduckgo.com/js/spice/currency/1/usd/"
    try:
        data = {}
        currencies = ["KRW", "JPY", "RUB"]
        # AUD,CAD,COP,EUR,GBP,INR,MXN,MYR,ZAR containted in topConversions by default
        for currency in currencies:
            url = uri + currency
            raw = requests.get(url, timeout=(15, 15)).text
            raw = (
                raw.replace("\n", "")
                .replace(" ", "")
                .replace("ddg_spice_currency(", "")
                .replace(");", "")
            )
            ret = json_loads(raw)
            data["USD:" + currency] = float(ret["conversion"]["converted-amount"])
            time.sleep(1)
            for item in ret["topConversions"]:
                data["USD:" + item["to-currency-symbol"]] = float(
                    item["converted-amount"]
                )
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def wocu(site):
    """
    live forex rates scraped from wocu.com
    """

    def parse(raw, symbol):
        """
        attempt to extract a float value from the html matrix
        """
        return float(raw.split(symbol)[1].split("</td>")[2].split(">")[1])

    url = "http://54.154.247.217/wocutab.php"
    symbols = ["EUR", "RUB", "GBP", "KRW", "CNY", "JPY"]
    try:
        raw = requests.get(url, timeout=(15, 15)).text
        data = {}
        for symbol in symbols:
            try:
                data["USD:" + symbol] = parse(raw, symbol)
            except:
                pass
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def oanda(site):
    """
    make external request, decode, decrypt, reformat to dict
    """
    key = "aaf6cb4f0ced8a211c2728328597268509ade33040233a11af"
    url = "https://www1.oanda.com/lfr/rates_lrrr?tstamp="

    def hex_decode(raw):
        """
        latin-1 from hexidecimal
        """
        return bytes.fromhex("0" + raw if len(raw) % 2 else raw).decode("latin-1")

    def rc4(cypher, key):
        """
        decryption of rc4 stream cypher from latin-1
        """
        idx1 = 0
        output = []
        r256 = [*range(256)]
        for idx2 in range(256):
            idx1 = (idx1 + r256[idx2] + ord(cypher[idx2 % len(cypher)])) % 256
            r256[idx2], r256[idx1] = r256[idx1], r256[idx2]
        idx1, idx2 = 0, 0
        for _, item in enumerate(key):
            idx2 = (idx2 + 1) % 256
            idx1 = (idx1 + r256[idx2]) % 256
            r256[idx2], r256[idx1] = r256[idx1], r256[idx2]
            output.append(chr(ord(item) ^ r256[(r256[idx2] + r256[idx1]) % 256]))
        return ("").join(output)

    try:
        while True:
            try:
                millies = str(int(round(time.time() * 1000)))
                raw = requests.get(url + millies, timeout=(15, 15)).text
                hex_decoded = hex_decode(raw)
                decrypted = rc4(key, hex_decoded)
                break
            except:
                time.sleep(5)
        content = decrypted.split("\n")
        parsed = {
            raw.split("=")[0]: (float(raw.split("=")[1]) + float(raw.split("=")[2])) / 2
            for raw in content
        }
        data = {}
        for pair, price in parsed.items():
            data[pair.replace("/", ":")] = float(price)
        data = refine_data(data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")
