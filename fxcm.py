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

ATTEMPTS = 1
TIMEOUT = 60
BEGIN = time.time()


def ret_headers():
    return {
        "authority": "www.fxcm.com",
        "method": "GET",
        "path": "/api/v1/en/markets/list",
        "scheme": "https",
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,"
            + "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "max-age=0",
        "dnt": "1",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, "
            + "like Gecko) Chrome/79.0.3945.79 Safari/537.36 OPR/66.0.3515.27"
        ),
    }


def fxcm(signal):
    try:
        # fails during some hours of day
        timestamp = int(time.time() * 1000) - 1000
        uri = f"https://ratesjson.fxcm.com/DataDisplayer?t={timestamp}"
        session = requests.Session()
        session.headers = ret_headers()
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(uri, timeout=(6, 30)).text
        # print (ret)
        data = (
            ret.replace(" ", "")
            .replace('null({"Rates":', "")
            .replace(",}]});", "}]")
            .replace(",}", "}")
        )
        # print(data)
        # {"Symbol":"CHFJPY","Bid":"112.536","Ask":"112.542","Spread":"0.60","ProductType":"1",}
        raw = json_loads(data)
        data = {}
        for item in raw:
            symbol = item["Symbol"]
            if symbol.isupper() and (len(symbol) == 6):
                symbol = symbol[:3] + ":" + symbol[-3:]
                data[symbol] = (float(item["Ask"]) + float(item["Bid"])) / 2
        data = refine_data(data)
        # inter process communication via txt
        race_write("fxcm_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("fxcm failed to load")
