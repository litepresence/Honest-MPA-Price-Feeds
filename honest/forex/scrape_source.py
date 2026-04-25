"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from 14 sources:

liveusd, freeforex, finviz, yahoo, wsj, duckduckgo(xe), wocu, oanda, reuters(refinitiv)
fxrate, forextime, currencyme, forexrates, exchangeratewidget


litepresence2020
"""

import sys
# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps
from json import loads as json_loads

# THIRD PARTY MODULES
import requests
# PRICE FEED MODULES
from utilities import it, race_write, refine_data


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
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def duckduckgo(site):
    """
    live forex rates scraped from XE via duckduckgo.com
    returns dict in format: {"USD:CNY": 7.24, "USD:XAU": 0.00048, ...}
    """
    uri = "https://duckduckgo.com/js/spice/currency/1/usd/"
    try:
        data = {}
        currencies = ["CNY", "XAU", "XAG", "RUB", "EUR", "GBP", "JPY", "KRW"]
        
        for currency in currencies:
            # XAU/XAG need inverted query: XAU->USD not USD->XAU
            if currency in ["XAU", "XAG"]:
                url = uri.replace("usd/", "") + currency + "/usd"
            else:
                url = uri + currency
                
            raw = requests.get(url, timeout=(15, 15), headers={
                "User-Agent": "Mozilla/5.0"
            }).text
            
            # Strip JSONP wrapper: ddg_spice_currency({...});
            raw = (
                raw.strip()
                .replace("\n", "")
                .replace(" ", "")
                .replace("ddg_spice_currency(", "")
                .rstrip(");")
            )
            
            ret = json_loads(raw)
            
            if currency in ["XAU", "XAG"]:
                # Response is XAU->USD, we want USD->XAU (invert)
                mid_val = [i["mid"] for i in ret["to"] if i["quotecurrency"] == "USD"][0]
                data["USD:" + currency] = round(1 / float(mid_val), 8)
            else:
                # Direct: USD->XXX
                mid_val = [i["mid"] for i in ret["to"] if i["quotecurrency"] == currency][0]
                data["USD:" + currency] = round(float(mid_val), 6)
                
            time.sleep(0.5)  # polite delay
            
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
        return data
        
    except Exception as e:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load: {e}"))
        return {}


def wocu(site):
    """
    live forex rates scraped from wocu.com
    XAU XAG are not precise
    """

    def parse(raw, symbol):
        """
        attempt to extract a float value from the html matrix
        """
        return float(raw.split(symbol)[1].split("</td>")[2].split(">")[1])

    url = "http://54.154.247.217/wocutab.php"
    symbols = ["CNY", "EUR", "GBP", "KRW", "JPY", "RUB", "XAU", "XAG"]
    try:
        raw = requests.get(url, timeout=(15, 15)).text
        data = {}
        for symbol in symbols:
            try:
                data["USD:" + symbol] = parse(raw, symbol)
            except:
                pass
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def oanda(site):
    """
    live forex rates scraped from oanda via acuity trading widget
    """
    symbols = ["EUR", "RUB", "GBP", "KRW", "CNY", "JPY", "XAG", "XAU"]
    base_url = "https://dashboard.acuitytrading.com/OandaPriceApi/GetPrices"
    try:
        data = {}
        # Fetch all instruments in one call (more efficient than per-symbol requests)
        params = {"widgetName": "oandaliverates", "apikey": "4b12e6bb-7ecd-49f7-9bbc-2e03644ce41f"}
        payload = {"lang": "en-GB", "region": "OC", "instrumentType": "currency"}
        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        response = requests.post(base_url, params=params, headers=headers, data=payload, timeout=10)
        instruments = response.json() if response.ok else []
        
        for symbol in symbols:
            try:
                # Look for USD_SYMBOL or SYMBOL_USD pair formats
                pair1, pair2 = f"USD_{symbol}", f"{symbol}_USD"
                match = next((inst for inst in instruments if inst.get("Instrument") in (pair1, pair2)), None)
                if match:
                    # Use ask price ("s") as reference rate; change to "b" for bid or calc mid if needed
                    rate = float(match.get("s", 0))
                    data[f"USD:{symbol}"] = rate
            except:
                pass
        
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def currencyme(site):
    """
    live forex rates scraped from currency.me.uk
    """
    symbols = ["CNY", "EUR", "GBP", "KRW", "JPY", "RUB"]
    url = "https://www.currency.me.uk/remote/ER-CCCS2-AJAX.php"
    try:
        data = {}
        for symbol in symbols:
            try:
                params = {"ConvertTo": symbol, "ConvertFrom": "USD", "amount": 1}
                raw = requests.get(url, params=params, timeout=(15, 15)).text
                data["USD:" + symbol] = float(raw.replace(" ", ""))
            except:
                pass
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def ratewidget(site):
    """
    live forex rates scraped from exchangeratewidget.com
    """
    url = "https://www.exchangeratewidget.com/converter.php?v=11&t="
    symbols = ["USDEUR", "USDGBP", "USDJPY", "USDCNY", "USDRUB", "USDKRW"]
    for symbol in symbols:
        url += symbol + ","
    try:
        data = {}
        raw = requests.get(url, timeout=20).text
        for symbol in symbols:
            currency = symbol.replace("USD", "")
            price = raw.split(currency)[1].split("</span>")[1].split(">")[1]
            data["USD:" + currency] = float(price)
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def forexrates(site):
    """
    live forex rates scraped from forexrates.net
    """

    def parse(raw):
        """
        remove xml tags, return list of rates split with =
        """
        lines = [i.split(";")[0] for i in raw.split("Values")]
        lines.pop(0)
        return [
            i.replace('"', "").replace("[", "").replace("]", "").replace(" ", "")
            for i in lines
        ]

    url = "https://www.forexrates.net/widget/FR-FRW-2.php?"
    symbols = "c1=USD/EUR&c2=USD/GBP&c3=USD/RUB&c4=USD/JPY&c5=USD/CNY"
    url += symbols
    try:
        raw = requests.get(url, timeout=20).text
        rates = parse(raw)
        data = {}
        for rate in rates:
            symbol = rate.split("=")[0].replace("USD", "USD:")
            price = float(rate.split("=")[1])
            data[symbol] = price
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))


def aastock(site):
    """
    live forex rates scraped from aastock.com (morningstar backdoor)
    """

    uri = "http://www.aastocks.com/en/resources/datafeed/getrtcurconvert.ashx?curr="
    symbols = "USDCNY,USDEUR,USDGBP,USDKRW,USDJPY,USDXAU,USDXAG"
    url = uri + symbols

    try:
        raw = requests.get(url).json()
        data = {}
        for item in raw:
            if item["to"] == "USD":
                if item["from"] in ["XAU", "XAG"]:
                    data[item["to"] + ":" + item["from"]] = 1 / float(item["price"])
            else:
                data[item["symbol"].replace("USD", "USD:")] = float(item["price"])
        data = refine_data(data)
        print(it("purple", "FOREX SCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX SCRAPE:"), it("red", f"{site} failed to load"))
