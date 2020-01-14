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
from pprint import pprint

URL = "https://duckduckgo.com/js/spice/currency/1/usd/"


def duckduckgo(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        data = {}
        currencies = ["KRW", "JPY", "RUB"]
        # AUD,CAD,COP,EUR,GBP,INR,MXN,MYR,ZAR containted in topConversions by default

        for currency in currencies:
            url = URL + currency
            raw = requests.get(url, timeout=(6, 30)).text
            raw = (
                raw.replace("\n", "")
                .replace(" ", "")
                .replace("ddg_spice_currency(", "")
                .replace(");", "")
            )
            ret = json_loads(raw)
            data["USD:" + currency] = float(ret["conversion"]["converted-amount"])
            time.sleep(1)
            for item in ret["topConversions"]:
                data["USD:" + item["to-currency-symbol"]] = float(
                    item["converted-amount"]
                )

        data = refine_data(data)
        race_write("duckduckgo_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("duckduckgo failed to load")
