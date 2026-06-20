"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped with cloudfare nodejs spoofing from 4 sources:

bitcoinaverage, bloomberg, fxcm, fxempire

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps
from json import loads as json_loads

import cfscrape

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import it, race_write, refine_data


def fxempire1(site):
    """
    live forex rates scraped from fxempire.com (backdoor to xignite)
    """
    ret = {}
    try:
        ret.update(fxempire_curr())
    except:
        pass
    try:
        ret.update(fxempire_comm())
    except:
        pass
    return ret


def fxempire_curr():

    base_url = ("https://www.fxempire.com/api/v1/en/currencies/rates",)
    instruments = [
        "usd-eur",
        "usd-gbp",
        "usd-jpy",
        "usd-aud",
        "usd-nzd",
        "usd-cad",
        "usd-chf",
    ]
    params = {
        "category": "",
        "includeSparkLines": "false",
        "includeFullData": "false",
        "instruments": ",".join(i.strip() for i in instruments if i.strip()),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:147.0) Gecko/20100101 Firefox/147.0",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=4",
    }
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    url = f"{base_url}?{query_string}"

    session = requests.Session()
    session.headers = headers
    cfscrape_requests = cfscrape.create_scraper(sess=session)
    response = cfscrape_requests.get(
        url,
        headers=headers,
        timeout=10,
    )
    response.raise_for_status()

    return response


def fxempire_comm():

    url = "https://www.fxempire.com/commodities"
    session = requests.Session()
    session.headers = headers
    cfscrape_requests = cfscrape.create_scraper(sess=session)
    html = cfscrape_requests.get(url)

    result = {}
    h = html.lower()

    # Split into rows
    rows = h.split("<tr")

    for row in rows:
        # Check for XAU symbol
        if 'data-playwright="commodity-symbol">xau</span>' in row:
            if 'data-playwright="commodity-last-price"' in row:
                price_part = row.split('data-playwright="commodity-last-price"')[
                    1
                ].split("</td>")[0]
                price_text = price_part.split(">")[-1].strip()
                if price_text.endswith("k"):
                    price = float(price_text[:-1]) * 1000
                else:
                    price = float(price_text.replace(",", ""))
                result["USD:XAU"] = 1 / price

        # Check for XAG symbol
        elif 'data-playwright="commodity-symbol">xag</span>' in row:
            if 'data-playwright="commodity-last-price"' in row:
                price_part = row.split('data-playwright="commodity-last-price"')[
                    1
                ].split("</td>")[0]
                price_text = price_part.split(">")[-1].strip()
                if price_text.endswith("k"):
                    price = float(price_text[:-1]) * 1000
                else:
                    price = float(price_text.replace(",", ""))
                result["USD:XAG"] = 1 / price

    return result


def fxcm(site):
    """
    live forex rates scraped from fxcm.com
    """
    timestamp = int(time.time() * 1000) - 1000
    url = f"https://ratesjson.fxcm.com/DataDisplayer?t={timestamp}"
    headers = {
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
    try:
        # fails during some hours of day
        session = requests.Session()
        session.headers = headers
        cfscrape_requests = cfscrape.create_scraper(sess=session)
        ret = cfscrape_requests.get(url, timeout=(15, 15)).text
        # print (ret)
        data = (
            ret.replace(" ", "")
            .replace('null({"Rates":', "")
            .replace(",}]});", "}]")
            .replace(",}", "}")
            .replace("});", "")
            .replace("NaN", "null")
        )
        # {"Symbol":"CHFJPY","Bid":"1.1","Ask":"1.2","Spread":"0.1","ProductType":"1",}
        raw = json_loads(data)
        data = {}
        for item in raw:
            symbol = item["Symbol"]
            if symbol.isupper() and (len(symbol) == 6):
                symbol = symbol[:3] + ":" + symbol[-3:]
                data[symbol] = (float(item["Ask"]) + float(item["Bid"])) / 2
        data = refine_data(data)
        print(it("purple", "FOREX CFSCRAPE:"), site, data)
        race_write(f"{site}_forex.txt", json_dumps(data))
    except:
        print(it("purple", "FOREX CFSCRAPE:"), it("red", f"{site} failed to load"))
