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
from pricefeed_publish import broker
from utilities import race_read_json

# ######################################################################################
# USER CONTROL PANEL
# ######################################################################################

PRODUCER_IDS = [
    "1.2.581357",  # user85                    @litepresence.com
    "1.2.420263",  # gabrielv0                 @Don_Gabriel
    "1.2.1060824",  # bitshares-notifications  @murda_ra
    "1.2.1691170",  # bitshares-robot          @AmmarYousef
    "1.2.20638",  # datasecuritynode           @JBahai
]
ASSET_ID = "1.3.5641"  # HONEST.CNY
# ######################################################################################
# FIXME: add method to remove a producer
# FIXME: use ASSET_NAME instead ASSET_ID; add call in pricefeed_publish.py to translate


def add_producer(name, wif):
    """
    update authorized feed producers with broker(order) method
    """
    edicts = []
    nodes = race_read_json("nodes.txt")
    header = {
        "account_name": name,
        "wif": wif,
    }
    edict = {
        "op": "producer",
        "asset_id": ASSET_ID,
        "producer_ids": PRODUCER_IDS,
    }
    order = {
        "header": header,
        "edicts": [edict],
        "nodes": nodes,
    }

    broker(order)


def main():
    """
    input name and wif then add a new pricefeed producer
    """
    name = input("\n\nBitshares DEX asset owner account name:\n\n")
    wif = getpass("\n\nBitshares DEX wif:\n\n")
    add_producer(name, wif)


if __name__ == "__main__":

    main()
