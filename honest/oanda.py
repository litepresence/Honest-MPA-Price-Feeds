"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from oanda.com

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

KEY = "aaf6cb4f0ced8a211c2728328597268509ade33040233a11af"
URL = "https://www1.oanda.com/lfr/rates_lrrr?tstamp="


def request_header():
    """
    not strictly necessary... but good practice :D
    """
    return {
        "authority": "www.oanda.com",
        "method": "GET",
        "path": "/jslib/wl/lrrr/liverates.js",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "cookie": "",
        "dnt": "1",
        "referer": "https://www1.oanda.com/currency/live-exchange-rates/",
        "sec-fetch-mode": "no-cors",
        "sec-fetch-site": "same-site",
        "user-agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            + " (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36 OPR/65.0.3467.69"
        ),
    }


def hex_decode(raw):
    """
    encrypted hexidecimal to encrypted latin-1
    """
    return bytes.fromhex("0" + raw if len(raw) % 2 else raw).decode("latin-1")


def rc4(cypher, key):
    """
    decryption of rc4 stream cypher from latin-1
    """
    idx1 = 0
    output = []
    r256 = [*range(256)]
    for idx2 in range(256):
        idx1 = (idx1 + r256[idx2] + ord(cypher[idx2 % len(cypher)])) % 256
        r256[idx2], r256[idx1] = r256[idx1], r256[idx2]
    idx1, idx2 = 0, 0
    for _, char in enumerate(key):
        idx2 = (idx2 + 1) % 256
        idx1 = (idx1 + r256[idx2]) % 256
        r256[idx2], r256[idx1] = r256[idx1], r256[idx2]
        output.append(chr(ord(key[char]) ^ r256[(r256[idx2] + r256[idx1]) % 256]))
    return ("").join(output)


def oanda(signal):
    """
    make external request, decode, decrypt, reformat to dict
    """
    try:
        while True:
            try:
                millies = str(int(round(time.time() * 1000)))
                raw = requests.get(
                    URL + millies, headers=request_header(), timeout=(6, 30)
                ).text
                hex_decoded = hex_decode(raw)
                decrypted = rc4(KEY, hex_decoded)
                break
            except:
                time.sleep(5)
        content = decrypted.split("\n")
        parsed = {
            raw.split("=")[0]: (float(raw.split("=")[1]) + float(raw.split("=")[2])) / 2
            for raw in content
        }
        data = {}
        for pair, price in parsed.items():
            data[pair.replace("/", ":")] = float(price)
        data = refine_data(data)
        race_write("oanda_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("oanda failed to load")


if __name__ == "__main__":

    oanda(None)
