import json

import requests
from utilities import it, race_write


def cnbc(site):
    url = "https://quote.cnbc.com/quote-html-webservice/restQuote/symbolType/symbol"
    params = {
        "symbols": "@GC.1|@SI.1|",
        "requestMethod": "itv",
        "noform": "1",
        "partnerId": "2",
        "fund": "1",
        "exthrs": "1",
        "output": "json",
        "events": "1",
    }

    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "en-US,en;q=0.7",
        "cache-control": "max-age=0",
        "cookie": "sess-id=16430086; region=USA; AMCVS_A8AB776A5245B4220A490D44%40AdobeOrg=1; _pctx=%7Bu%7DN4IgrgzgpgThIC4B2YA2qA05owMoBcBDfSREQpAeyRCwgEt8oBJAEzIEYOAWABgA4AzPwBMg7iP68A7LwHSAnCAC%2BQA; _pcid=%7B%22browserId%22%3A%22m8iw9xxn47hvdz28%22%7D; s_getNewRepeat30=1742568473351-New; s_getNewRepeat90=1742568473352-New; s_vmonthnum=1743480000353%26vn%3D1; s_monthinvisit=true; s_lv=1742568473354; s_lv_s=First%20Visit; linktrk=%5B%5BB%5D%5D; s_cc=true; AMCV_A8AB776A5245B4220A490D44%40AdobeOrg=-1124106680%7CMCIDTS%7C20169%7CMCMID%7C29171022591285717033622650769202853971%7CMCAID%7CNONE%7CMCOPTOUT-1742575673s%7CNONE%7CvVersion%7C5.2.0; __tbc=%7Bkpex%7DQloLM19VKNCj940yma8HEpOjas-VDvR3oo8gmFTKl57JsfCktGHQ5oSCzxVt1YIE; __pat=-14400000; __pvi=eyJpZCI6InYtbThpdzl4eTN3bmRxd29tZSIsImRvbWFpbiI6Ii5jbmJjLmNvbSIsInRpbWUiOjE3NDI1Njg0NzMzOTl9; xbc=%7Bkpex%7DZTU0_R6VCJHC5Q3SI_OqZg",
        "priority": "u=0, i",
        "sec-ch-ua": '"Chromium";v="134", "Not:A-Brand";v="24", "Brave";v="134"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "sec-gpc": "1",
        "upgrade-insecure-requests": "1",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
    }

    prices = {}

    try:
        response = requests.get(url, headers=headers, params=params)
        ret = response.json()
        prices["USD:XAU"] = 1/float(
            ret["FormattedQuoteResult"]["FormattedQuote"][0]["last"].replace(",", "")
        )
        prices["USD:XAG"] = 1/float(
            ret["FormattedQuoteResult"]["FormattedQuote"][1]["last"].replace(",", "")
        )

        print(it("purple", "FOREX API:"), site, prices)
        race_write(f"{site}_forex.txt", json.dumps(prices))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))


def arincen(site):
    url = "https://en.arincen.com/markets/commodities"
    result = {}
    try:
        response = requests.get(url, timeout=10)
        ret = response.text.lower()
        ret = ret.split("footer_warning")[2]
        result["USD:XAG"] = 1/float(
            ret.split("xagusd", 1)[1]
            .split("volume&quot")[0]
            .split("last_price&quot;:")[1]
            .split(",&quot;")[0]
        )
        result["USD:XAU"] = 1/float(
            ret.split("xauusd", 1)[1]
            .split("volume&quot")[0]
            .split("last_price&quot;:")[1]
            .split(",&quot;")[0]
        )

        print(it("purple", "FOREX API:"), site, result)
        race_write(f"{site}_forex.txt", json.dumps(result))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))

    return result


def bitpanda(site):
    prices = {}
    grams_to_troy_ounces = 31.1034768
    try:
        url_gold = "https://api.bitpanda.com/v3/ohlc/b86c88d4-efe3-11eb-b56f-0691764446a7/USD/day"
        try:
            response_gold = requests.get(url_gold)
            gold_price_grams = 1/float(
                response_gold.json()["data"][-1]["attributes"]["close"]
            )
            prices["USD:XAU"] = gold_price_grams / grams_to_troy_ounces
        except:
            pass

        url_silver = "https://api.bitpanda.com/v3/ohlc/b86c8c67-efe3-11eb-b56f-0691764446a7/USD/day"

        try:
            response_silver = requests.get(url_silver)
            silver_price_grams = 1/float(
                response_silver.json()["data"][-1]["attributes"]["close"]
            )
            prices["USD:XAG"] = silver_price_grams / grams_to_troy_ounces
        except:
            pass

        if not prices:
            raise

        print(it("purple", "FOREX API:"), site, prices)
        race_write(f"{site}_forex.txt", json.dumps(prices))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))

    return prices


def commoditycom(site):
    prices = {}
    try:
        url = "https://commodity.com/wp-content/plugins/commodity-price-graph/live-prices.php?symbol=XAU/USD"
        try:
            prices["USD:XAU"] = 1/float(requests.get(url).json()["close"])
        except:
            pass

        url = "https://commodity.com/wp-content/plugins/commodity-price-graph/live-prices.php?symbol=XAG/USD"
        try:
            prices["USD:XAG"] = 1/float(requests.get(url).json()["close"])
        except:
            pass

        if not prices:
            raise

        print(it("purple", "FOREX API:"), site, prices)
        race_write(f"{site}_forex.txt", json.dumps(prices))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))

    return prices


def businessinsider(site):
    url = "https://markets.businessinsider.com/commodities?op=1"
    result = {}
    try:
        response = requests.get(url, timeout=10)
        ret = response.text
        ret = ret.split("Precious Metals")[1].split("Energy")[0].split("</tr>")

        result["USD:XAU"] = 1/float(
            ret[1].split('data-animation="">')[1].split("</span>")[0].replace(",", "")
        )
        result["USD:XAG"] = 1/float(
            ret[4].split('data-animation="">')[1].split("</span>")[0].replace(",", "")
        )
        print(it("purple", "FOREX API:"), site, result)
        race_write(f"{site}_forex.txt", json.dumps(result))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))


def mql5(site):
    url = "https://www.mql5.com/en/quotes/metals"
    prices = {}
    try:
        ret = requests.get(url).text
        ret = ret.split('class="nav-cards nav-cards__no-more">')[1]
        ret = ret.split('<div class="nav-card" id="card_XAUEUR">')[0]
        ret = ret.split('"Ask price">')
        prices["USD:XAU"] = 1/float(ret[1].split("</span>")[0])
        prices["USD:XAG"] = 1/float(ret[2].split("</span>")[0])

        print(it("purple", "FOREX API:"), site, prices)
        race_write(f"{site}_forex.txt", json.dumps(prices))
    except:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))
