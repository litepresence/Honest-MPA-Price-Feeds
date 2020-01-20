"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

FSCAPI

https://fcsapi.com/document/forex-api
https://fcsapi.com/api/forex/latest?symbol=USD/JPY&access_key=KEY

limit 10 per minute

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["fscapi"]
URL = "https://fcsapi.com/api/forex/latest"
SYMBOLS = "USD/EUR,USD/JPY,USD/GBP,USD/CNY,USD/KRW,USD/RUB"
PARAMS = {"symbol": SYMBOLS, "access_key": KEY}


def fscapi(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, params=PARAMS).json()["response"]
        data = {}
        for item in ret:
            data[item["symbol"].replace("/", ":")] = item["price"]
        data = refine_data(data)
        race_write("fscapi_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("fscapi failed to load")


if __name__ == "__main__":

    fscapi(None)
