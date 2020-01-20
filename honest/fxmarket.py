"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

# FX MARKET API
# https://fixer.io/documentation
# https://fxmarketapi.com/apilive?api_key=KEY&currency=EURUSD,GBPUSD
# 1000 / month

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["fxmarket"]
URL = "https://fxmarketapi.com/apilive"
SYMBOLS = "USDEUR,USDGBP,USDCNY,USDKRW,USDRUB,USDJPY"
PARAMS = {"currency": SYMBOLS, "api_key": KEY}


def fxmarket(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, params=PARAMS).json()["price"]
        data = {k.replace("USD", "USD:"): v for k, v in ret.items()}
        data = refine_data(data)
        race_write("fxmarket_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("fxmarket failed to load")


if __name__ == "__main__":

    fxmarket(None)
