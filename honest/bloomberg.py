"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from bloomberg.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests
import cfscrape

# PRICE FEED MODULES
from utilities import race_write, refine_data

URI = "https://www.bloomberg.com/markets/api/bulk-time-series/price/"
ENDPOINT = "USDCNY%3ACUR,USDRUB%3ACUR,USDJPY%3ACUR,USDEUR%3ACUR,USDKRW%3ACUR"
URL = URI + ENDPOINT


def ret_headers():
    """
    expect higher success rate by mimicking a legitimate browser header
    """
    return {
        "authority": "www.bloomberg.com",
        "method": "GET",
        "path": (
            "/markets/api/comparison/data?securities=EURUSD%3ACUR,USDJPY%3ACUR,"
            + "GBPUSD%3ACUR,AUDUSD%3ACUR,USDCAD%3ACUR,USDCHF%3ACUR,EURJPY%3ACUR,"
            + "EURGBP%3ACUR,USDHKD%3ACUR,EURCHF%3ACUR,USDKRW%3ACUR"
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


def bloomberg(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        session = requests.Session()
        session.headers = ret_headers()
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(URL, timeout=(6, 30)).text
        ret = requests.get(URL, headers=ret_headers()).json()
        data = {}
        for item in ret:
            symbol = item["id"].replace(":CUR", "")
            symbol = symbol[:3] + ":" + symbol[-3:]
            data[symbol] = float(item["lastPrice"])
        data = refine_data(data)
        race_write("bloomberg_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("bloomberg failed to load")


if __name__ == "__main__":

    bloomberg(None)
