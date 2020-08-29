"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

final aggregation and call to publish feed on chain and at jsonbin.io

litepresence2020
"""

# STANDARD PYTHON MODULES
import time
from statistics import median
from multiprocessing import Process
from json import dumps as json_dumps

# THIRD PARTY MODULES
from getpass import getpass

# ######################################################################################
# ######################################################################################
# YOU ARE OBLIGED AS AN HONEST MPA PRICE FEED PRODUCER
# TO PUBLISH WITH THESE UNALTERED METHODS AND CONSTANTS
# ######################################################################################
from utilities import race_write, race_read_json, sigfig, it
from pricefeed_forex import pricefeed_forex
from pricefeed_cex import pricefeed_cex
from pricefeed_dex import pricefeed_dex, race_append, print_logo
from pricefeed_publish import broker
from pricefeed_sceletus import sceletus
from jsonbin import update_jsonbin
from cancel_all_markets import cancel_all_markets

CER = 1.5  # encourage payment of fees in bts, else 1.5X profit for HONEST producers
MCR = 150  # min declared by FINRA is 125; min recommended by core dev is 160
MSSR = 125  # liquidate default immediately to as low as 100/125 = 20% below market rate
REFRESH = 3100  # maintain accurate timely price feeds
# ######################################################################################
# TRADEMARK HONEST MPA litepresence2020 - BDFL
# ######################################################################################
# ######################################################################################
BEGIN = int(time.time())


def publish_feed(prices, name, wif):
    """
    update the feed price on the blockchain using broker(order) method
    """
    # gather the node list created by dex_process
    nodes = race_read_json("nodes.txt")
    # attach your account name and wif to the header
    header = {
        "account_name": name,
        "wif": wif,
    }
    pub_dict = {
        "op": "publish",
        "CER": CER,
        "MSSR": MSSR,
        "MCR": MCR,
        "currency_name": "BTS",
    }
    # create publication edict for each MPA
    # include standard publication dictionary parameters with unique name and price
    btscny = dict(pub_dict)
    btscny["asset_name"] = "HONEST.CNY"
    btscny["settlement_price"] = prices["feed"]["BTS:CNY"]
    btsusd = dict(pub_dict)
    btsusd["asset_name"] = "HONEST.USD"
    btsusd["settlement_price"] = prices["feed"]["BTS:USD"]
    btsbtc = dict(pub_dict)
    btsbtc["asset_name"] = "HONEST.BTC"
    btsbtc["settlement_price"] = prices["feed"]["BTS:BTC"]
    btsxag = dict(pub_dict)
    btsxag["asset_name"] = "HONEST.XAG"
    btsxag["settlement_price"] = prices["feed"]["BTS:XAG"]
    btsxau = dict(pub_dict)
    btsxau["asset_name"] = "HONEST.XAU"
    btsxau["settlement_price"] = prices["feed"]["BTS:XAU"]
    # btsltc = dict(pub_dict)
    # btsltc["asset_name"] = "HONEST.LTC"
    # btsltc["settlement_price"] = prices["feed"]["BTS:LTC"]
    btseth = dict(pub_dict)
    btseth["asset_name"] = "HONEST.ETH"
    btseth["settlement_price"] = prices["feed"]["BTS:ETH"]
    btsxrp = dict(pub_dict)
    btsxrp["asset_name"] = "HONEST.XRP"
    btsxrp["settlement_price"] = prices["feed"]["BTS:XRP"]
    btseth1 = dict(pub_dict)
    # these are a little different; we'll override currency name and add core price
    btseth1["asset_name"] = "HONEST.ETH1"
    btseth1["currency_name"] = "HONEST.BTC"
    btseth1["core_price"] = prices["feed"]["BTS:ETH"]
    btseth1["settlement_price"] = prices["feed"]["BTC:ETH"]
    btsxrp1 = dict(pub_dict)
    btsxrp1["asset_name"] = "HONEST.XRP1"
    btsxrp1["currency_name"] = "HONEST.BTC"
    btsxrp1["core_price"] = prices["feed"]["BTS:XRP"]
    btsxrp1["settlement_price"] = prices["feed"]["BTC:XRP"]
    # add each publication edict to the edicts list
    edicts = [btscny, btsusd, btsbtc, btsxag, btsxau, btseth, btsxrp, btseth1, btsxrp1]
    # construct and broker() the publication order dictionary
    order = {
        "header": header,
        "edicts": edicts,
        "nodes": nodes,
    }
    broker(order)


def gather_data(name, wif, trigger):
    """
    primary event loop
    """
    # purge the IPC text pipe
    race_write("pricefeed_final.txt", {})
    race_write("pricefeed_forex.txt", {})
    race_write("pricefeed_cex.txt", {})
    race_write("pricefeed_dex.txt", {})
    race_write("sceletus_output.txt", [])
    race_write("honest_cross_rates.txt", {})
    race_write("feed.txt", {})
    # begin the dex pricefeed (metanode fork)
    dex_process = Process(target=pricefeed_dex)
    dex_process.daemon = False
    dex_process.start()
    # dex_process.join(10)
    dex = {}
    # wait until the first dex pricefeed writes to file
    while dex == {}:
        dex = race_read_json("pricefeed_dex.txt")
    updates = 1
    while True:
        try:
            # collect forex and cex data
            forex = pricefeed_forex()  # takes about 30 seconds
            cex = pricefeed_cex()  # takes about 30 seconds
            # read the latest dex data
            dex = race_read_json("pricefeed_dex.txt")
            # localize forex rates
            usdcny = forex["medians"]["USD:CNY"][0]
            # usdeur = forex["medians"]["USD:EUR"][0]
            # usdgbp = forex["medians"]["USD:GBP"][0]
            # usdrub = forex["medians"]["USD:RUB"][0]
            # usdjpy = forex["medians"]["USD:JPY"][0]
            # usdkrw = forex["medians"]["USD:KRW"][0]
            usdxau = forex["medians"]["USD:XAU"][0]
            usdxag = forex["medians"]["USD:XAG"][0]
            # localize cex rates
            btcusd = cex["BTC:USD"]["median"]
            cex_btsbtc = cex["BTS:BTC"]["median"]
            cex_btsbtc_list = []
            for key, val in cex["BTS:BTC"]["data"].items():
                cex_btsbtc_list.append(val["last"])
            # attain dex BTS:BTC median
            dex_btsbtc_list = [v for k, v in dex["last"].items() if "BTC" in k]
            dex_btsbtc = median(dex_btsbtc_list)
            # finalize btsbtc by taking median of all cex and dex btsbtc prices
            btsbtc = median(dex_btsbtc_list + cex_btsbtc_list)
            # create feed prices for crypto altcoins: LTC, ETH, XRP
            # btcltc = 1/cex["LTC:BTC"]["median"]
            btceth = 1 / cex["ETH:BTC"]["median"]
            btcxrp = 1 / cex["XRP:BTC"]["median"]
            # btsltc = btsbtc * btcltc
            btseth = btsbtc * btceth
            btsxrp = btsbtc * btcxrp
            # create implied bts us dollar price
            btsusd = btsbtc * btcusd
            # create implied bts priced in forex terms
            feed = {
                "BTC:ETH": btceth,
                "BTC:XRP": btcxrp,
                "BTS:ETH": btseth,
                "BTS:XRP": btsxrp,
                "BTS:BTC": btsbtc,
                "BTS:USD": btsusd,
                "BTS:CNY": (btsusd * usdcny),
                # "BTS:EUR": (btsusd * usdeur),
                # "BTS:GBP": (btsusd * usdgbp),
                # "BTS:RUB": (btsusd * usdrub),
                # "BTS:JPY": (btsusd * usdjpy),
                # "BTS:KRW": (btsusd * usdkrw),
                "BTS:XAU": (btsusd * usdxau),
                "BTS:XAG": (btsusd * usdxag),
            }
            feed = {k: sigfig(v) for k, v in feed.items()}
            # forex priced in bts terms; switch symbol and 1/price
            inverse_feed = {
                (k[-3:] + ":" + k[:3]): sigfig(1 / v) for k, v in feed.items()
            }
            # aggregate full price calculation for jsonbin.io
            current_time = {
                "unix": int(time.time()),
                "local": time.ctime() + " " + time.strftime("%Z"),
                "utc": time.asctime(time.gmtime()) + " UTC",
                "runtime": int(time.time() - BEGIN),
                "updates": updates,
            }
            prices = {
                "time": current_time,
                "cex": cex,
                "dex": dex,
                "forex": forex,
                "inverse": inverse_feed,
                "feed": feed,
            }
            # update final output on disk
            race_write(doc="feed.txt", text=feed)
            race_write(doc="pricefeed_final.txt", text=json_dumps(prices))
            # publish feed prices to the blockchain
            if trigger["feed"] == "y":
                time.sleep(3)
                print("\n", it("red", "PUBLISHING TO BLOCKCHAIN"))
                time.sleep(5)
                publish_feed(prices, name, wif)
            # upload production data matrix to jsonbin.io
            if trigger["jsonbin"] == "y":
                time.sleep(3)
                print("\n", it("red", "UPLOADING TO JSONBIN"))
                time.sleep(5)
                update_jsonbin(prices)
            # buy/sell reference rates with two accounts
            msg = "DEMO SCELETUS REFERENCE RATES"
            if trigger["sceletus"] == "y":
                if trigger["cancel"] == "y":
                    time.sleep(3)
                    print("\n", it("red", "CANCEL ALL IN ALL MARKETS"))
                    time.sleep(5)
                    cancel_all_markets(name, wif)
                msg = msg.replace("DEMO ", "")
            time.sleep(3)
            print("\n", it("red", msg))
            time.sleep(5)
            sceletus_orders, sceletus_output = sceletus(
                prices, name, wif, trigger["sceletus"]
            )
            race_append("sceletus_orders.txt", ("\n\n" + json_dumps(sceletus_orders)))
            race_write("sceletus_output.txt", json_dumps(sceletus_output))

            appendage = (
                "\n" + str(int(time.time())) + " " + time.ctime() + " " + str(feed)
            )
            race_append(doc="feed_append.txt", text=appendage)
            updates += 1
            time.sleep(REFRESH)
        except Exception as error:
            print(error)
            time.sleep(10)  # try again in 10 seconds


def main():
    """
    initialize final aggregation and publication event loop
    """
    print("\033c")
    print_logo()
    trigger = {}
    trigger["feed"] = input(
        "\n  to PUBLISH" + it("cyan", " y + Enter ") + "or Enter to skip\n\n          "
    ).lower()
    trigger["jsonbin"] = input(
        "\n  to JSONBIN" + it("cyan", " y + Enter ") + "or Enter to skip\n\n          "
    ).lower()
    trigger["sceletus"] = input(
        "\n  to SCELETUS" + it("cyan", " y + Enter ") + "or Enter to skip\n\n          "
    ).lower()
    trigger["cancel"] = input(
        "\n  to CANCEL" + it("cyan", " y + Enter ") + "or Enter to skip\n\n          "
    ).lower()
    wif, name = "", ""
    if trigger["feed"].lower() == "y" or (trigger["sceletus"] == "y"):
        name = input("\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           "))
        wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
        print("           *****************")
    gather_data(name, wif, trigger)


if __name__ == "__main__":

    main()
