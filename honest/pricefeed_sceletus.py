"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

create a skeleton historical chart of reference rates
final aggregation of prices vs a variety of noteworthy dex instruments
RPC places dust sized opposing buy and sell orders using two accounts
leverages the manualsigning.py broker(order) method

this module by pricefeed_final.py

litepresence2020
"""

# STANDARD PYTHON MODULES
import sys

import time
import random
import itertools
from pprint import pprint
from getpass import getpass
from statistics import median
from multiprocessing import Process
from json import dumps as json_dumps

# HONEST PRICE FEEDS MODULES
from dex_manual_signing import broker
from pricefeed_cex import pricefeed_cex
from pricefeed_forex import pricefeed_forex
from pricefeed_dex import pricefeed_dex, race_append, trace
from utilities import race_write, race_read_json, sigfig, it
from dex_meta_node import rpc_last, rpc_lookup_asset_symbols, rpc_lookup_accounts
from dex_meta_node import wss_handshake
from config_sceletus import config_sceletus


def reconnect(rpc):
    """
    create a fresh websocket connection to a random node
    """
    try:
        rpc.close()
    except:
        pass
    while True:
        try:
            # create a connection to a dex node
            storage = {"mean_ping": 1}
            nodes = race_read_json("nodes.txt")
            random.shuffle(nodes)
            # return rpc, handshake_latency, handshake_max
            rpc, _, _ = wss_handshake(storage, nodes[0])
            # make sure its a fast connection, else recursion
            begin = time.time()
            _ = rpc_last(rpc, {"asset": "BTS", "currency": "BTC"})
            break
        except Exception as error:
            print(trace(error))
            pass
    if begin - time.time() > 0.4:
        print(nodes[0], "TOO SLOW")
        reconnect(rpc)
    return rpc


def create_honest_cross_rates(prices):
    """
    return a dictionary of forex/cex median cross prices for usd cny and btc
    """
    usdxau = prices["forex"]["medians"]["USD:XAU"][0]
    usdxag = prices["forex"]["medians"]["USD:XAG"][0]
    usdcny = prices["forex"]["medians"]["USD:CNY"][0]
    btcusd = prices["cex"]["BTC:USD"]["median"]
    ethbtc = prices["cex"]["ETH:BTC"]["median"]
    xrpbtc = prices["cex"]["XRP:BTC"]["median"]
    btccny = btcusd * usdcny
    usdbtc = 1 / btcusd
    cnyusd = 1 / usdcny
    cnybtc = 1 / btccny
    xagusd = 1 / usdxag
    xauusd = 1 / usdxau

    xauxag = xauusd * usdxag
    xaubtc = xauusd * usdbtc
    xagbtc = xagusd * usdbtc
    xaucny = xauusd * usdcny
    xagcny = xagusd * usdcny

    btcxau = 1 / xaubtc
    btcxag = 1 / xagbtc
    cnyxau = 1 / xaucny
    cnyxag = 1 / xagcny
    xagxau = 1 / xauxag

    btceth = 1 / ethbtc
    btcxrp = 1 / xrpbtc

    cnyeth = cnybtc * btceth
    cnyxrp = cnybtc * btcxrp
    usdeth = usdbtc * btceth
    usdxrp = usdbtc * btcxrp
    xageth = xagbtc * btceth
    xagxrp = xagbtc * btcxrp
    xaueth = xaubtc * btceth
    xauxrp = xaubtc * btcxrp

    ethcny = 1 / cnyeth
    ethusd = 1 / usdeth
    ethxag = 1 / xageth
    ethxau = 1 / xaueth
    xrpcny = 1 / cnyxrp
    xrpusd = 1 / usdxrp
    xrpxag = 1 / xagxrp
    xrpxau = 1 / xauxrp

    ethxrp = ethbtc * btcxrp
    xrpeth = 1 / ethxrp

    honest_cross_rates = {
        "CNY:USD": sigfig(cnyusd),
        "CNY:XAG": sigfig(cnyxag),
        "CNY:XAU": sigfig(cnyxau),
        "CNY:BTC": sigfig(cnybtc),
        "CNY:ETH": sigfig(cnyeth),
        "CNY:XRP": sigfig(cnyxrp),
        "USD:CNY": sigfig(usdcny),
        "USD:XAG": sigfig(usdxag),
        "USD:XAU": sigfig(usdxau),
        "USD:BTC": sigfig(usdbtc),
        "USD:ETH": sigfig(usdeth),
        "USD:XRP": sigfig(usdxrp),
        "XAU:CNY": sigfig(xaucny),
        "XAU:USD": sigfig(xauusd),
        "XAU:XAG": sigfig(xauxag),
        "XAU:BTC": sigfig(xaubtc),
        "XAU:ETH": sigfig(xaueth),
        "XAU:XRP": sigfig(xauxrp),
        "XAG:CNY": sigfig(xagcny),
        "XAG:USD": sigfig(xagusd),
        "XAG:XAU": sigfig(xagxau),
        "XAG:BTC": sigfig(xagbtc),
        "XAG:ETH": sigfig(xageth),
        "XAG:XRP": sigfig(xagxrp),
        "BTC:CNY": sigfig(btccny),
        "BTC:USD": sigfig(btcusd),
        "BTC:XAU": sigfig(btcxau),
        "BTC:XAG": sigfig(btcxag),
        "BTC:ETH": sigfig(btceth),
        "BTC:XRP": sigfig(btcxrp),
        "ETH:CNY": sigfig(ethcny),
        "ETH:USD": sigfig(ethusd),
        "ETH:XAU": sigfig(ethxau),
        "ETH:XAG": sigfig(ethxag),
        "ETH:BTC": sigfig(ethbtc),
        "ETH:XRP": sigfig(ethxrp),
        "XRP:CNY": sigfig(xrpcny),
        "XRP:USD": sigfig(xrpusd),
        "XRP:XAU": sigfig(xrpxau),
        "XRP:XAG": sigfig(xrpxag),
        "XRP:ETH": sigfig(xrpeth),
        "XRP:BTC": sigfig(xrpbtc),
    }
    race_write(doc="honest_cross_rates.txt", text=json_dumps(honest_cross_rates))
    return honest_cross_rates


def create_pairs(tick):
    """
    return a list of the markets to skeleton
    use a matrix of CURRENCIES and HONEST_ASSETS
    """
    config = config_sceletus()
    pairs = []
    for currency in config["currencies"]:
        for asset in config["honest_assets"]:
            pairs.append(asset + ":" + currency)
    if config["honest_to_honest"]:
        honest_pairs = [
            i[0] + ":" + i[1]
            for i in list(itertools.combinations(config["honest_assets"], 2))
        ]
        pairs += honest_pairs
    pairs = [i for i in pairs if i not in config["exclude_pairs"]]
    pairs.sort()
    return pairs


def fetch_bts_bitassets(rpc):
    """
    make remote procedure calls for last price for bts:bitasset markets
    """
    bitassets = {
        "BTS:BTC": 0,
        "BTS:USD": 0,
        "BTS:CNY": 0,
    }
    for pair in bitassets.keys():
        pair_dict = {
            "asset": pair.split(":")[0],
            "currency": pair.split(":")[1],
        }
        bitassets[pair] = rpc_last(rpc, pair_dict)
    return bitassets


def create_qty_rate(prices, bitassets):
    """
    QUANTITY GENERALLY:
    CNY, USD are precision 4 :: BTS is precision 5 :: XAG,XAG,BTC are precision 8
    graphene integer currency and asset quanitites must be greater than 300
    to enacts a dust transaction with precision 0.333% or finer:
    pairs ending in BTC assets are all 0.00000300 qty
    pairs ending in XAU assets are all 0.00001800 qty
    pairs ending in XAG assets are all 0.0.0015 qty
    pairs ending in USD and CNY assets are all 0.03 qty, except BTC:CNY 0.2 qty
    pairs ending in BTS require case by case approach
    some additional quirks may become apparent with use

    RATE GENERALLY:  (XYZ:ABC * ABC:JKL) = XYZ:JKL
    """
    # calculate skeleton honest-to-honest rates
    rates = create_honest_cross_rates(prices)
    # 20 HONEST to HONEST
    honest_to_honest = {
        "HONEST.XRP:HONEST.BTC": {"qty": 0.3, "rate": rates["XRP:BTC"]},
        "HONEST.CNY:HONEST.BTC": {"qty": 0.3, "rate": rates["CNY:BTC"]},
        "HONEST.USD:HONEST.BTC": {"qty": 0.03, "rate": rates["USD:BTC"]},
        "HONEST.XAG:HONEST.BTC": {"qty": 0.0003, "rate": rates["XAG:BTC"]},
        "HONEST.ETH:HONEST.BTC": {"qty": 0.00003, "rate": rates["ETH:BTC"]},
        "HONEST.XAU:HONEST.BTC": {"qty": 0.000003, "rate": rates["XAU:BTC"]},
        "HONEST.XRP:HONEST.XAU": {"qty": 0.3, "rate": rates["XRP:XAU"]},
        "HONEST.CNY:HONEST.XAU": {"qty": 0.3, "rate": rates["CNY:XAU"]},
        "HONEST.USD:HONEST.XAU": {"qty": 0.03, "rate": rates["USD:XAU"]},
        "HONEST.XAG:HONEST.XAU": {"qty": 0.0003, "rate": rates["XAG:XAU"]},
        "HONEST.ETH:HONEST.XAU": {"qty": 0.00003, "rate": rates["ETH:XAU"]},
        "HONEST.BTC:HONEST.XAU": {"qty": 0.000003, "rate": rates["BTC:XAU"]},
        "HONEST.XRP:HONEST.XAG": {"qty": 0.3, "rate": rates["XRP:XAG"]},
        "HONEST.CNY:HONEST.XAG": {"qty": 0.3, "rate": rates["CNY:XAG"]},
        "HONEST.USD:HONEST.XAG": {"qty": 0.03, "rate": rates["USD:XAG"]},
        "HONEST.ETH:HONEST.XAG": {"qty": 0.00003, "rate": rates["ETH:XAG"]},
        "HONEST.BTC:HONEST.XAG": {"qty": 0.000003, "rate": rates["BTC:XAG"]},
        "HONEST.XAU:HONEST.XAG": {"qty": 0.000003, "rate": rates["XAU:XAG"]},
        "HONEST.XRP:HONEST.USD": {"qty": 0.3, "rate": rates["XRP:USD"]},
        "HONEST.CNY:HONEST.USD": {"qty": 0.3, "rate": rates["CNY:USD"]},
        "HONEST.XAG:HONEST.USD": {"qty": 0.0003, "rate": rates["XAG:USD"]},
        "HONEST.ETH:HONEST.USD": {"qty": 0.00003, "rate": rates["ETH:USD"]},
        "HONEST.XAU:HONEST.USD": {"qty": 0.000003, "rate": rates["XAU:USD"]},
        "HONEST.BTC:HONEST.USD": {"qty": 0.000003, "rate": rates["BTC:USD"]},
        "HONEST.XRP:HONEST.CNY": {"qty": 0.3, "rate": rates["XRP:CNY"]},
        "HONEST.USD:HONEST.CNY": {"qty": 0.03, "rate": rates["USD:CNY"]},
        "HONEST.XAG:HONEST.CNY": {"qty": 0.0003, "rate": rates["XAG:CNY"]},
        "HONEST.ETH:HONEST.CNY": {"qty": 0.00003, "rate": rates["ETH:CNY"]},
        "HONEST.XAU:HONEST.CNY": {"qty": 0.000003, "rate": rates["XAU:CNY"]},
        "HONEST.BTC:HONEST.CNY": {"qty": 0.000003, "rate": rates["BTC:CNY"]},
        "HONEST.CNY:HONEST.XRP": {"qty": 0.3, "rate": rates["CNY:XRP"]},
        "HONEST.USD:HONEST.XRP": {"qty": 0.03, "rate": rates["USD:XRP"]},
        "HONEST.XAG:HONEST.XRP": {"qty": 0.0003, "rate": rates["XAG:XRP"]},
        "HONEST.ETH:HONEST.XRP": {"qty": 0.00003, "rate": rates["ETH:XRP"]},
        "HONEST.XAU:HONEST.XRP": {"qty": 0.000003, "rate": rates["XAU:XRP"]},
        "HONEST.BTC:HONEST.XRP": {"qty": 0.000003, "rate": rates["BTC:XRP"]},
        "HONEST.CNY:HONEST.ETH": {"qty": 0.3, "rate": rates["CNY:ETH"]},
        "HONEST.XRP:HONEST.ETH": {"qty": 0.3, "rate": rates["XRP:ETH"]},
        "HONEST.USD:HONEST.ETH": {"qty": 0.03, "rate": rates["USD:ETH"]},
        "HONEST.XAG:HONEST.ETH": {"qty": 0.0003, "rate": rates["XAG:ETH"]},
        "HONEST.XAU:HONEST.ETH": {"qty": 0.000003, "rate": rates["XAU:ETH"]},
        "HONEST.BTC:HONEST.ETH": {"qty": 0.000003, "rate": rates["BTC:ETH"]},
    }
    # 5 HONEST TO BTS
    honest_to_bts = {
        "HONEST.XRP:BTS": {"qty": 0.3, "rate": prices["inverse"]["XRP:BTS"]},
        "HONEST.CNY:BTS": {"qty": 0.3, "rate": prices["inverse"]["CNY:BTS"]},
        "HONEST.USD:BTS": {"qty": 0.03, "rate": prices["inverse"]["USD:BTS"]},
        "HONEST.XAG:BTS": {"qty": 0.0003, "rate": prices["inverse"]["XAG:BTS"]},
        "HONEST.ETH:BTS": {"qty": 0.00003, "rate": prices["inverse"]["ETH:BTS"]},
        "HONEST.XAU:BTS": {"qty": 0.000003, "rate": prices["inverse"]["XAU:BTS"]},
        "HONEST.BTC:BTS": {"qty": 0.000003, "rate": prices["inverse"]["BTC:BTS"]},
    }
    # 5 HONEST TO GATEWAY BTC
    hcnygbtc = float(prices["inverse"]["CNY:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    husdgbtc = float(prices["inverse"]["USD:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    hxaggbtc = float(prices["inverse"]["XAG:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    hxaugbtc = float(prices["inverse"]["XAU:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    hbtcgbtc = float(prices["inverse"]["BTC:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    hxrpgbtc = float(prices["inverse"]["XRP:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    hethgbtc = float(prices["inverse"]["ETH:BTS"]) * float(
        prices["dex"]["last"]["GDEX.BTC"]
    )
    honest_to_gdexbtc = {
        "HONEST.CNY:GDEX.BTC": {"qty": 0.3, "rate": hcnygbtc},
        "HONEST.USD:GDEX.BTC": {"qty": 0.03, "rate": husdgbtc},
        "HONEST.XAG:GDEX.BTC": {"qty": 0.003, "rate": hxaggbtc},
        "HONEST.XAU:GDEX.BTC": {"qty": 0.000003, "rate": hxaugbtc},
        "HONEST.BTC:GDEX.BTC": {"qty": 0.000003, "rate": hbtcgbtc},
        "HONEST.ETH:GDEX.BTC": {"qty": 0.00003, "rate": hethgbtc},
        "HONEST.XRP:GDEX.BTC": {"qty": 0.3, "rate": hxrpgbtc},
    }
    # 15 HONEST to BITASSETS: CNY, USD, BTC
    hcnycny = float(prices["inverse"]["CNY:BTS"]) * float(bitassets["BTS:CNY"])
    husdcny = float(prices["inverse"]["USD:BTS"]) * float(bitassets["BTS:CNY"])
    hxagcny = float(prices["inverse"]["XAG:BTS"]) * float(bitassets["BTS:CNY"])
    hxaucny = float(prices["inverse"]["XAU:BTS"]) * float(bitassets["BTS:CNY"])
    hbtccny = float(prices["inverse"]["BTC:BTS"]) * float(bitassets["BTS:CNY"])
    hethcny = float(prices["inverse"]["ETH:BTS"]) * float(bitassets["BTS:CNY"])
    hxrpcny = float(prices["inverse"]["XRP:BTS"]) * float(bitassets["BTS:CNY"])

    hcnyusd = float(prices["inverse"]["CNY:BTS"]) * float(bitassets["BTS:USD"])
    husdusd = float(prices["inverse"]["USD:BTS"]) * float(bitassets["BTS:USD"])
    hxagusd = float(prices["inverse"]["XAG:BTS"]) * float(bitassets["BTS:USD"])
    hxauusd = float(prices["inverse"]["XAU:BTS"]) * float(bitassets["BTS:USD"])
    hbtcusd = float(prices["inverse"]["BTC:BTS"]) * float(bitassets["BTS:USD"])
    hethusd = float(prices["inverse"]["ETH:BTS"]) * float(bitassets["BTS:USD"])
    hxrpusd = float(prices["inverse"]["XRP:BTS"]) * float(bitassets["BTS:USD"])

    hcnybtc = float(prices["inverse"]["CNY:BTS"]) * float(bitassets["BTS:BTC"])
    husdbtc = float(prices["inverse"]["USD:BTS"]) * float(bitassets["BTS:BTC"])
    hxagbtc = float(prices["inverse"]["XAG:BTS"]) * float(bitassets["BTS:BTC"])
    hxaubtc = float(prices["inverse"]["XAU:BTS"]) * float(bitassets["BTS:BTC"])
    hbtcbtc = float(prices["inverse"]["BTC:BTS"]) * float(bitassets["BTS:BTC"])
    hethbtc = float(prices["inverse"]["ETH:BTS"]) * float(bitassets["BTS:BTC"])
    hxrpbtc = float(prices["inverse"]["XRP:BTS"]) * float(bitassets["BTS:BTC"])

    honest_to_bitcny = {
        "HONEST.CNY:CNY": {"qty": 0.3, "rate": hcnycny},
        "HONEST.USD:CNY": {"qty": 0.03, "rate": husdcny},
        "HONEST.XAG:CNY": {"qty": 0.003, "rate": hxagcny},
        "HONEST.XAU:CNY": {"qty": 0.000003, "rate": hxaucny},
        "HONEST.BTC:CNY": {"qty": 0.000003, "rate": hbtccny},
        "HONEST.ETH:CNY": {"qty": 0.00003, "rate": hethcny},
        "HONEST.XRP:CNY": {"qty": 0.3, "rate": hxrpcny},
    }
    honest_to_bitusd = {
        "HONEST.CNY:USD": {"qty": 0.3, "rate": hcnyusd},
        "HONEST.USD:USD": {"qty": 0.03, "rate": husdusd},
        "HONEST.XAG:USD": {"qty": 0.003, "rate": hxagusd},
        "HONEST.XAU:USD": {"qty": 0.00003, "rate": hxauusd},
        "HONEST.BTC:USD": {"qty": 0.00003, "rate": hbtcusd},
        "HONEST.ETH:USD": {"qty": 0.00003, "rate": hethusd},
        "HONEST.XRP:USD": {"qty": 0.3, "rate": hxrpusd},
    }
    honest_to_bitbtc = {
        "HONEST.CNY:BTC": {"qty": 0.3, "rate": hcnybtc},
        "HONEST.USD:BTC": {"qty": 0.03, "rate": husdbtc},
        "HONEST.XAG:BTC": {"qty": 0.003, "rate": hxagbtc},
        "HONEST.XAU:BTC": {"qty": 0.000003, "rate": hxaubtc},
        "HONEST.BTC:BTC": {"qty": 0.000003, "rate": hbtcbtc},
        "HONEST.ETH:BTC": {"qty": 0.00003, "rate": hethbtc},
        "HONEST.XRP:BTC": {"qty": 0.3, "rate": hxrpbtc},
    }
    qty_rate = {}
    qty_rate.update(honest_to_bts)
    qty_rate.update(honest_to_bitcny)
    qty_rate.update(honest_to_bitusd)
    qty_rate.update(honest_to_bitbtc)
    qty_rate.update(honest_to_gdexbtc)
    qty_rate.update(honest_to_honest)

    qty_rate = {
        k: {k2: sigfig(v2) for k2, v2 in v.items()} for k, v in qty_rate.items()
    }

    # repackage dict to handle XRP1 and ETH1 as well
    qty_rate2 = {}
    for key, val in qty_rate.items():
        # include all standard standard variants
        qty_rate2[key] = val
        # handle the ETH1 variants
        if "ETH" in key:
            qty_rate2[key.replace("ETH", "ETH1")] = val
        # handle the XRP1 variants
        if "XRP" in key:
            qty_rate2[key.replace("XRP", "XRP1")] = val
        # handle the ETH1 to XRP1 crossrate and vice versa
        if ("ETH" in key) and ("XRP" in key):
            qty_rate2[key.replace("XRP", "XRP1").replace("ETH", "ETH1")] = val

    return qty_rate2


def sceletus(prices, name, wif, do_sceletus):
    """
    update the historic chart on the blockchain using buy/sell broker(order) method
    for each pair to be skeleton'd, for each agent on opposing sides of the book
    """
    orders = []
    order_dict = {}
    header = {}
    tick = prices["time"]["updates"]
    # create a list of all pairs to be skeleton'd
    pairs = create_pairs(tick)
    # websocket handshake
    rpc = reconnect(None)
    # remote procedure price of bts to Bitassets rates
    bitassets = fetch_bts_bitassets(rpc)
    account_id = ""
    if do_sceletus:
        account_id = rpc_lookup_accounts(rpc, {"account_name": name})
    # build qty_rate dict
    qty_rate = create_qty_rate(prices, bitassets)

    # each agent will place a limit order for each market pair
    for pair in pairs:
        amount = sigfig(qty_rate[pair]["qty"])
        price = sigfig(qty_rate[pair]["rate"])
        order_dict[pair] = [amount, price]
        # sort pair into dict of asset and currency
        asset = pair.split(":")[0]
        currency = pair.split(":")[1]
        pair_dict = {
            "asset": asset,
            "currency": currency,
        }
        # flash the curreny pair being bought/sold
        msg = "\033c\n\n\n"
        msg += it("red", "SCELETUS")
        msg += "\n\n\n"
        for i in range(50):
            msg += (
                "\n       "
                + asset
                + "  :  "
                + currency
                + "   @   "
                + it("cyan", price)
                + "   qty   "
                + it("yellow", amount)
            )
        print(msg)
        # make rpc for A.B.C id's and precisions
        (
            asset_id,
            asset_precision,
            currency_id,
            currency_precision,
        ) = rpc_lookup_asset_symbols(rpc, pair_dict)
        # update the header respectively
        header["asset_id"] = asset_id
        header["currency_id"] = currency_id
        header["asset_precision"] = asset_precision
        header["currency_precision"] = currency_precision
        # perform buy ops for agents[0] and sell ops for agents[1]
        for idx in range(2):
            # build the header with correct account info
            header["account_name"] = name
            header["account_id"] = account_id
            header["wif"] = wif
            operation = ["buy", "sell"][idx]
            # build the final edict for this agent*pair with operation and qty_rate
            edict = {
                "op": operation,
                "amount": amount,
                "price": price,
                "expiration": 0,
            }
            # fetch the nodes list and shuffle
            nodes = race_read_json("nodes.txt")
            random.shuffle(nodes)
            # build the order with agent appropriate header and edict for this pair
            order = {
                "header": header,
                "edicts": [edict],
                "nodes": nodes,
            }
            # print the outcome and if not a demo, then live execution
            orders.append(
                {
                    "time": time.ctime(),
                    "unix": int(time.time()),
                    "tick": tick,
                    "name": name,
                    "op": operation,
                    "pair": pair,
                    "price": price,
                    "amount": amount,
                }
            )

            if do_sceletus:
                broker(order)

    return orders, order_dict


if __name__ == "__main__":

    print(create_pairs())
    print("see module docstring, launch with pricefeed_final.py")
