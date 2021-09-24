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

PRODUCER_IDS = [  # BITSHARES NAME             # TELEGRAM           # ASSOCIATION
    "1.2.581357",  # user85                    @litepresence        litepresence.com
    "1.2.420263",  # gabrielv0                 @Don_Gabriel         dexbot.info
    "1.2.1691170",  # bitshares-robot          @AmmarYousef         iobanker.com
    "1.2.20638",  # datasecuritynode           @JBahai              peerplays.com
    "1.2.1790240",  # piga-mifupa              @christophersanborn  bitshares-core
    "1.2.35770",  # teiva                      @Teiva
    #"1.2.390320",  # agorise                  @KenCode             palmpay.io
    #"1.2.1060824",  # bitshares-notifications @murda_ra            bitshares.org
]

ASSET_IDS = [
    "1.3.5641",  # HONEST.CNY
    "1.3.5649",  # HONEST.USD
    "1.3.5650",  # HONEST.BTC
    "1.3.5651",  # HONEST.XAU
    "1.3.5652",  # HONEST.XAG
    "1.3.5659",  # HONEST.ETH
    "1.3.5660",  # HONEST.XRP
    "1.3.5661",  # HONEST.ETH1
    "1.3.5662",  # HONEST.XRP1
]
# 1.19.43   1.3.5901    HONEST.USDBTSMM
# 1.19.65   1.3.5938    HONEST.BTCUSDMM
# 1.19.66   1.3.5939    HONEST.BTCBTSMM

def add_producer(name, wif):
    """
    update authorized feed producers with broker(order) method
    """
    for asset_id in ASSET_IDS:
        nodes = race_read_json("nodes.txt")
        header = {
            "account_name": name,
            "wif": wif,
        }
        edict = {
            "op": "producer",
            "asset_id": asset_id,
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
