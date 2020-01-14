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

URL = "https://apiv2.bitcoinaverage.com/frontend/constants/exchangerates/local"


def ret_headers():

    return {
        "Accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp"
            + ",image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": (
            "driftt_aid=872a5226-7de8-491f-860c-dbc232f057e8; DFTT_END_USER_PREV"
            + "_BOOTSTRAPPED=true; driftt_sid=7fad01bb-4d34-41b5-88e7-982bed7c4fe6"
        ),
        "DNT": "1",
        "Host": "bitcoinaverage.com",
        "If-Modified-Since": "Thu, 19 Dec 2019 09:14:17 GMT",
        "If-None-Match": 'W/"5dfb3f69-d04"',
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            + "like Gecko) Chrome/79.0.3945.79 Safari/537.36 OPR/66.0.3515.27"
        ),
    }


def bitcoinaverage(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        ret = requests.get(URL, timeout=(6, 30)).json()["rates"]
        # print (ret)
        data = {}
        for k, v in ret.items():
            data["USD:" + k] = float(v["rate"])
        data = refine_data(data)
        race_write("bitcoinaverage_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("bitcoinaverage failed to load")
