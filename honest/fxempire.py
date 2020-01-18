"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from fxempire.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests
import cfscrape

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://www.fxempire.com/api/v1/en/markets/list"


def ret_headers():
    """
    expect higher success rate by mimicking a legitimate browser header
    """
    return {
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


def fxempire(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        session = requests.Session()
        session.headers = ret_headers()
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(URL, timeout=(6, 30)).json()
        data = {}
        for item in ret["forex"]:
            if item:
                try:
                    pair = item["name"].replace("/", ":")
                    price = item["value"]
                    data[pair] = float(price)
                except:
                    pass
        data = refine_data(data)
        race_write("fxempire_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("fxempire failed to load")


if __name__ == "__main__":

    fxempire(None)
