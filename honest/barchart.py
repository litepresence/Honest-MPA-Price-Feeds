"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

BARCHART

https://ondemand.websol.barchart.com/getQuote.json?apikey=KEY&symbols=AAPL%2CGOOG

limit 400 per day

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["barchart"]
URL = "https://ondemand.websol.barchart.com/getQuote.json"
URL = "https://marketdata.websol.barchart.com/getQuote.json"

SYMBOLS = "^USDEUR,^USDJPY,^USDGBP,^USDCNY,^USDKRW,^USDRUB"
PARAMS = {"symbols": SYMBOLS, "apikey": KEY}


def barchart(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, params=PARAMS).json()["results"]
        data = {}
        for item in ret:
            data[item["symbol"].replace("^USD", "USD:")] = item["lastPrice"]
        data = refine_data(data)
        race_write("barchart_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("barchart failed to load")


if __name__ == "__main__":

    barchart(None)
