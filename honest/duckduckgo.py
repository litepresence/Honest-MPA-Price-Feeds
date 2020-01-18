"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from duckduckgo.com

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://duckduckgo.com/js/spice/currency/1/usd/"


def duckduckgo(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        data = {}
        currencies = ["KRW", "JPY", "RUB"]
        # AUD,CAD,COP,EUR,GBP,INR,MXN,MYR,ZAR containted in topConversions by default
        for currency in currencies:
            url = URL + currency
            raw = requests.get(url, timeout=(6, 30)).text
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
        race_write("duckduckgo_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("duckduckgo failed to load")


if __name__ == "__main__":

    duckduckgo(None)
