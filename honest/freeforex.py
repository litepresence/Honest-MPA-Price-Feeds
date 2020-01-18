"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from freeforexapi.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://www.freeforexapi.com/api/live?pairs="
CURR = "EURUSD,EURGBP,GBPUSD,USDJPY,AUDUSD,USDCHF,NZDUSD,USDCAD,USDZAR"
URL += CURR


def freeforex(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, timeout=(6, 30)).json()["rates"]
        data = {}
        for key, val in ret.items():
            symbol = key[:3] + ":" + key[-3:]
            data[symbol] = float(val["rate"])
        data = refine_data(data)
        race_write("freeforex_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("freeforex failed to load")


if __name__ == "__main__":

    freeforex(None)
