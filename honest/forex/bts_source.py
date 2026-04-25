import json

import requests
from utilities import it, race_write


def cmc(site):
    try:
        url = "https://coinmarketcap.com/currencies/bitshares/"
        ret = requests.get(url).text
        ret = ret.split("The live BitShares price today is $")[1].split("USD")[0]

        data = {"BTS:USD": float(ret.strip())}
        print(it("purple", "FOREX API:"), site, data)
        race_write(f"{site}_forex.txt", json.dumps(data))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))


def cryptocomp(site):
    try:
        url = "https://data-api.cryptocompare.com/index/cc/v1/historical/minutes"
        end = "?market=cadli&instrument=BTS-USD&limit=1&aggregate=5&fill=true&apply_mapping=true&response_format=JSON"
        url += end
        ret = requests.get(url).json()
        ret = float(ret["Data"][-1]["CLOSE"])

        data = {"BTS:USD": ret}

        print(it("purple", "FOREX API:"), site, data)
        race_write(f"{site}_forex.txt", json.dumps(data))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))
