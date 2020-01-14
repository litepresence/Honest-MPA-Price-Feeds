# STANDARD PYTHON MODULES
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value

# THIRD PARTY MODULES
import requests
import cfscrape
from pprint import pprint

# PRICE FEED MODULES
from utilities import it, sigfig, from_iso_date, race_write, race_read_json, refine_data

URL = "https://api.wsj.net/api/deltoro-mw/marketwatchsite/quote/currency/convert"


def wsj(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        currencies = ["EUR", "CNY", "RUB", "KRW", "JPY"]
        data = {}
        for currency in currencies:
            endpoint = f"?from=USD&to={currency}USD&amount=1.00"
            url = URL + endpoint
            raw = requests.get(url, timeout=(6, 30)).text
            data["USD:" + currency] = float(raw)
            time.sleep(1)

        data = refine_data(data)
        race_write("wsj_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("wsj failed to load")
