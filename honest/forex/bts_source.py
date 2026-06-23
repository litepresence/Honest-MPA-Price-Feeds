import json
import re

import requests
from utilities import it, race_write


def cmc(site):
    try:
        url = "https://coinmarketcap.com/currencies/bitshares/"
        ret = requests.get(url).text

        # Method 1: Parse from the JSON data embedded in the page
        # Look for the __NEXT_DATA__ script tag which contains all data
        match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', ret, re.DOTALL
        )
        if match:
            try:
                data = json.loads(match.group(1))
                # Navigate to the price in the JSON structure
                price = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("detailRes", {})
                    .get("detail", {})
                    .get("statistics", {})
                    .get("price")
                )
                if price is not None:
                    data_out = {"BTS:USD": float(price)}
                    print(f"FOREX API: {site} {data_out}")
                    race_write(f"{site}_forex.txt", json.dumps(data_out))
                    return
            except (json.JSONDecodeError, TypeError, AttributeError, ValueError):
                pass

        # Method 2: Fallback - Look for price in quotesLatestData
        bts_match = re.search(r'"symbol":"BTS","p":([\d.]+)', ret)
        if bts_match:
            price = float(bts_match.group(1))
            data_out = {"BTS:USD": price}
            print(f"FOREX API: {site} {data_out}")
            race_write(f"{site}_forex.txt", json.dumps(data_out))
            return

        print(f"FOREX API: {site} failed - price not found")

    except Exception as e:
        print(f"FOREX API: {site} failed to load - {str(e)}")


def cryptocomp(site):
    try:
        url = "https://min-api.cryptocompare.com/data/v2/histominute"

        params = {
            "aggregate": "1",
            "e": "CCCAGG",
            "extraParams": "https://www.cryptocompare.com",
            "fsym": "BTS",
            "limit": "1",
            "tryConversion": "false",
            "tsym": "USDT",
        }

        headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9",
            "Origin": "https://www.cryptocompare.com",
            "Referer": "https://www.cryptocompare.com/",
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        price = float(data["Data"]["Data"][-1]["close"])

        result = {"BTS:USD": price}

        print(it("purple", "FOREX API:"), site, result)
        race_write(f"{site}_forex.txt", json.dumps(result))

    except requests.exceptions.RequestException:
        print(it("purple", "FOREX API:"), it("red", f"{site} failed to load"))
    except (KeyError, IndexError, ValueError):
        print(it("purple", "FOREX API:"), it("red", f"{site} invalid response"))
