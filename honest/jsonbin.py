"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

called by pricefeed_final.py to upload data matrix for HONEST MPA's to jsonbin.io

if you run this script solo it will create a new jsonbin the bin id

to view your jsonbin, visit:

https://api.jsonbin.io/b/<<< your bin id >>>/latest

litepresence2020
"""

import time

# STANDARD PYTHON MODULES
from multiprocessing import Process, Value

# THIRD PARTY MODULES
import requests

# HONEST PRICE FEED MODULES
from config_apikeys import config_apikeys

# GLOBAL USER DEFINED CONSTANTS
# get secret by creating account at jsonbin.io website
JSONBIN_SECRET = config_apikeys()["jsonbin"]["key"]
# get bin id by running this script
BIN_ID = config_apikeys()["jsonbin"]["id"]
# tag your bin, relevent to managing the jsonbin.io UI, must be ALL_CAPS_UNDERSCORES
BIN_NAME = "HONEST_MPA"
# These settings work... don't touch
ATTEMPTS = 3
TIMEOUT = 20


def create_jsonbin():
    """
    initialize a new jsonbin, logs the bin_id to terminal
    """
    url = "https://api.jsonbin.io/b"
    headers = {
        "Content-Type": "application/json",
        "secret-key": JSONBIN_SECRET,
        "name": BIN_NAME,
        "private": "false",
    }
    data = {"initialize": ""}
    method = "POST"
    execute_request(url, data, headers, method)


def update_jsonbin(data):
    """
    used by pricefeed_final to keep HONEST data matrix available live
    """
    url = f"https://api.jsonbin.io/b/{BIN_ID}"
    headers = {
        "Content-Type": "application/json",
        "secret-key": JSONBIN_SECRET,
        "versioning": "false",
    }
    method = "PUT"
    execute_request(url, data, headers, method)


def post_request(signal, url, data, headers, method):
    """
    perform the actual external request and print results
    """
    if method == "PUT":
        req = requests.put(url, json=data, headers=headers)
    elif method == "POST":
        req = requests.post(url, json=data, headers=headers)
    print(url, data, headers)
    print("\n", "jsonbin.io response:", "\n", req.text, "\n")
    signal.value = 1


def execute_request(url, data, headers, method):
    """
    multiprocess wrap, join, and timeout external request for durability
    """
    signal = Value("i", 0)
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        i += 1
        print("")
        print("jsonbin.io authentication attempt:", i, time.ctime())
        child = Process(target=post_request, args=(signal, url, data, headers, method))
        child.daemon = False
        child.start()
        child.join(TIMEOUT)
        child.terminate()
        time.sleep(1)


def main():
    """
    if you run this script solo it will create a new jsonbin bin_id
    """
    create_jsonbin()


if __name__ == "__main__":
    main()
