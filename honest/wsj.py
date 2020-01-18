"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from wsj.com

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://api.wsj.net/api/deltoro-mw/marketwatchsite/quote/currency/convert"


def wsj(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        currencies = ["EUR", "CNY", "RUB", "KRW", "JPY"]
        data = {}
        for currency in currencies:
            endpoint = f"?from=USD&to={currency}USD&amount=1.00"
            url = URL + endpoint
            raw = requests.get(url, timeout=(6, 30)).text
            data["USD:" + currency] = float(raw)
            time.sleep(1)
        data = refine_data(data)
        race_write("wsj_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("wsj failed to load")


if __name__ == "__main__":

    wsj(None)
