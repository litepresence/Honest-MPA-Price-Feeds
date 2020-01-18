"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from bitcoinaverage.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://apiv2.bitcoinaverage.com/frontend/constants/exchangerates/local"


def ret_headers():
    """
    expect higher success rate by mimicking a legitimate browser header
    """
    return {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp"
            + ",image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": (
            "driftt_aid=872a5226-7de8-491f-860c-dbc232f057e8; DFTT_END_USER_PREV"
            + "_BOOTSTRAPPED=true; driftt_sid=7fad01bb-4d34-41b5-88e7-982bed7c4fe6"
        ),
        "DNT": "1",
        "Host": "bitcoinaverage.com",
        "If-Modified-Since": "Thu, 19 Dec 2019 09:14:17 GMT",
        "If-None-Match": 'W/"5dfb3f69-d04"',
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            + "like Gecko) Chrome/79.0.3945.79 Safari/537.36 OPR/66.0.3515.27"
        ),
    }


def bitcoinaverage(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, timeout=(6, 30)).json()["rates"]
        data = {}
        for key, val in ret.items():
            data["USD:" + key] = float(val["rate"])
        data = refine_data(data)
        race_write("bitcoinaverage_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("bitcoinaverage failed to load")


if __name__ == "__main__":

    bitcoinaverage(None)
