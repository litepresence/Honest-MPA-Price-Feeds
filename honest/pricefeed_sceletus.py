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
    # create a connection to a dex node
    storage = {"mean_ping": 1}
    nodes = race_read_json("nodes.txt")
    random.shuffle(nodes)
    # return rpc, handshake_latency, handshake_max
    rpc, _, _ = wss_handshake(storage, nodes[0])
    # make sure its a fast connection, else recursion
    begin = time.time()
    _ = rpc_last(rpc, {"asset": "BTS", "currency": "BTC"})
    if begin - time.time() > 0.4:
        reconnect(rpc)
    return rpc


def create_usd_cny_btc(prices):
    """
    return a dictionary of forex/cex median cross prices for usd cny and btc
    """
    usdcny = prices["forex"]["medians"]["USD:CNY"][0]
    btcusd = prices["cex"]["BTC:USD"]["median"]
    btccny = btcusd * usdcny
    return {
        "USD:CNY": usdcny,
        "CNY:USD": 1 / usdcny,
        "BTC:USD": btcusd,
        "USD:BTC": 1 / btcusd,
        "BTC:CNY": btccny,
        "CNY:BTC": 1 / btccny,
    }


def create_pairs():
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


def market_split(pair):
    """
    sort pair into dict of asset and currency
    """
    asset = pair.split(":")[0]
    currency = pair.split(":")[1]
    bare_asset = asset.replace("HONEST.", "")
    bare_currency = currency.replace("HONEST.", "").replace("GDEX.", "")

    return asset, currency, bare_asset, bare_currency


def sceletus(prices, agents, do_sceletus):
    """
    update the historic chart on the blockchain using buy/sell broker(order) method
    for each pair to be skeleton'd, for each agent on opposing sides of the book
    """
    output = [{}, {}, time.ctime()]
    orders = []
    # calculate skeleton honest-to-honest rates
    usd_cny_btc = create_usd_cny_btc(prices)
    # create a list of all pairs to be skeleton'd
    pairs = create_pairs()
    # websocket handshake
    rpc = reconnect(None)
    # remote procedure price of bts to Bitassets 1.0 (bogus) rates
    bitassets = fetch_bts_bitassets(rpc)
    if do_sceletus:
        for idx, agent in enumerate(agents):
            agents[idx]["id"] = rpc_lookup_accounts(
                rpc, {"account_name": agent["name"]}
            )
    header = {}
    # each agent will place a limit order for each market pair
    for pair in pairs:
        # sort pair into dict of asset and currency
        asset, currency, bare_asset, bare_currency = market_split(pair)
        pair_dict = {
            "asset": asset,
            "currency": currency,
        }
        # make rpc for A.B.C id's and precisions
        (
            asset_id,
            asset_precision,
            currency_id,
            currency_precision,
        ) = rpc_lookup_asset_symbols(
            rpc, pair_dict
        )  # nonetype is not subscriptable???
        # update the header respectively
        header["asset_id"] = asset_id
        header["currency_id"] = currency_id
        header["asset_precision"] = asset_precision
        header["currency_precision"] = currency_precision
        # when BTS is the quote currency, skeleton the inverse feed price
        if currency == "BTS":
            price = float(prices["inverse"][bare_asset + ":" + "BTS"])
        # when HONEST MPA or gateway is currency skeleton the median market rate
        elif currency in ["HONEST.BTC", "HONEST.CNY", "HONEST.USD", "GDEX.BTC"]:
            price = float(usd_cny_btc[bare_asset + ":" + bare_currency])
        # when bitasset is currency skeleton using BTS as the intemediary currency:
        # prce = pricefeed inverse * bitasset rate

        elif currency in ["CNY", "USD", "BTC"]:
            price = float(prices["inverse"][bare_asset + ":" + "BTS"]) * float(
                bitassets["BTS:" + currency]
            )
        # determine a dust size amount for this market pair
        if bare_asset == "BTC":
            amount == 0.00000300
        if bare_asset in ["CNY", "USD"]:
            if currency == "BTS":
                amount = 0.0005
            elif bare_currency == "CNY":
                amount = 0.02
            elif bare_currency == "USD":
                amount = 0.15
            elif bare_currency == "BTC":
                amount = 0.2
        if bare_asset == "USD":
            amount *= 0.15
        # perform buy ops for agents[0] and sell ops for agents[1]
        for idx in range(2):
            header["account_name"] = agents[idx]["name"]
            header["account_id"] = agents[idx]["id"]
            header["wif"] = agents[idx]["wif"]

            operation = "buy"
            if idx:  # idx is zero or one
                operation = "sell"
            # adjust the final price to ensure execution
            price = sigfig(price)
            # build the final edict for this agent*pair
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
            output[idx][pair] = price
            # print the outcome and if not a demo, then live execution
            orders.append(order)
            if do_sceletus:
                broker(order)

    return orders, output


def sceletus_agents():
    """
    select whether to sceletus and input agents name and wif
    """
    # demo or live decision input
    do_sceletus = input(
        "\n  to SCELETUS"
        + it("cyan", " y + Enter ")
        + "or Enter to skip\n\n           "
    ).lower()
    # create a list of two agent dictionaries with name and wif
    agents = []
    agent = {"name": "XXX", "wif": "XXX", "id": "XXX"}
    for idx in range(2):
        side = "BUYING"
        color = "green"
        if idx:
            side = "SELLING"
            color = "red"
        if do_sceletus == "y":
            name = input(
                "\n  Bitshares"
                + it(color, f" SCELETUS {side} ")
                + "agent name:\n\n           "
            )
            wif = getpass(
                "\n  Bitshares"
                + it(color, f" SCELETUS {side} ")
                + "agent wif:\n           "
            )
            print("           *****************")
            agent = {"name": name, "wif": wif}
        agents.append(agent)

    return agents, do_sceletus


if __name__ == "__main__":

    print("see module docstring, launch with pricefeed_final.py")
