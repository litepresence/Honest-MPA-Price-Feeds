"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

FIXER.IO

http://data.fixer.io/api/latest?access_key=KEY&base=USD&symbols=AUD,CAD,PLN,MXN

limit 1000 per month (hourly updates)

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["fixerio"]
URL = "http://data.fixer.io/api/latest"
SYMBOLS = "USD,RUB,GBP,CNY,KRW,JPY"
PARAMS = {"symbols": SYMBOLS, "access_key": KEY}


def fixerio(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, params=PARAMS).json()["rates"]
        eurusd = ret["USD"]
        usdeur = 1 / eurusd
        data = {
            "USD:EUR": usdeur,
            "USD:RUB": ret["RUB"] * usdeur,
            "USD:GBP": ret["GBP"] * usdeur,
            "USD:CNY": ret["CNY"] * usdeur,
            "USD:KRW": ret["KRW"] * usdeur,
            "USD:JPY": ret["JPY"] * usdeur,
        }
        data = refine_data(data)
        race_write("fixerio_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("fixerio failed to load")


if __name__ == "__main__":

    fixerio(None)
