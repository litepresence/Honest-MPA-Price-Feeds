"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

RUDEX, XBTSX, and DEEX GATEWAY SCELETUS OPS

litepresence2020
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-statements, too-many-locals, too-many-branches
# pylint: disable=too-many-arguments, broad-except, bare-except, invalid-name
# pylint: disable=too-many-nested-blocks, bad-continuation, bad-whitespace
# pylint: disable=too-many-lines, consider-iterating-dictionary

# STANDARD MODULES
import os
import time
from multiprocessing import Process
from statistics import median
from random import shuffle
from getpass import getpass

# PROPRIETARY MODULES
from utilities import race_write, race_read_json, it, sigfig
from pricefeed_dex import print_logo
from pricefeed_cex import fetch
from pricefeed_sceletus import reconnect
from dex_manual_signing import broker
from dex_meta_node import rpc_lookup_asset_symbols, rpc_lookup_accounts, rpc_last
from forex_scrape import liveusd, freeforex, yahoo, wsj
from forex_scrape import reuters, duckduckgo, wocu, oanda, aastock, fxempire2, ino
from forex_scrape import fxrate, forextime, currencyme, forexrates, exchangeratewidget
from forex_cfscrape import bloomberg, fxcm, fxempire1, investing
from cancel_all_markets import cancel_all_markets, wss_query

# GLOBAL CONSTANTS
TIMEOUT = 10
ATTEMPTS = 10
REFRESH = 3600
DETAIL = False
BEGIN = int(time.time())
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def rpc_open_orders(rpc, account_name):
    """
    return a list of open orders, for one account, in ALL MARKETS
    """
    ret = wss_query(rpc, ["database", "get_full_accounts", [[account_name], "false"]])
    try:
        limit_orders = ret[0][1]["limit_orders"]
    except:
        limit_orders = []
    orders = []
    for order in limit_orders:
        print(order)


def create_prices(cex, dex, forex):
    """
    extract pertinent median prices from cex and forex dictionaries
    """
    prices = {}
    for key, val in cex.items():
        if ":" in key:
            prices[key] = val["median"]
    for key, val in forex["medians"].items():
        if key in ["USD:CNY", "USD:EUR"]:
            prices[key] = val[0]
    for key, val in dex.items():
        prices[key] = val

    return prices


def true_dex_last(pair):
    """
    ensure 3 consecutive requests to random nodes return same response
    """
    rpc = reconnect(None)
    lasts = []
    while True:
        try:
            last = sigfig(float(rpc_last(rpc, pair)))
        except:
            continue
        lasts.append(last)
        lasts = lasts[-3:]
        print(pair, lasts)
        if (len(lasts) == 3) and (len(list(set(lasts))) == 1):
            break
        rpc = reconnect(rpc)
    try:
        rpc.close()
    except:
        pass

    return last


def dex_rates(gateway):
    """
    fetch gateway specific pairs from the dex
    """
    while True:
        try:
            prices = {}
            if gateway == "DEEX":
                prices["DEEX:BTS"] = true_dex_last({"asset": "DEEX", "currency": "BTS"})
            if gateway == "XBTSX":
                prices["STH:BTS"] = true_dex_last(
                    {"asset": "XBTSX.STH", "currency": "BTS"}
                )
                prices["BTS:XBTSX.BTC"] = true_dex_last(
                    {"asset": "BTS", "currency": "XBTSX.BTC"}
                )
            if gateway == "RUDEX":
                prices["BTS:RUDEX.BTC"] = true_dex_last(
                    {"asset": "BTS", "currency": "RUDEX.BTC"}
                )
            break
        except:
            continue

    return prices


def cex_rates(gateway):
    """
    create a cex price feed, write it to disk, and return it
    """
    api = {}
    cex = {}
    api["pair"] = "BTC:USD"
    exchanges = [
        "bittrex",
        "bitfinex",
        "coinbase",
        "kraken",
        "bitstamp",
    ]
    cex[api["pair"]] = fetch(exchanges, api)
    assets = select_assets(gateway)
    for asset in assets:
        api["pair"] = asset + ":BTC"
        exchanges = select_exchanges(asset)
        cex[api["pair"]] = fetch(exchanges, api)

    return cex


def forex_rates():
    """
    sort and aggregate data from external sources
    calculate medians
    """
    sources = refresh_forex_rates()
    aggregate = {}
    for source, prices in sources.items():
        for pair, price in prices.items():
            if pair in aggregate.keys():
                aggregate[pair].append((price, source))
            else:
                aggregate[pair] = [(price, source)]
    medians = {
        k: (
            sigfig(median([i[0] for i in v])),
            len([i[0] for i in v]),
            [i[1] for i in v],
        )
        for k, v in aggregate.items()
    }
    return {
        "sources": sources,
        "aggregate": aggregate,
        "medians": medians,
    }


def refresh_forex_rates():
    """
    make process wrapped external calls; IPC via text pipe
    """
    methods = [
        aastock,  # DARKWEB API; MORNINGSTAR (GOOGLE FINANCE) BACKDOOR
        bloomberg,  # MAY ADD CAPTCHA; HEADER REQUIRED; CLOUDFARE SPOOFING
        currencyme,  # DARKWEB API
        duckduckgo,  # XML SCRAPING, XE BACKDOOR
        exchangeratewidget,  # XML SCRAPING
        forexrates,  # XML SCRAPING
        forextime,  # DARKWEB API
        freeforex,  # FREE API
        fxcm,  # CLOUDFARE SPOOFING; HEADER REQUIRED; ALMOST JSON RESPONSE
        fxempire1,  # XIGNITE BACKDOOR; HEADER REQUIRED; CLOUDFARE SPOOFING
        fxempire2,  # TRADINGVIEW BACKDOOR
        fxrate,  # XML SCRAPING
        ino,  # DARKWEB API
        investing,  # CLOUDFARE SPOOFING, XML SCRAPING
        liveusd,  # DARKWEB API
        oanda,  # DARKWEB API; RC4 ECRYPTION OF LATIN ENCODING
        reuters,  # REFINITIV BACKDOOR, DARKWEB API
        wocu,  # XML SCRAPING
        wsj,  # MARKETWATCH BACKDOOR, DARKWEB API
        yahoo,  # YAHOO FINANCE V7 DARKWEB API
    ]
    # initialize each external call method as a process
    processes = {}
    for method in methods:
        site = method.__name__
        race_write(f"{site}_forex.txt", {})
        processes[site] = Process(target=method, args=(site,))
        processes[site].daemon = False
        processes[site].start()
    for site in processes.keys():
        processes[site].join(TIMEOUT)
    for site in processes.keys():
        processes[site].terminate()
    # read the text pipe ipc results of each process
    sources = {}
    for site in processes.keys():
        sources[site] = race_read_json(f"{site}_forex.txt")
    return sources


def deex_qty_rate(prices):
    """
    build a qty_rate dictionary for deex
    """
    qty_rate = {}
    btcusd = prices["BTC:USD"]
    usdbtc = 1 / btcusd
    usdcny = prices["USD:CNY"]
    cnyusd = 1 / usdcny
    deexbts = prices["DEEX:BTS"]
    btsbtc = prices["BTS:BTC"]
    deexbtc = deexbts * btsbtc
    dgbbtc = prices["DGB:BTC"]
    eosbtc = prices["EOS:BTC"]
    ltcbtc = prices["LTC:BTC"]
    ethbtc = prices["ETH:BTC"]
    steembtc = prices["STEEM:BTC"]
    bchbtc = prices["BCH:BTC"]
    dashbtc = prices["DASH:BTC"]
    dogebtc = prices["DOGE:BTC"]
    xmrbtc = prices["XMR:BTC"]
    xembtc = prices["XEM:BTC"]
    btcdgb = 1 / dgbbtc
    btceos = 1 / eosbtc
    btceth = 1 / ethbtc
    btcltc = 1 / ltcbtc
    btcsteem = 1 / steembtc
    btcbch = 1 / bchbtc
    btcdash = 1 / dashbtc
    btcdoge = 1 / dogebtc
    btcxmr = 1 / xmrbtc
    btcxem = 1 / xembtc
    deexdgb = deexbtc * btcdgb
    deexeos = deexbtc * btceos
    deexeth = deexbtc * btceth
    deexltc = deexbtc * btcltc
    deexsteem = deexbtc * btcsteem
    deexbch = deexbtc * btcbch
    deexdash = deexbtc * btcdash
    deexdoge = deexbtc * btcdoge
    deexxmr = deexbtc * btcxmr
    deexxem = deexbtc * btcxem
    usddgb = usdbtc * btcdgb
    usdeos = usdbtc * btceos
    usdeth = usdbtc * btceth
    usdltc = usdbtc * btcltc
    usdsteem = usdbtc * btcsteem
    usdbch = usdbtc * btcbch
    usddash = usdbtc * btcdash
    usddoge = usdbtc * btcdoge
    usdxmr = usdbtc * btcxmr
    usdxem = usdbtc * btcxem
    cnydgb = cnyusd * usddgb
    cnyeos = cnyusd * usdeos
    cnyeth = cnyusd * usdeth
    cnyltc = cnyusd * usdltc
    cnysteem = cnyusd * usdsteem
    cnybch = cnyusd * usdbch
    cnydash = cnyusd * usddash
    cnydoge = cnyusd * usddoge
    cnyxmr = cnyusd * usdxmr
    cnyxem = cnyusd * usdxem
    qty_rate["DEEX:DEEX.DGB"] = {"qty": 3, "rate": deexdgb}
    qty_rate["DEEX:DEEX.EOS"] = {"qty": 3, "rate": deexeos}
    qty_rate["DEEX:DEEX.ETH"] = {"qty": 3, "rate": deexeth}
    qty_rate["DEEX:DEEX.LTC"] = {"qty": 3, "rate": deexltc}
    qty_rate["DEEX:DEEX.STEEM"] = {"qty": 3, "rate": deexsteem}
    qty_rate["DEEX:DEEX.BCH"] = {"qty": 3, "rate": deexbch}
    qty_rate["DEEX:DEEX.DASH"] = {"qty": 3, "rate": deexdash}
    qty_rate["DEEX:DEEX.DOGE"] = {"qty": 3, "rate": deexdoge}
    qty_rate["DEEX:DEEX.MONERO"] = {"qty": 3, "rate": deexxmr}
    qty_rate["DEEX:DEEX.NEM"] = {"qty": 3, "rate": deexxem}
    qty_rate["DEEX.BTC:DEEX.DGB"] = {"qty": 0.000003, "rate": btcdgb}
    qty_rate["DEEX.BTC:DEEX.EOS"] = {"qty": 0.000003, "rate": btceos}
    qty_rate["DEEX.BTC:DEEX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["DEEX.BTC:DEEX.LTC"] = {"qty": 0.000003, "rate": btcltc}
    qty_rate["DEEX.BTC:DEEX.STEEM"] = {"qty": 0.000003, "rate": btcsteem}
    qty_rate["DEEX.BTC:DEEX.BCH"] = {"qty": 0.000003, "rate": btcbch}
    qty_rate["DEEX.BTC:DEEX.DASH"] = {"qty": 0.000003, "rate": btcdash}
    qty_rate["DEEX.BTC:DEEX.DOGE"] = {"qty": 0.000003, "rate": btcdoge}
    qty_rate["DEEX.BTC:DEEX.MONERO"] = {"qty": 0.000003, "rate": btcxmr}
    qty_rate["DEEX.BTC:DEEX.NEM"] = {"qty": 0.000003, "rate": btcxem}
    qty_rate["HONEST.BTC:DEEX.DGB"] = {"qty": 0.000003, "rate": btcdgb}
    qty_rate["HONEST.BTC:DEEX.EOS"] = {"qty": 0.000003, "rate": btceos}
    qty_rate["HONEST.BTC:DEEX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["HONEST.BTC:DEEX.LTC"] = {"qty": 0.000003, "rate": btcltc}
    qty_rate["HONEST.BTC:DEEX.STEEM"] = {"qty": 0.000003, "rate": btcsteem}
    qty_rate["HONEST.BTC:DEEX.BCH"] = {"qty": 0.000003, "rate": btcbch}
    qty_rate["HONEST.BTC:DEEX.DASH"] = {"qty": 0.000003, "rate": btcdash}
    qty_rate["HONEST.BTC:DEEX.DOGE"] = {"qty": 0.000003, "rate": btcdoge}
    qty_rate["HONEST.BTC:DEEX.MONERO"] = {"qty": 0.000003, "rate": btcxmr}
    qty_rate["HONEST.BTC:DEEX.NEM"] = {"qty": 0.000003, "rate": btcxem}
    qty_rate["HONEST.USD:DEEX.DGB"] = {"qty": 0.03, "rate": usddgb}
    qty_rate["HONEST.USD:DEEX.EOS"] = {"qty": 0.03, "rate": usdeos}
    qty_rate["HONEST.USD:DEEX.ETH"] = {"qty": 0.03, "rate": usdeth}
    qty_rate["HONEST.USD:DEEX.LTC"] = {"qty": 0.03, "rate": usdltc}
    qty_rate["HONEST.USD:DEEX.STEEM"] = {"qty": 0.03, "rate": usdsteem}
    qty_rate["HONEST.USD:DEEX.BCH"] = {"qty": 0.03, "rate": usdbch}
    qty_rate["HONEST.USD:DEEX.DASH"] = {"qty": 0.03, "rate": usddash}
    qty_rate["HONEST.USD:DEEX.DOGE"] = {"qty": 0.03, "rate": usddoge}
    qty_rate["HONEST.USD:DEEX.MONERO"] = {"qty": 0.03, "rate": usdxmr}
    qty_rate["HONEST.USD:DEEX.NEM"] = {"qty": 0.03, "rate": usdxem}
    qty_rate["HONEST.CNY:DEEX.DGB"] = {"qty": 0.3, "rate": cnydgb}
    qty_rate["HONEST.CNY:DEEX.EOS"] = {"qty": 0.3, "rate": cnyeos}
    qty_rate["HONEST.CNY:DEEX.ETH"] = {"qty": 0.3, "rate": cnyeth}
    qty_rate["HONEST.CNY:DEEX.LTC"] = {"qty": 0.3, "rate": cnyltc}
    qty_rate["HONEST.CNY:DEEX.STEEM"] = {"qty": 0.3, "rate": cnysteem}
    qty_rate["HONEST.CNY:DEEX.BCH"] = {"qty": 0.3, "rate": cnybch}
    qty_rate["HONEST.CNY:DEEX.DASH"] = {"qty": 0.3, "rate": cnydash}
    qty_rate["HONEST.CNY:DEEX.DOGE"] = {"qty": 0.3, "rate": cnydoge}
    qty_rate["HONEST.CNY:DEEX.MONERO"] = {"qty": 0.3, "rate": cnyxmr}
    qty_rate["HONEST.CNY:DEEX.NEM"] = {"qty": 0.3, "rate": cnyxem}
    return qty_rate


def xbtsx_qty_rate(prices):
    """
    build a qty_rate dictionary for xbtsx
    """
    qty_rate = {}
    btcusd = prices["BTC:USD"]
    usdbtc = 1 / btcusd
    usdcny = prices["USD:CNY"]
    cnyusd = 1 / usdcny
    sthbts = prices["STH:BTS"]
    btsbtc = prices["BTS:BTC"]
    sthbtc = sthbts * btsbtc
    bchbtc = prices["BCH:BTC"]
    btgbtc = prices["BTG:BTC"]
    ltcbtc = prices["LTC:BTC"]
    ethbtc = prices["ETH:BTC"]
    wavesbtc = prices["WAVES:BTC"]
    btcbch = 1 / bchbtc
    btcbtg = 1 / btgbtc
    btceth = 1 / ethbtc
    btcltc = 1 / ltcbtc
    btcwaves = 1 / wavesbtc
    sthbch = sthbtc * btcbch
    sthbtg = sthbtc * btcbtg
    stheth = sthbtc * btceth
    sthwaves = sthbtc * btcwaves
    sthltc = sthbtc * btcltc
    usdbch = usdbtc * btcbch
    usdbtg = usdbtc * btcbtg
    usdeth = usdbtc * btceth
    usdwaves = usdbtc * btcwaves
    usdltc = usdbtc * btcltc
    cnybch = cnyusd * usdbch
    cnybtg = cnyusd * usdbtg
    cnyeth = cnyusd * usdeth
    cnyltc = cnyusd * usdltc
    cnywaves = cnyusd * usdwaves
    qty_rate["XBTSX.STH:XBTSX.BCH"] = {"qty": 3, "rate": sthbch}
    qty_rate["XBTSX.STH:XBTSX.BTG"] = {"qty": 3, "rate": sthbtg}
    qty_rate["XBTSX.STH:XBTSX.ETH"] = {"qty": 3, "rate": stheth}
    qty_rate["XBTSX.STH:XBTSX.LTC"] = {"qty": 3, "rate": sthltc}
    qty_rate["XBTSX.STH:XBTSX.WAVES"] = {"qty": 3, "rate": sthwaves}
    qty_rate["XBTSX.BTC:XBTSX.BCH"] = {"qty": 0.000003, "rate": btcbch}
    qty_rate["XBTSX.BTC:XBTSX.BTG"] = {"qty": 0.000003, "rate": btcbtg}
    qty_rate["XBTSX.BTC:XBTSX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["XBTSX.BTC:XBTSX.LTC"] = {"qty": 0.000003, "rate": btcltc}
    qty_rate["XBTSX.BTC:XBTSX.WAVES"] = {"qty": 0.000003, "rate": btcwaves}
    qty_rate["HONEST.BTC:XBTSX.BCH"] = {"qty": 0.000003, "rate": btcbch}
    qty_rate["HONEST.BTC:XBTSX.BTG"] = {"qty": 0.000003, "rate": btcbtg}
    qty_rate["HONEST.BTC:XBTSX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["HONEST.BTC:XBTSX.LTC"] = {"qty": 0.000003, "rate": btcltc}
    qty_rate["HONEST.BTC:XBTSX.WAVES"] = {"qty": 0.000003, "rate": btcwaves}
    qty_rate["HONEST.USD:XBTSX.BCH"] = {"qty": 0.03, "rate": usdbch}
    qty_rate["HONEST.USD:XBTSX.BTG"] = {"qty": 0.03, "rate": usdbtg}
    qty_rate["HONEST.USD:XBTSX.ETH"] = {"qty": 0.03, "rate": usdeth}
    qty_rate["HONEST.USD:XBTSX.LTC"] = {"qty": 0.03, "rate": usdltc}
    qty_rate["HONEST.USD:XBTSX.WAVES"] = {"qty": 0.03, "rate": usdwaves}
    qty_rate["HONEST.CNY:XBTSX.BCH"] = {"qty": 0.3, "rate": cnybch}
    qty_rate["HONEST.CNY:XBTSX.BTG"] = {"qty": 0.3, "rate": cnybtg}
    qty_rate["HONEST.CNY:XBTSX.ETH"] = {"qty": 0.3, "rate": cnyeth}
    qty_rate["HONEST.CNY:XBTSX.LTC"] = {"qty": 0.3, "rate": cnyltc}
    qty_rate["HONEST.CNY:XBTSX.WAVES"] = {"qty": 0.3, "rate": cnywaves}
    return qty_rate


def rudex_qty_rate(prices):
    """
    build a qty_rate dictionary for rudex
    """
    qty_rate = {}
    btcusd = prices["BTC:USD"]
    usdbtc = 1 / btcusd
    usdcny = prices["USD:CNY"]
    cnyusd = 1 / usdcny
    dgbbtc = prices["DGB:BTC"]
    eosbtc = prices["EOS:BTC"]
    steembtc = prices["STEEM:BTC"]
    ethbtc = prices["ETH:BTC"]
    btcdgb = 1 / dgbbtc
    btceos = 1 / eosbtc
    btceth = 1 / ethbtc
    btcsteem = 1 / steembtc
    usddgb = usdbtc * btcdgb
    usdeos = usdbtc * btceos
    usdeth = usdbtc * btceth
    usdsteem = usdbtc * btcsteem
    cnydgb = cnyusd * usddgb
    cnyeos = cnyusd * usdeos
    cnyeth = cnyusd * usdeth
    cnysteem = cnyusd * usdsteem
    ethdgb = ethbtc * btcdgb
    etheos = ethbtc * btceos
    ethsteem = ethbtc * btcsteem
    eosdgb = eosbtc * btcdgb
    eossteem = eosbtc * btcsteem
    dgbsteem = dgbbtc * btcsteem
    qty_rate["RUDEX.DGB:RUDEX.STEEM"] = {"qty": 30, "rate": dgbsteem}
    qty_rate["RUDEX.EOS:RUDEX.DGB"] = {"qty": 0.003, "rate": eosdgb}
    qty_rate["RUDEX.EOS:RUDEX.STEEM"] = {"qty": 0.003, "rate": eossteem}
    qty_rate["RUDEX.ETH:RUDEX.DGB"] = {"qty": 0.00003, "rate": ethdgb}
    qty_rate["RUDEX.ETH:RUDEX.EOS"] = {"qty": 0.00003, "rate": etheos}
    qty_rate["RUDEX.ETH:RUDEX.STEEM"] = {"qty": 0.00003, "rate": ethsteem}
    qty_rate["RUDEX.BTC:RUDEX.DGB"] = {"qty": 0.000003, "rate": btcdgb}
    qty_rate["RUDEX.BTC:RUDEX.EOS"] = {"qty": 0.000003, "rate": btceos}
    qty_rate["RUDEX.BTC:RUDEX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["RUDEX.BTC:RUDEX.STEEM"] = {"qty": 0.000003, "rate": btcsteem}
    qty_rate["HONEST.BTC:RUDEX.DGB"] = {"qty": 0.000003, "rate": btcdgb}
    qty_rate["HONEST.BTC:RUDEX.EOS"] = {"qty": 0.000003, "rate": btceos}
    qty_rate["HONEST.BTC:RUDEX.ETH"] = {"qty": 0.000003, "rate": btceth}
    qty_rate["HONEST.BTC:RUDEX.STEEM"] = {"qty": 0.000003, "rate": btcsteem}
    qty_rate["HONEST.USD:RUDEX.DGB"] = {"qty": 0.03, "rate": usddgb}
    qty_rate["HONEST.USD:RUDEX.EOS"] = {"qty": 0.03, "rate": usdeos}
    qty_rate["HONEST.USD:RUDEX.ETH"] = {"qty": 0.03, "rate": usdeth}
    qty_rate["HONEST.USD:RUDEX.STEEM"] = {"qty": 0.03, "rate": usdsteem}
    qty_rate["HONEST.CNY:RUDEX.DGB"] = {"qty": 0.3, "rate": cnydgb}
    qty_rate["HONEST.CNY:RUDEX.EOS"] = {"qty": 0.3, "rate": cnyeos}
    qty_rate["HONEST.CNY:RUDEX.ETH"] = {"qty": 0.3, "rate": cnyeth}
    qty_rate["HONEST.CNY:RUDEX.STEEM"] = {"qty": 0.3, "rate": cnysteem}
    return qty_rate


def create_qty_rate(prices, gateway):
    """
    fetch a qty rate dictionary for the correct gateway
    """
    if gateway == "DEEX":
        qty_rate = deex_qty_rate(prices)
    if gateway == "XBTSX":
        qty_rate = xbtsx_qty_rate(prices)
    if gateway == "RUDEX":
        qty_rate = rudex_qty_rate(prices)

    for key, val in qty_rate.items():
        qty_rate[key] = {"qty":val["qty"],"rate":sigfig(val["rate"])}
        
    return qty_rate


def sceletus(prices, gateway, name, wif, do_sceletus):
    """
    update the historic chart on the blockchain using buy/sell broker(order) method
    for each pair to be skeleton'd, for each agent on opposing sides of the book
    """
    orders = []
    order_dict = {}
    header = {}
    # build qty_rate dict
    qty_rate = create_qty_rate(prices, gateway)
    print("\033c")
    print_logo()   
    print("\n\nQTY_RATE")
    for k, v in qty_rate.items():
        print(k, v, it("cyan", sigfig(1/v["rate"])))
    time.sleep(5)
    print(it("green", "Begin sceletus buy/sell ops..."))
    time.sleep(5)
    account_id = ""
    if do_sceletus:
        rpc = reconnect(None)
        account_id = rpc_lookup_accounts(rpc, {"account_name": name})
    for pair in qty_rate.keys():
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
        for _ in range(50):
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
            shuffle(nodes)
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
                    "name": name,
                    "op": operation,
                    "pair": pair,
                    "price": price,
                    "amount": amount,
                }
            )

            if do_sceletus:
                broker(order)
    if do_sceletus:
        print("\033c")
        print_logo()
        print(it("cyan", "OPEN ORDERS"))
        rpc_open_orders(rpc, name)

    return orders, order_dict


def select_exchanges(asset):
    """
    returns a dict keyed by asset which trades to btc
    value is a list of available exchanges where it trades
    """
    all_exchanges = [
        "kraken",
        "hitbtc",
        "poloniex",
        "huobi",
        "bittrex",
        "binance",
        "bitfinex",
    ]

    listings = {
        "BTS": ["bittrex", "binance", "poloniex", "huobi", "hitbtc"],
        "DGB": ["bittrex", "bitfinex", "huobi", "hitbtc"],
        "EOS": all_exchanges,
        "ETH": all_exchanges,
        "STEEM": ["hitbtc", "binance", "huobi", "bittrex"],
        "BCH": all_exchanges,
        "BTG": ["hitbtc", "bitfinex", "binance", "huobi"],
        "LTC": all_exchanges,
        "WAVES": ["kraken", "hitbtc", "binance", "bittrex", "huobi"],
        "DASH": all_exchanges,
        "DOGE": ["kraken", "hitbtc", "poloniex", "huobi", "bittrex", "binance"],
        "XMR": all_exchanges,
        "XEM": ["poloniex", "bittrex", "binance", "hitbtc", "huobi"],
        "ZEC": all_exchanges,
    }
    return listings[asset]


def select_assets(gateway):
    """
    given a gateway, return the correct list of assets
    """

    if gateway == "DEEX":
        assets = [
            "DGB",
            "EOS",
            "ETH",
            "STEEM",
            "BCH",
            "LTC",
            "DASH",
            "DOGE",
            "XMR",
            "XEM",
            "ZEC",
        ]
    if gateway == "RUDEX":
        assets = ["DGB", "EOS", "ETH", "STEEM"]
    if gateway == "XBTSX":
        assets = ["ETH", "BCH", "BTG", "LTC", "WAVES"]

    assets.append("BTS")

    return assets


def user_input():
    """
    initialize script with user inputs
    """
    print("\nChoose RUDEX, XBTSX, or DEEX\n")
    gateway = input("enter gateway: ").upper()
    do_sceletus = input(
        "\n  to SCELETUS"
        + it("cyan", " y + Enter ")
        + "or just Enter for Demo\n\n           "
    ).lower()
    wif, name = "", ""
    if do_sceletus == "y":
        name = input("\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           "))
        wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
        print("           *****************")

    return gateway, do_sceletus, name, wif


def main():
    """
    primary event loop
    """
    print("\033c")
    print_logo()
    print(it("cyan", "    presents:  Gateway Sceletus"))
    gateway, do_sceletus, name, wif = user_input()
    while True:
        print("\033c")
        print_logo()
        if do_sceletus:
            print(it("cyan", "Cancelling ALL Open Orders..."))
            cancel_all_markets(name, wif)
        print("\033c")
        print_logo()
        print(it("cyan", "Gathering CEX Data..."))
        cex = cex_rates(gateway)
        print("\033c")
        print_logo()
        print(it("cyan", "Gathering DEX Data..."))
        dex = dex_rates(gateway)
        print("\033c")
        print_logo()
        print(it("cyan", "Gathering FOREX Data..."))
        forex = forex_rates()
        print("\033c")
        print_logo()        
        print(it("cyan", "\n\nCEX"))
        print(cex)
        print(it("cyan", "\n\nDEX"))
        print(dex)
        print(it("cyan", "\n\nFOREX"))
        print(forex["medians"])
        race_write("pricefeed_cex.txt", cex)
        race_write("pricefeed_forex.txt", forex)        
        prices = create_prices(cex, dex, forex)
        time.sleep(10)
        sceletus(prices, gateway, name, wif, do_sceletus)
        time.sleep(REFRESH-100)


if __name__ == "__main__":

    main()
