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
]

ASSET_IDS = [
    # "1.3.5641",  # HONEST.CNY
    # "1.3.5649",  # HONEST.USD
    # "1.3.5650",  # HONEST.BTC
    # "1.3.5651",  # HONEST.XAU
    # "1.3.5652",  # HONEST.XAG
    # "1.3.5659",  # HONEST.ETH
    # "1.3.5660",  # HONEST.XRP
    # "1.3.5661",  # HONEST.ETH1
    # "1.3.5662",  # HONEST.XRP1
    # "1.3.6289",  # HONEST.USDSHORT
    # "1.3.6290",  # HONEST.BTCSHORT
    "1.3.6304",  # HONEST.ADA
    "1.3.6305",  # HONEST.DOT
    "1.3.6306",  # HONEST.LTC
    "1.3.6307",  # HONEST.SOL
    "1.3.6308",  # HONEST.XMR
    "1.3.6309",  # HONEST.ATOM
    "1.3.6310",  # HONEST.XLM
    "1.3.6311",  # HONEST.ALGO
    "1.3.6312",  # HONEST.FIL
    "1.3.6313",  # HONEST.EOS
    "1.3.6314",  # HONEST.RUB
    "1.3.6315",  # HONEST.EUR
    "1.3.6316",  # HONEST.GBP
    "1.3.6317",  # HONEST.JPY
    "1.3.6318",  # HONEST.KRW
    "1.3.6319",  # HONEST.ADASHORT
    "1.3.6320",  # HONEST.DOTSHORT
    "1.3.6321",  # HONEST.LTCSHORT
    "1.3.6322",  # HONEST.SOLSHORT
    "1.3.6323",  # HONEST.XMRSHORT
    "1.3.6324",  # HONEST.ATOMSHORT
    "1.3.6325",  # HONEST.XLMSHORT
    "1.3.6326",  # HONEST.ALGOSHORT
    "1.3.6327",  # HONEST.FILSHORT
    "1.3.6328",  # HONEST.EOSSHORT
    "1.3.6329",  # HONEST.RUBSHORT
    "1.3.6330",  # HONEST.EURSHORT
    "1.3.6331",  # HONEST.GBPSHORT
    "1.3.6332",  # HONEST.JPYSHORT
    "1.3.6333",  # HONEST.KRWSHORT
    "1.3.6334",  # HONEST.XRPSHORT
    "1.3.6335",  # HONEST.ETHSHORT
    "1.3.6336",  # HONEST.XAUSHORT
    "1.3.6337",  # HONEST.XAGSHORT
    "1.3.6338",  # HONEST.CNYSHORT
]
# 1.19.43   1.3.5901    HONEST.USDBTSMM
# 1.19.65   1.3.5938    HONEST.BTCUSDMM
# 1.19.66   1.3.5939    HONEST.BTCBTSMM


def add_producer(name, wif):
    """
    update authorized feed producers with broker(order) method
    """
    for asset_id in ASSET_IDS:
        nodes = [
            "wss://api.bts.mobi/wss",
        ]
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
