# STANDARD PYTHON MODULES
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import it, sigfig, from_iso_date, race_write, race_read_json, refine_data

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
