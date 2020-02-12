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
MCR = 160  # min declared by FINRA is 125; min recommended by core dev is 160
MSSR = 125  # liquidate default immediately to as low as 100/125 = 20% below market rate
REFRESH = 3600  # maintain accurate timely price feeds
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
    }
    # HONEST.CNY publication edict
    btscny = dict(pub_dict)
    btscny["asset_name"] = "HONEST.CNY"
    btscny["settlement_price"] = prices["feed"]["BTS:CNY"]
    # HONEST.USD publication edict
    btsusd = dict(pub_dict)
    btsusd["asset_name"] = "HONEST.USD"
    btsusd["settlement_price"] = prices["feed"]["BTS:USD"]
    # HONEST.BTC publication edict
    btsbtc = dict(pub_dict)
    btsbtc["asset_name"] = "HONEST.BTC"
    btsbtc["settlement_price"] = prices["feed"]["BTS:BTC"]
    # HONEST.XAG publication edict
    btsxag = dict(pub_dict)
    btsxag["asset_name"] = "HONEST.XAG"
    btsxag["settlement_price"] = prices["feed"]["BTS:XAG"]
    # HONEST.XAU publication edict
    btsxau = dict(pub_dict)
    btsxau["asset_name"] = "HONEST.XAU"
    btsxau["settlement_price"] = prices["feed"]["BTS:XAU"]
    # append edicts to the edicts list
    # eventually we will update to: [btscny, btsusd, btsbtc] and beyond...
    edicts = [btscny, btsusd, btsbtc, btsxag, btsxau]
    # build and broker the publication order
    order = {
        "header": header,
        "edicts": edicts,
        "nodes": nodes,
    }
    broker(order)


def gather_data(name, wif, do_feed, do_jsonbin, do_sceletus, do_cancel):
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
            usdeur = forex["medians"]["USD:EUR"][0]
            usdgbp = forex["medians"]["USD:GBP"][0]
            usdrub = forex["medians"]["USD:RUB"][0]
            usdjpy = forex["medians"]["USD:JPY"][0]
            usdkrw = forex["medians"]["USD:KRW"][0]
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

            # finalize btsbtc mean by averaging median dex with median cex rates
            # btsbtc = (median(dex_btsbtc_list) + median(cex_btsbtc_list)) / 2

            # finalize btsbtc by taking median of all cex and dex btsbtc prices 
            btsbtc = median(dex_btsbtc_list + cex_btsbtc_list)
            
            # create implied bts us dollar price
            btsusd = btsbtc * btcusd
            # create implied bts priced in forex terms
            feed = {
                "BTS:BTC": btsbtc,
                "BTS:USD": btsusd,
                "BTS:CNY": (btsusd * usdcny),
                "BTS:EUR": (btsusd * usdeur),
                "BTS:GBP": (btsusd * usdgbp),
                "BTS:RUB": (btsusd * usdrub),
                "BTS:JPY": (btsusd * usdjpy),
                "BTS:KRW": (btsusd * usdkrw),
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
            if do_feed == "y":
                time.sleep(3)
                print("\n", it("red", "PUBLISHING TO BLOCKCHAIN"))
                time.sleep(5)
                publish_feed(prices, name, wif)
            # upload production data matrix to jsonbin.io
            if do_jsonbin == "y":
                time.sleep(3)
                print("\n", it("red", "UPLOADING TO JSONBIN"))
                time.sleep(5)
                update_jsonbin(prices)
            # buy/sell reference rates with two accounts
            msg = "DEMO SCELETUS REFERENCE RATES"
            if do_sceletus == "y":
                if do_cancel == "y":
                    time.sleep(3)
                    print("\n", it("red", "CANCEL ALL IN ALL MARKETS"))
                    time.sleep(5)
                    cancel_all_markets(name, wif)  
                msg = msg.replace("DEMO ", "")
            time.sleep(3)
            print("\n", it("red", msg))
            time.sleep(5)
            sceletus_orders, sceletus_output = sceletus(prices, name, wif, do_sceletus)
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
    do_feed = input(
        "\n  to PUBLISH" + it("cyan", " y + Enter ") + "or Enter to skip\n\n           "
    ).lower()
    do_jsonbin = input(
        "\n  to JSONBIN" + it("cyan", " y + Enter ") + "or Enter to skip\n\n           "
    ).lower()
    do_sceletus = input(
        "\n  to SCELETUS"
        + it("cyan", " y + Enter ")
        + "or Enter to skip\n\n           "
    ).lower()
    do_cancel = input(
        "\n  to CANCEL" + it("cyan", " y + Enter ") + "or Enter to skip\n\n           "
    ).lower()
    wif, name = "", ""
    if do_feed.lower() == "y" or (do_sceletus == "y"):
        name = input("\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           "))
        wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
        print("           *****************")
    gather_data(name, wif, do_feed, do_jsonbin, do_sceletus, do_cancel)


if __name__ == "__main__":

    main()
