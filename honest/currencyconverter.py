"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

# CURRENCY CONVERTER API
# https://free.currconv.com/api/v7/convert?q=USD_PHP&compact=ultra&apiKey=KEY
# 100/hour two pairs per request

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["currencyconverter"]
URL = "https://free.currconv.com/api/v7/convert"
SYMBOLS = ["USD_EUR,USD_GBP", "USD_CNY,USD_KRW", "USD_JPY,USD_RUB"]


def currencyconverter(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        data = {}
        for symbol in SYMBOLS:
            params = {"compact": "y", "apiKey": KEY, "q": symbol}
            ret = requests.get(URL, params=params).json()
            for key, val in ret.items():
                data[key.replace("_", ":")] = val["val"]
        data = refine_data(data)
        race_write("currencyconverter_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("currencyconverter failed to load")


if __name__ == "__main__":

    currencyconverter(None)
