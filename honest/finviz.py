"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from finviz.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "https://finviz.com/api/forex_all.ashx?timeframe=m5"


def finviz(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, timeout=(6, 30)).json()
        data = {}
        data["AUD:USD"] = ret["AUDUSD"]["last"]
        data["EUR:GBP"] = ret["EURGBP"]["last"]
        data["EUR:USD"] = ret["EURUSD"]["last"]
        data["GBP:JPY"] = ret["GBPJPY"]["last"]
        data["GBP:USD"] = ret["GBPUSD"]["last"]
        data["USD:CAD"] = ret["USDCAD"]["last"]
        data["NZD:USD"] = ret["NZDUSD"]["last"]
        data["USD:CHF"] = ret["USDCHF"]["last"]
        data["USD:JPY"] = ret["USDJPY"]["last"]
        data["XAG:USD"] = ret["SI"]["last"]
        data["XAU:USD"] = ret["GC"]["last"]
        data = refine_data(data)
        race_write("finviz_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("finviz failed to load")


if __name__ == "__main__":

    finviz(None)
