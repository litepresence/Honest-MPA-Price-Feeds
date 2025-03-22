"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

use this script to add a price feed publisher
manually update the global variables PRODUCER_ID and ASSET_ID
run the script from terminal where you will add your account name and wif

litepresence2020
"""

# THIRD PARTY MODULES
from getpass import getpass

# HONEST PRICE FEED MODULES
from bitshares_signing import broker
from config_tokens import MPAS, PRODUCER_IDS
from utilities import print_logo, race_read_json

ASSET_IDS = list(MPAS.values())


def add_producer(name, wif):
    """
    update authorized feed producers with broker(order) method
    """
    nodes = [
        "wss://api.bts.mobi/wss",
    ]
    header = {
        "account_name": name,
        "wif": wif,
    }
    edicts = []
    for asset_id in ASSET_IDS:
        edicts.append(
            {
                "op": "add_producer",
                "asset_id": asset_id,
                "producer_ids": PRODUCER_IDS,
            }
        )
    order = {
        "header": header,
        "edicts": edicts,
        "nodes": nodes,
    }
    broker(order, broadcast=True)


def main():
    """
    input name and wif then add a new pricefeed producer
    """
    print("\033c")
    print_logo()
    name = input("\n\nBitshares DEX asset owner account name:\n\n")
    wif = getpass("\n\nBitshares DEX wif:\n\n")
    add_producer(name, wif)


if __name__ == "__main__":
    main()
