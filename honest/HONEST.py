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
import json
import os
import sys
import time
from getpass import getpass
from multiprocessing import Process
from statistics import median

# 3RD PARTY MODULES
from bitshares_signing import broker
from bitshares_signing.rpc import (rpc_account_id, rpc_get_objects,
                                   wss_handshake)
# HONEST MODULES
from config_nodes import public_nodes
from pricefeed_cex import pricefeed_cex
from pricefeed_dex import pricefeed_dex
from pricefeed_forex import pricefeed_forex
from proxy_list import ProxyManager
from utilities import (PATH, it, logger, print_logo, race_append,
                       race_read_json, race_write, sigfig, trace)

# ######################################################################################
# ######################################################################################
# YOU ARE OBLIGED AS AN HONEST MPA PRICE FEED PRODUCER
# TO PUBLISH WITH THESE UNALTERED METHODS AND CONSTANTS
# ######################################################################################
CER = 1.5  # encourage payment of fees in bts, else 1.5X profit for HONEST producers
MCR = 1400  # min. debt/collateral = 1.4
MSSR = 1100  # liquidate immediately to as low as 1000/1100 = 11.0% below price feed
REFRESH = 2750  # maintain accurate timely price feeds; approximately on 55 min
# ######################################################################################
# TRADEMARK HONEST MPA litepresence2020 - BDFL
# ######################################################################################
# ######################################################################################
BEGIN = int(time.time())
REDIRECT_TO_LOG = False
BROADCAST = True

def create_btc_collateral_edict(
    pub_dict, prices, asset_name, currency_name, core_price_key, settlement_price_key
):
    """
    Helper function to create an edict for assets backed by HONEST.BTC collateral.
    """
    return {
        **pub_dict,  # Start with the base publication dictionary
        "asset_name": asset_name,
        "currency_name": currency_name,
        "core_price": prices["feed"][core_price_key],
        "settlement_price": prices["feed"][settlement_price_key],
    }


def publish_feed(prices, name, wif):
    """
    Updates the feed prices on the blockchain using the broker(order) method.
    Publishes prices for regular tokens, shorts, and assets backed by HONEST.BTC collateral.
    """
    # Gather the node list created by the pricefeed_dex metanode
    nodes = race_read_json("nodes.txt")

    # Attach account name and WIF to the header
    header = {"account_name": name, "wif": wif}

    # Base publication dictionary with standard parameters
    pub_dict = {
        "op": "publish",
        "CER": CER,
        "MSSR": MSSR,
        "MCR": MCR,
        "currency_name": "BTS",
    }

    # Prepare list of edicts for regular tokens and shorts
    # NOTE to future self: this requires that all honest short tokens end in "SHORT"
    # if we ever had to use "INV" or similar because of symbol length, this would break
    edicts = [
        {
            **pub_dict,
            "asset_name": f"HONEST.{coin.split(':')[1]}{short}",
            "settlement_price": 1 / feed if short else feed,
        }
        for short in ["SHORT", ""]  # Handle both regular and short tokens
        for coin, feed in prices["feed"].items()
        if coin.split(":")[0] != "BTC"
    ]

    print("EDICTS BEFORE BTC COLLATERAL")
    print(edicts)

    # Handle BTC-backed collateral assets (ETH1 and XRP1)
    btc_eth_edicts = [
        create_btc_collateral_edict(
            pub_dict, prices, "HONEST.ETH1", "HONEST.BTC", "BTS:ETH", "BTC:ETH"
        ),
        create_btc_collateral_edict(
            pub_dict, prices, "HONEST.XRP1", "HONEST.BTC", "BTS:XRP", "BTC:XRP"
        ),
    ]

    # Add BTC collateral edicts to the main edicts list
    edicts.extend(btc_eth_edicts)

    print("EDICTS:\n")
    print(json.dumps(edicts, indent=4))

    # Attempt to publish all at once
    try:
        order = {
            "header": header,
            "edicts": edicts,
            "nodes": nodes,
        }
        broker(order, BROADCAST)
    except Exception as error:
        print(it("red", "FAILED TO PUBLISH ATOMICALLY, FALLING BACK TO INDIVIDUAL"))
        trace(error)

        # Attempt to publish each MPA individually if atomic publish fails
        for edict in edicts:
            try:
                order = {
                    "header": header,
                    "edicts": [edict],
                    "nodes": nodes,
                }
                broker(order, BROADCAST)
            except Exception as error:
                trace(error)


def purge_ipc():
    """
    purge the IPC text pipe
    """
    race_write("pricefeed_final.txt", {})
    race_write("pricefeed_forex.txt", {})
    race_write("pricefeed_cex.txt", {})
    race_write("pricefeed_dex.txt", {})
    race_write("bts_btc_pipe.txt", {})
    race_write("honest_cross_rates.txt", {})  # This is only populated, not printed
    race_write("feed.txt", {})


def wait_for_dex():
    """
    wait until the first dex pricefeed writes to file
    """
    dex = {}
    while not dex:
        # Prevent hard drive strain
        time.sleep(0.5)
        dex = race_read_json("pricefeed_dex.txt")
    return dex


def calculate_btsbtc_price(cex, exchange):
    """
    Calculate BTS:BTC price for a given exchange using CEX data.
    """
    btsusd_price = cex["BTS:USDT"]["data"][exchange]
    btcusd_price = cex["BTC:USDT"]["data"][exchange]
    return btsusd_price * (1 / btcusd_price)


def gather_dex_btsbtc(dex, cex):
    """
    Gather BTS:BTC prices from DEX and adjust for systemic risks.
    """
    dex_btsbtc_list = [v for k, v in dex["last"].items() if "BTC" in k]
    dex_btsbtc_dict = {k: v for k, v in dex["last"].items() if "BTC" in k}

    # Remove the systemic risk of EOS and XRP while leaving the systemic risk of IOB and
    # BTWTY to attain two addional BTS:BTC sources from bitshares pools
    for asset in ["IOB.XRP", "BTWTY.EOS"]:
        if asset in dex["last"]:
            price = dex["last"][asset] * cex[f"{asset.split('.')[1]}:BTC"]["median"]
            dex_btsbtc_list.append(price)
            dex_btsbtc_dict[asset] = price

    return dex_btsbtc_list, dex_btsbtc_dict


def process_data(cex, dex, forex):
    btcusd = cex["BTC:USD"]["median"]

    # Get BTS:BTC prices from CEX
    cex_btsbtc_dict = {
        exchange: calculate_btsbtc_price(cex, exchange)
        for exchange in cex["BTS:USDT"]["data"]
        if exchange in cex["BTC:USDT"]["data"]
    }

    agg_btsbtc_dict = {
        source: price / btcusd for price, source in forex["aggregate"]["BTS:USD"]
    }

    # Gather DEX BTS:BTC prices
    dex_btsbtc_list, dex_btsbtc_dict = gather_dex_btsbtc(dex, cex)

    agg_btsbtc_list = list(agg_btsbtc_dict.values())
    cex_btsbtc_list = list(cex_btsbtc_dict.values())

    # Finalize BTS:BTC by taking the median of all prices
    btsbtc = median(dex_btsbtc_list + cex_btsbtc_list + agg_btsbtc_list)
    race_write(
        doc="bts_btc_pipe.txt",
        text=json.dumps(
            {
                k: sigfig(v, 4)
                for k, v in {
                    **dex_btsbtc_dict,
                    **cex_btsbtc_dict,
                    **agg_btsbtc_dict,
                }.items()
            }
        ),
    )

    # Create implied BTS USD price
    btsusd = btsbtc * btcusd
    usdtusd = btcusd / cex["BTC:USDT"]["median"]

    # Prepare forex feeds
    forexfeedusd = {pair: value[0] for pair, value in forex["medians"].items()}
    forexfeedbts = {
        f"BTS:{pair.split(':')[1]}": btsusd * value
        for pair, value in forexfeedusd.items()
    }

    # Prepare crypto feeds
    cryptofeedbtc = {
        ":".join(coin.split(":")[::-1]): price["median"]
        for coin, price in cex.items()
        if coin not in ["BTC:USD", "BTS:BTC", "BTS:USDT"]
    }
    cryptofeedbts = {
        f"BTS:{pair.split(':')[1]}": btsbtc / value
        for pair, value in cryptofeedbtc.items()
    }
    cryptofeedbtc = {
        coin: 1 / value
        for coin, value in cryptofeedbtc.items()
        if coin in ["BTC:XRP", "BTC:ETH"]
    }

    # Create the final feed
    feed = {
        **cryptofeedbtc,
        **cryptofeedbts,
        **forexfeedbts,
        "BTS:USD": btsusd,
        "BTS:BTC": btsbtc,
    }
    feed = {k: sigfig(v) for k, v in feed.items()}

    # Create inverse feed
    inverse_feed = {
        ":".join(k.split(":")[::-1]): sigfig(1 / v) for k, v in feed.items()
    }

    return feed, inverse_feed


def gather_data(name, wif, publish):
    """
    primary event loop
    """
    purge_ipc()
    # begin the dex pricefeed (metanode fork)
    dex_process = Process(target=pricefeed_dex)
    dex_process.start()
    # pause for the dex process the start up
    time.sleep(1)
    updates = 0
    proxy_manager = ProxyManager()
    while True:
        if REDIRECT_TO_LOG:
            # FIXME this leaves a file "dangling" open, probably not the best
            print("REDIRECTING STDOUT TO LOG")
            sys.stdout.close()
            sys.stdout = open(
                os.path.join(PATH, "pipe", f"log{int(time.time())}.txt"), "w"
            )
        try:
            # collect forex and cex data
            forex_proc = Process(target=pricefeed_forex)
            forex_proc.start()
            # FIXME for now this is disabled because the two exchanges that use proxies
            # are disabled.  this needs improvement so requests can actually be made to
            # binance and bybit
            # proxy_manager.get_proxy_list()
            cex = pricefeed_cex(proxy_manager)
            forex_proc.join()
            # pricefeed_dex has been spooling up this whole time
            # but make sure the data is there before grabbing it
            wait_for_dex()
            forex = race_read_json("pricefeed_forex.txt")
            dex = race_read_json("pricefeed_dex.txt")

            feed, inverse_feed = process_data(cex, dex, forex)

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
            race_write(doc="pricefeed_final.txt", text=json.dumps(prices))

            # publish feed prices to the blockchain
            if publish:
                try:
                    race_write(
                        doc=f"price_log_{time.ctime()}.txt", text=json.dumps(prices)
                    )
                    print("\n", it("red", "PUBLISHING TO BLOCKCHAIN"))
                    time.sleep(5)
                    publish_feed(prices, name, wif)
                except Exception as error:
                    msg = trace(error)
                    logger(msg, "publishing")
                    print(msg)
                    time.sleep(10)  # try again in 10 seconds
                    continue
        except Exception as error:
            msg = trace(error)
            logger(msg, "data collection")
            print(msg)
            time.sleep(10)  # try again in 10 seconds
            continue
        print("\n", it("red", "REFERENCE RATES"))
        time.sleep(5)

        race_append(
            doc="feed_append.txt",
            text=f"\n\n\n{int(time.time())} {time.ctime()}\n{feed}",
        )
        updates += 1
        time.sleep(REFRESH)


def authenticate_account():
    """Authenticate user account based on Bitshares agent name and WIF."""
    while True:
        account_name = input(
            "\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           ")
        )
        try:
            rpc = wss_handshake()
            try:
                account_id = rpc_account_id(rpc, account_name)
                name = rpc_get_objects(rpc, account_id)["name"]
                assert name == account_name
            except (IndexError, KeyError, AssertionError):
                raise ValueError("\nInvalid account name, try again...")
        except ValueError as error:
            print(error.args[0])
            continue

        print(f"\nWelcome back account {account_name} with id {account_id}")

        wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
        order = {
            "edicts": [{"op": "login"}],
            "header": {
                "asset_id": "1.3.0",
                "currency_id": "1.3.861",
                "asset_precision": 5,
                "currency_precision": 8,
                "account_id": account_id,
                "account_name": account_name,
                "wif": wif,
            },
            "nodes": public_nodes(),
        }
        if broker(order):
            print("Authenticated")
            time.sleep(3)
            return account_name, wif
        print("Invalid WIF for this account, try again")


def main():
    """
    Initialize final aggregation and publication event loop.
    """
    print("\033c")
    print_logo()

    # create the pipe folder if it does not exist
    os.makedirs(os.path.join(PATH, "pipe"), exist_ok=True)

    # Trigger inputs for various actions
    publish = (
        "y"
        in input(
            f'\n   y + Enter to {it("cyan", "PUBLISH")} or Enter to skip\n\n          '
        ).lower()
    )
    if publish:
        name, wif = authenticate_account()
    else:
        name, wif = "", ""

    # Proceed to gather data
    gather_data(name, wif, publish)


if __name__ == "__main__":
    main()
