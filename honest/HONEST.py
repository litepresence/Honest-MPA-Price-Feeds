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
import os
import time
import sys
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
from dex_manual_signing import wss_handshake, wss_query, trace
from dex_manual_signing import broker as broker2
from config_nodes import public_nodes

CER = 1.5  # encourage payment of fees in bts, else 1.5X profit for HONEST producers
MCR = 1400  # min. debt/collateral = 1.4
MSSR = 1100  # liquidate immediately to as low as 1000/1100 = 11.0% below price feed
REFRESH = 2750  # maintain accurate timely price feeds; approximately on 55 min
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
    print(it("yellow", "NODES + PUB_DICT"))
    print(nodes)
    print(pub_dict)

    edicts = []
    # Regular tokens, then shorts.
    for short in ["SHORT", ""]:
        for coin, feed in prices["feed"].items():
            if coin.split(":")[0] != "BTC":
                edict = dict(pub_dict)
                edict["asset_name"] = f"HONEST.{coin.split(':')[1]}{short}"
                edict["settlement_price"] = 1 / feed if short else feed
                edicts.append(edict)
    print("EDICTS BEFORE BTC COLLATERAL")
    print(edicts)

    # these are a little different; they're backed by HONEST.BTC collateral
    # we'll override currency name and add core price
    btceth1 = dict(pub_dict)
    btceth1["asset_name"] = "HONEST.ETH1"
    btceth1["currency_name"] = "HONEST.BTC"
    btceth1["core_price"] = prices["feed"]["BTS:ETH"]
    btceth1["settlement_price"] = prices["feed"]["BTC:ETH"]
    btcxrp1 = dict(pub_dict)
    btcxrp1["asset_name"] = "HONEST.XRP1"
    btcxrp1["currency_name"] = "HONEST.BTC"
    btcxrp1["core_price"] = prices["feed"]["BTS:XRP"]
    btcxrp1["settlement_price"] = prices["feed"]["BTC:XRP"]
    # add each publication edict to the edicts list
    edicts = [*edicts, btceth1, btcxrp1]

    print("EDICTS:\n")
    print(json_dumps(edicts, indent=4))

    # attempt to publish them all at once
    # try:
    #     order = {
    #         "header": header,
    #         "edicts": edicts,
    #         "nodes": nodes,
    #     }
    #     broker(order)
    # # otherwise attempt each mpa indvidually
    # except Exception as error:
    # print(it("red", "FAILED TO PUBLISH ATOMICALLY, FALLING BACK TO INDIVIDUAL"))
    # trace(error)
    for edict in edicts:
        try:
            order = {
                "header": header,
                "edicts": [edict],
                "nodes": nodes,
            }
            broker(order)
        except Exception as error:
            trace(error)


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
    while not dex:
        time.sleep(0.5)
        # Above prevents hard drive strain and allows `pricefeed_dex` to actually start
        dex = race_read_json("pricefeed_dex.txt")
    updates = 1
    while True:
        # print("REDIRECTING STDOUT TO LOG")
        # sys.stdout.close()
        # sys.stdout = open(f"pipe/log{int(time.time())}.txt", "w")
        try:
            # collect forex and cex data
            forex = pricefeed_forex()  # takes about 30 seconds
            cex = pricefeed_cex()  # takes about 30 seconds
            # read the latest dex data
            dex = race_read_json("pricefeed_dex.txt")

            # Get BTS:BTC price for each exchange
            cex_btsbtc_dict = {}
            for exchange, btsusd_price in cex["BTS:USDT"]["data"].items():
                if exchange in cex["BTC:USDT"]["data"]:
                    cex_btsbtc_dict[exchange] = btsusd_price["last"] * (
                        1 / cex["BTC:USDT"]["data"][exchange]["last"]
                    )
            # Remove exchange keys after printing
            cex_btsbtc_list = list(cex_btsbtc_dict.values())

            # attain dex BTS:BTC median
            dex_btsbtc_list = [v for k, v in dex["last"].items() if "BTC" in k]
            dex_btsbtc_dict = {k: v for k, v in dex["last"].items() if "BTC" in k}

            # remove the systemic risk of EOS and XRP leaving the systemic risk of IOB and BTWTY
            # to attain two addional BTS:BTC sources from bitshares pools
            if "IOB.XRP_at_pool" in dex["last"]:
                dex_btsbtc_list.append(
                    dex["last"]["IOB.XRP_at_pool"] * cex["XRP:BTC"]["median"]
                )
                dex_btsbtc_dict["IOB.XRP"] = dex_btsbtc_list[-1]
            if "BTWTY.EOS_at_pool" in dex["last"]:
                dex_btsbtc_list.append(
                    dex["last"]["BTWTY.EOS_at_pool"] * cex["EOS:BTC"]["median"]
                )
                dex_btsbtc_dict["BTWTY.EOS"] = dex_btsbtc_list[-1]

            # finalize btsbtc by taking median of all cex and dex btsbtc prices
            btsbtc = median(dex_btsbtc_list + cex_btsbtc_list)
            race_write(
                doc="bts_btc_pipe.txt",
                text=json_dumps(
                    {
                        k: sigfig(v, 4)
                        for k, v in {**dex_btsbtc_dict, **cex_btsbtc_dict}.items()
                    }
                ),
            )
            # create feed prices for crypto altcoins: LTC, ETH, XRP

            btcusd = cex["BTC:USD"]["median"]
            # create implied bts us dollar price
            btsusd = btsbtc * btcusd

            forexfeedusd = {pair: value[0] for pair, value in forex["medians"].items()}
            print(forexfeedusd)
            forexfeedbts = {
                "BTS:" + pair.split(":")[1]: btsusd * value
                for pair, value in forexfeedusd.items()
            }
            print(forexfeedbts)
            cryptofeedbtc = {
                ":".join(coin.split(":")[::-1]): price["median"]
                for coin, price in cex.items()
                if coin not in ["BTC:USD", "BTS:BTC", "BTS:USDT"]
            }
            print(cryptofeedbtc)
            cryptofeedbts = {
                "BTS:" + pair.split(":")[1]: btsbtc / value
                for pair, value in cryptofeedbtc.items()
            }
            cryptofeedbtc = {
                coin: 1 / value
                for coin, value in cryptofeedbtc.items()
                if coin in ["BTC:XRP", "BTC:ETH"]
            }

            # create implied bts priced in forex terms
            feed = {
                **cryptofeedbtc,
                **cryptofeedbts,
                **forexfeedbts,
                "BTS:USD": btsusd,
                "BTS:BTC": btsbtc,
            }
            feed = {k: sigfig(v) for k, v in feed.items()}
            # forex priced in bts terms; switch symbol and 1/price
            inverse_feed = {f"{k[-3:]}:{k[:3]}": sigfig(1 / v) for k, v in feed.items()}
            # aggregate full price calculation for jsonbin.io
            current_time = {
                "unix": int(time.time()),
                "local": f"{time.ctime()} " + time.strftime("%Z"),
                "utc": f"{time.asctime(time.gmtime())} UTC",
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
                race_write(doc=f"price_log_{time.ctime()}.txt", text=json_dumps(prices))
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

            if not updates % 24:

                sceletus_orders, sceletus_output = sceletus(
                    prices, name, wif, trigger["sceletus"]
                )
                race_append(
                    "sceletus_orders.txt", ("\n\n" + json_dumps(sceletus_orders))
                )
                race_write("sceletus_output.txt", json_dumps(sceletus_output))

            appendage = (
                "\n" + str(int(time.time())) + " " + time.ctime() + " " + str(feed)
            )
            race_append(doc="feed_append.txt", text=appendage)
            updates += 1
            time.sleep(REFRESH)
        except Exception as error:
            print(trace(error))
            time.sleep(10)  # try again in 10 seconds


def main():
    """
    initialize final aggregation and publication event loop
    """
    print("\033c")
    print_logo()
    PATH = f"{str(os.path.dirname(os.path.abspath(__file__)))}/"
    os.makedirs(f"{PATH}pipe", exist_ok=True)
    trigger = {
        "feed": input(
            "\n  to PUBLISH"
            + it("cyan", " y + Enter ")
            + "or Enter to skip\n\n          "
        ).lower()
    }

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
        while True:
            name = input("\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           "))
            try:
                wss_handshake()
                account_name, account_id = wss_query(
                    ["database", "lookup_accounts", [name, 1]]
                )[0]
                if name == account_name:
                    print(f"\nWelcome back account {account_name} with id {account_id}")
                else:
                    raise ValueError("\nInvalid account name, try again...")
            except ValueError as error:
                print(error.args)
                continue
            wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
            order = {
                "edicts": [{"op": "login"}],
                "header": {
                    "asset_id": "1.3.0",
                    "currency_id": "1.3.861",
                    "asset_precision": 5,
                    "currency_precision": 8,
                    "account_id": account_id,
                    "account_name": name,
                    "wif": wif,
                },
                "nodes": public_nodes(),
            }
            if broker2(order):
                print("Authenticated")
                time.sleep(3)
                break
            print("invalid WIF for this account, try again")

    gather_data(name, wif, trigger)


if __name__ == "__main__":

    main()
