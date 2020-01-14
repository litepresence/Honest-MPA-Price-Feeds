# STANDARD PYTHON MODULES
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value

# THIRD PARTY MODULES
import requests
import cfscrape

# PRICE FEED MODULES
from utilities import it, sigfig, from_iso_date, race_write, race_read_json, refine_data

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
        for k, v in ret.items():
            symbol = k[:3] + ":" + k[-3:]
            data[symbol] = float(v["rate"])
        data = refine_data(data)
        race_write("freeforex_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("freeforex failed to load")
