"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped with cloudfare nodejs spoofing from 4 sources:

bitcoinaverage, bloomberg, fxcm, fxempire

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps
from json import loads as json_loads

import cfscrape
# THIRD PARTY MODULES
import requests
# PRICE FEED MODULES
from utilities import it, race_write, refine_data


def fxempire1(site):
    """
    live forex rates scraped from fxempire.com (backdoor to xignite)
    """
    # FIXME this endpoint no longer exists, must use webscraping on https://www.fxempire.com/currencies
    return
    url = "https://www.fxempire.com/api/v1/en/markets/list"
    headers = {
        "authority": "www.fxempire.com",
        "method": "GET",
        "path": "/api/v1/en/markets/list",
        "scheme": "https",
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
            + "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "dnt": "1",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            + " (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36 OPR/66.0.3515.27"
        ),
    }
    try:
        session = requests.Session()
        session.headers = headers
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(url, timeout=(15, 15))
        print(ret.text)
        ret.json()
        data = {}
        for item in ret["forex"]:
            if item:
                try:
                    pair = item["name"].replace("/", ":")
                    price = item["value"]
                    data[pair] = float(price)
                except:
                    pass
        for item in ret["commodities"]:
            try:
                if item["symbol"] in ["XAUUSD", "XAGUSD"]:
                    pair = "USD:" + item["symbol"].replace("USD", "")
                    price = 1 / float(item["value"])
                    data[pair] = price
            except:
                pass
        data = {k: v for k, v in data.items() if "RUB" not in k}  # RUBLE is stale
        data = refine_data(data)
        print(it("purple", "FOREX CFSCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        raise
        print(it("purple", "FOREX CFSCRAPE:"), it("red", f"{site} failed to load"))


def fxcm(site):
    """
    live forex rates scraped from fxcm.com
    """
    timestamp = int(time.time() * 1000) - 1000
    url = f"https://ratesjson.fxcm.com/DataDisplayer?t={timestamp}"
    headers = {
        "authority": "www.fxcm.com",
        "method": "GET",
        "path": "/api/v1/en/markets/list",
        "scheme": "https",
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
            + "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "dnt": "1",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            + "like Gecko) Chrome/79.0.3945.79 Safari/537.36 OPR/66.0.3515.27"
        ),
    }
    try:
        # fails during some hours of day
        session = requests.Session()
        session.headers = headers
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(url, timeout=(15, 15)).text
        # print (ret)
        data = (
            ret.replace(" ", "")
            .replace('null({"Rates":', "")
            .replace(",}]});", "}]")
            .replace(",}", "}")
            .replace("});", "")
            .replace("NaN", "null")
        )
        # {"Symbol":"CHFJPY","Bid":"1.1","Ask":"1.2","Spread":"0.1","ProductType":"1",}
        raw = json_loads(data)
        data = {}
        for item in raw:
            symbol = item["Symbol"]
            if symbol.isupper() and (len(symbol) == 6):
                symbol = symbol[:3] + ":" + symbol[-3:]
                data[symbol] = (float(item["Ask"]) + float(item["Bid"])) / 2
        data = refine_data(data)
        print(it("purple", "FOREX CFSCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX CFSCRAPE:"), it("red", f"{site} failed to load"))
