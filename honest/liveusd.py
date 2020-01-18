"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from liveusd.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "http://liveusd.com/veri/refresh/total.php"


def liveusd(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, timeout=(6, 30)).text
        ret = ret.replace(" ", "").split("\n")
        data = {}
        for item in ret:
            if item:
                try:
                    pair = item.split(":")[0].replace("USD", "USD:")
                    price = item.split(":")[1]
                    data[pair] = float(price)
                except:
                    pass
        data = refine_data(data)
        race_write("liveusd_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("liveusd failed to load")


if __name__ == "__main__":

    liveusd(None)
