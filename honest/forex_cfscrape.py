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
from utilities import race_write, refine_data


def fxempire1(site):
    """
    live forex rates scraped from fxempire.com (backdoor to xignite)
    """
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
        ret = cfscrape_requests.get(url, timeout=(15, 15)).json()
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
        print(site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


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
        )
        # print(data)
        # {"Symbol":"CHFJPY","Bid":"1.1","Ask":"1.2","Spread":"0.1","ProductType":"1",}
        raw = json_loads(data)
        data = {}
        for item in raw:
            symbol = item["Symbol"]
            if symbol.isupper() and (len(symbol) == 6):
                symbol = symbol[:3] + ":" + symbol[-3:]
                data[symbol] = (float(item["Ask"]) + float(item["Bid"])) / 2
        data = refine_data(data)
        print(site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def bloomberg(site):
    """
    live forex rates scraped from bloomberg.com
    """
    uri = "https://www.bloomberg.com/markets/api/bulk-time-series/price/"
    endpoint = (
        "USDCNY%3ACUR,USDRUB%3ACUR,USDJPY%3ACUR,USDEUR%3ACUR,USDKRW%3ACUR"
        + ",XAUUSD%3ACUR,XAGUSD%3ACUR"
    )
    url = uri + endpoint
    headers = {
        "authority": "www.bloomberg.com",
        "method": "GET",
        "path": (
            "/markets/api/comparison/data?securities="
            + "USDCNY%3ACUR,USDRUB%3ACUR,USDJPY%3ACUR,USDEUR%3ACUR,USDKRW%3ACUR"
            + ",XAUUSD%3ACUR,XAGUSD%3ACUR"
            + "&securityType=CURRENCY&locale=en"
        ),
        "scheme": "https",
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/"
            + "webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "cookie": (
            "bbAbVisits=1; _pxhd=e24b47c64d37711c147cfb3c4b35c845563d2f9831b"
            + "03d9189f8cd761bc2be4f:d78eeb01-34c9-11ea-8f86-51d2aad9afb3; _px"
            + "vid=d78eeb01-34c9-11ea-8f86-51d2aad9afb3; _reg-csrf=s%3Ab0pWvbcs"
            + "UtrjYeJ0T2GrTaaD.8kaQlvHchJ1D%2FZZMaQWQiTizJTxrqqyzzuEZHEvlQNw;"
            + " agent_id=7989385a-d6d9-4446-b7aa-3c937407862b;"
            + " session_id=5702901e-d5fe-41e7-b259-df46322015e0;"
            + " session_key=3179869387f4c4ec4385e0d16222f0e59f48c47f;"
            + " _user-status=anonymous; _is-ip-whitelisted=false;"
            + " _user-ip=91.132.137.116; trc_cookie_storage=taboola%2520global%253"
            + "Auser-id%3D2f4acdc6-7c3c-412c-8766-d9c80dcffc38-tuct513df3e;"
            + " bdfpc=004.0586371899.1578785723722;"
            + " _reg-csrf-token=4ZxUa9q8-fkNXQkoHHXhnobWne1sDlIVcKEQ"
        ),
        "dnt": "1",
        "if-none-match": 'W/"lZU52eQYxjadyNKGCyftEg=="',
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
        ret = cfscrape_requests.get(url, timeout=(15, 15)).json()
        data = {}
        for item in ret:
            symbol = item["id"].replace(":CUR", "")
            symbol = symbol[:3] + ":" + symbol[-3:]
            data[symbol] = float(item["lastPrice"])
        data["USD:XAG"] = 1 / data.pop("XAG:USD")
        data["USD:XAU"] = 1 / data.pop("XAU:USD")
        data = refine_data(data)
        print(site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def bitcoinaverage(site):
    """
    live forex rates scraped from bitcoinaverage.com
    """
    url = "https://apiv2.bitcoinaverage.com/frontend/constants/exchangerates/local"
    try:
        session = requests.Session()
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(url, timeout=(15, 15)).json()["rates"]
        data = {"USD:" + key: float(val["rate"]) for key, val in ret.items()}
        data = refine_data(data)
        print(site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")


def investing(site):
    """
    live forex rates scraped from investing.com
    https://www.investing.com/webmaster-tools/live-currency-cross-rates
    """
    url = (
        "https://www.widgets.investing.com/live-currency-cross-rates?"
        + "theme=darkTheme&cols=last&pairs=3,2111,2124,2126,650,962711,69,68"
    )
    headers = {
        "href": (
            "https://www.investing.com?utm_source=WMT&amp;utm_medium=referral&amp;"
            + "utm_campaign=LIVE_CURRENCY_X_RATES&amp;utm_content=Footer%20Link"
        ),
        "target": "_blank",
        "rel": "nofollow",
    }
    try:
        session = requests.Session()
        session.headers = headers
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(url, headers=headers, timeout=(15, 15)).text
        lines = ret.split('target="_blank"')
        lines = [i.replace(" ", "").replace(",", "") for i in lines]
        lines = [i for i in lines if "askpid" in i]
        lines = [i.split("hiddenFour")[0] for i in lines]
        data = {
            item.split("</a>")[0].replace(">", ""): item.split('last">')[1]
            for item in lines
        }

        data = {k.replace("/", ":"): v.split("</div>")[0] for k, v in data.items()}
        data = {k: float(v) for k, v in data.items()}
        data["USD:XAG"] = 1 / data.pop("XAG:USD")
        data["USD:XAU"] = 1 / data.pop("XAU:USD")
        data = refine_data(data)
        print(site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(f"{site} failed to load")
