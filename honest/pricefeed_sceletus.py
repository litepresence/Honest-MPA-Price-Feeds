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

NOTE: YOU CANNOT RUN THIS AT THE SAME TIME AS pricefeed_final.py in the SAME FOLDER
NOTE: make a full copy of honest folder contents including the pipe folder
NOTE: pricefeed_sceletus.py must have its OWN pipe files

results in the following 18 market pairs to skeleton:

HONEST.BTC:BTC
HONEST.BTC:BTS
HONEST.BTC:CNY
HONEST.BTC:GDEX.BTC
HONEST.BTC:USD
HONEST.CNY:BTC
HONEST.CNY:BTS
HONEST.CNY:CNY
HONEST.CNY:GDEX.BTC
HONEST.CNY:HONEST.BTC
HONEST.CNY:HONEST.USD
HONEST.CNY:USD
HONEST.USD:BTC
HONEST.USD:BTS
HONEST.USD:CNY
HONEST.USD:GDEX.BTC
HONEST.USD:HONEST.BTC
HONEST.USD:USD

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
from utilities import race_write, race_read_json, sigfig
from dex_meta_node import rpc_last, rpc_lookup_asset_symbols, rpc_lookup_accounts
from dex_meta_node import wss_handshake

# ######################################################################################
# ######################################################################################
# USER CONTROLS
# ######################################################################################
# maintain accurate historical chart skeleton
REFRESH = 3600
# draw a price chart in this matrix of market pairs:
CURRENCIES = ["CNY", "USD", "BTS", "BTC", "GDEX.BTC"]
HONEST_ASSETS = ["HONEST.CNY"]  # , "HONEST.USD", "HONEST.BTC"]
HONEST_TO_HONEST = True
# ######################################################################################
# ######################################################################################
BEGIN = int(time.time())  # Intialize runtime count


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
    pairs = []
    for currency in CURRENCIES:
        for asset in HONEST_ASSETS:
            pairs.append(asset + ":" + currency)
    if HONEST_TO_HONEST:
        honest_pairs = [
            i[0] + ":" + i[1] for i in list(itertools.combinations(HONEST_ASSETS, 2))
        ]
        pairs += honest_pairs
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
    output = [{}, {}]
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
        amount = 1 / 10 ** (asset_precision - 2)
        # perform buy ops for agents[0] and sell ops for agents[1]
        for idx in range(2):
            header = {
                "account_name": agents[idx]["name"],
                "account_id": agents[idx]["id"],
                "wif": agents[idx]["wif"],
            }
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
            output[idx][pair] = "%.16f" % price
            # print the outcome and if not a demo, then live execution
            orders.append(order)
            if do_sceletus:
                broker(order)

    race_write("orders.txt", orders)
    race_write("output.txt", output)


def gather_data(agents, do_sceletus):
    """
    primary event loop
    """
    # purge the IPC text pipe
    race_write("pricefeed_final.txt", {})
    race_write("pricefeed_forex.txt", {})
    race_write("pricefeed_cex.txt", {})
    race_write("pricefeed_dex.txt", {})
    race_write("feed.txt", {})
    # begin the dex pricefeed (metanode fork)
    dex_process = Process(target=pricefeed_dex)
    dex_process.daemon = False
    dex_process.start()
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
            # localize cex rates
            btcusd = cex["BTC:USD"]["median"]
            cex_btsbtc = cex["BTS:BTC"]["median"]
            # attain dex BTS:BTC median
            dex_btsbtc = median([v for k, v in dex["last"].items() if "BTC" in k])
            # finalize btsbtc mean by averaging dex and cex rates
            btsbtc = (cex_btsbtc + dex_btsbtc) / 2
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

            sceletus(prices, agents, do_sceletus)
            # update final output on disk
            appendage = (
                "\n" + str(int(time.time())) + " " + time.ctime() + " " + str(prices)
            )
            race_append(doc="feed_append.txt", text=appendage)
            race_write(doc="feed.txt", text=feed)
            race_write(doc="pricefeed_final.txt", text=json_dumps(prices))
            updates += 1
            time.sleep(REFRESH)
        except Exception as error:
            print(trace(error))
            time.sleep(1)  # try again in 10 seconds


def main():
    """
    initialize final aggregation and publication event loop
    """
    # demo or live decision input
    do_sceletus = input(
        "\033c\n\nto skeleton the market 'y + Enter' or Enter to demo\n\n"
    )
    # create a list of two agent dictionaries with name and wif
    agents = []
    for i in range(2):
        agent = {"name": "XXX", "wif": "XXX", "id": "XXX"}
        if do_sceletus == "y":
            name = input(f"\n\nBitshares DEX agent {i} name:\n\n")
            wif = getpass(f"\n\nBitshares DEX agent {i} wif:\n\n")
            agent = {"name": name, "wif": wif}
        agents.append(agent)

    # begin the data collection process
    gather_data(agents, do_sceletus)


if __name__ == "__main__":

    main()
