"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

OPEN EXCHANGE RATES

https://docs.openexchangerates.org/
https://openexchangerates.org/api/latest.json?app_id=KEY

limit 1000 per month (hourly updates)

litepresence2020
"""

# THIRD PARTY MODULES
import requests
from json import dumps as json_dumps

# HONEST PRICE FEED MODULES
from utilities import refine_data, race_write
from api_keys import api_keys

KEY = api_keys()["openexchangerates"]
URL = "https://openexchangerates.org/api/latest.json"
PARAMS = {"app_id": KEY}
SYMBOLS = ["EUR", "RUB", "GBP", "KRW", "CNY", "JPY"]


def openexchangerates(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, params=PARAMS).json()["rates"]
        data = {}
        for key, val in ret.items():
            if key in SYMBOLS:
                data["USD:" + key] = val

        data = refine_data(data)
        race_write("openexchangerates_forex.txt", json_dumps(data))
        if signal == None:
            print(data)
        signal.value = 1
    except:
        print("openexchangerates failed to load")


if __name__ == "__main__":

    openexchangerates(None)
