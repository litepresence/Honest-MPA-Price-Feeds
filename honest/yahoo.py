"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from yahoo.com

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://query1.finance.yahoo.com/v7/finance/spark?symbols=USD"


def yahoo(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        currencies = ["EUR", "CNY", "RUB", "KRW", "JPY"]
        data = {}
        for currency in currencies:
            endpoint = f"{currency}%3DX&range=1m&interval=1m"
            url = URL + endpoint
            raw = requests.get(url, timeout=(6, 30)).json()
            ret = raw["spark"]["result"][0]["response"][0]["meta"]["regularMarketPrice"]
            data["USD:" + currency] = float(ret)
            time.sleep(1)
        data = refine_data(data)
        race_write("yahoo_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("yahoo failed to load")


if __name__ == "__main__":

    yahoo(None)
