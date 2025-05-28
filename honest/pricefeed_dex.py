"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

pricefeed UX and GATEWAY.BTC:BTS data bifurcation

this is a metanode fork, but instead of one account and one asset, it maintains
median pricing for all gatewayBTC:BTS (plus gatewayUSD:BTS - for reference only)

litepresence2020
"""

# DISABLE SELECT PYLINT TESTS
# pylint: disable=too-many-statements, too-many-locals, too-many-branches
# pylint: disable=too-many-arguments, broad-except, bare-except, invalid-name
# pylint: disable=too-many-nested-blocks, bad-continuation, bad-whitespace
# pylint: disable=too-many-lines

import os
from calendar import timegm
from datetime import datetime
from json import dumps as json_dump
from json import loads as json_load
from multiprocessing import Process, Value
from os import popen
from random import random, shuffle
from statistics import median, mode
from sys import stdout
# STANDARD PYTHON MODULES
from time import ctime, sleep, strptime, time
from traceback import format_exc

import numpy as np
from config_nodes import public_nodes
from exchanges import EXCHANGES
# THIRD PARTY MODULES
from psutil import Process as psutil_Process
# HONEST PRICE FEED MODULES
from utilities import (PATH, at, it, print_logo, race_append, race_read,
                       race_write, sigfig, string_width, trace)
from websocket import create_connection as wss
from websocket import enableTrace

# ======================================================================
VERSION = "HONEST MPA DEX FEED 0.00000001"
# ======================================================================
DEV = False
COLOR = True
MAVENS = 7  # 7
TIMEOUT = 100  # 100
PROCESSES = 1  # 20 (slower than metanode)
MIN_NODES = 9  # 15
BOOK_DEPTH = 2  # 30
THRESH_PAUSE = 20  # 10  # 4 (slower than metanode)
UTILIZATIONS = 30  # 30
HISTORY_DEPTH = 2  # 30
LATENCY_REPEAT = 900  # 900
LATENCY_TIMEOUT = 5  # 5
BIFURCATION_PAUSE = 20  # 10  # 2 (slower than metanode)
# ======================================================================
ID = "4018d7844c78f6a6c41c6a552b898022310fc5dec06da467ee7905a8dad512c8"
# ======================================================================

CURRENCIES = [
    "GDEX.BTC",
    "XBTSX.BTC",
    "GDEX.USDT",
    "XBTSX.USDT",
    "IOB.XRP",
    "BTWTY.EOS",
]
ASSET = "BTS"


# INTER PROCESS COMMUNICATION VIA TEXT
# ======================================================================
def bitshares_trustless_client():
    """
    Include this definition in your script to access pricefeed_dex.txt
    Deploy your bot script in the same folder as pricefeed_dex.py
    """
    doc = os.path.join(PATH, "pipe", "pricefeed_dex.txt")

    while True:
        try:
            with open(doc, "r") as handle:
                ret = handle.read()
                handle.close()
                data = json_load(ret)
                break
        except Exception as error:
            msg = trace(error)
            race_condition = ["Unterminated", "Expecting"]
            if any(x in str(error.args) for x in race_condition):
                print("pricefeed_dex = bitshares_trustless_client() RACE READ")
            elif "pricefeed_dex is blank" in str(error.args):
                continue
            else:
                print("pricefeed_dex = bitshares_trustless_client() " + msg)
            try:
                handle.close()
            except BaseException:
                pass
        finally:
            try:
                handle.close()
            except BaseException:
                pass
    return data


# WEBSOCKET SEND AND RECEIVE
# ======================================================================
def wss_handshake(storage, node):  # DONE
    """
    Create a websocket handshake
    """
    start = time()
    handshake_max = min(9.999, 10 * storage["mean_ping"])
    rpc = wss(node, timeout=handshake_max)
    handshake_latency = min(9.999, (time() - start))
    if 0 > handshake_latency > handshake_max:
        raise ValueError("slow handshake", handshake_latency)
    sleep(2)
    return rpc, handshake_latency, handshake_max


def wss_query(rpc, params):  # DONE
    """
    Send and receive websocket requests
    """
    query = json_dump({"method": "call", "params": params, "jsonrpc": "2.0", "id": 1})
    rpc.send(query)
    ret = json_load(rpc.recv())
    try:
        return ret["result"]  # if there is result key take it
    except BaseException:
        return ret


# REMOTE PROCEDURE CALLS TO PUBLIC API DATABASE
# ======================================================================
def rpc_lookup_asset_symbols(rpc):  # DONE
    """
    Given asset names return asset ids and precisions
    """

    query_list = list(CURRENCIES)
    query_list.append(ASSET)
    ret = wss_query(rpc, ["database", "lookup_asset_symbols", [query_list]])
    # asset is bitshares
    asset_id = ret[-1]["id"]
    asset_precision = ret[-1]["precision"]
    # currencies are gatewayBTC and gatewayUSD
    currency_id = {}
    currency_precision = {}
    for idx, item in enumerate(CURRENCIES):
        currency_id[item] = ret[idx]["id"]
        currency_precision[item] = ret[idx]["precision"]
    return asset_id, asset_precision, currency_id, currency_precision


def rpc_block_latency(rpc, storage):  # DONE
    """
    Confirm the data contained on this node is not stale
    """
    dgp = wss_query(rpc, ["database", "get_dynamic_global_properties", []])
    blocktime = from_iso_date(dgp["time"])
    block_latency = min(9.999, (time() - blocktime))
    block_max = min(9.999, (3 + 3 * storage["mean_ping"]))
    if 0 > block_latency > block_max:
        raise ValueError("stale blocktime", block_latency)
    return block_latency, block_max, int(blocktime)


def rpc_ping_latency(rpc, storage):  # DONE
    """
    Confirm we have fast connection to a node on the correct chain
    """
    start = time()
    chain_id = wss_query(rpc, ["database", "get_chain_id", []])
    ping_latency = min(9.999, (time() - start))
    ping_max = min(2, 2 * storage["mean_ping"])
    if chain_id != ID:
        raise ValueError("chain_id != ID")
    if 0 > ping_latency > ping_max:
        raise ValueError("slow ping", ping_latency)
    return ping_latency, ping_max


def rpc_last(rpc, cache):  # DONE
    """
    Get the latest ticker price
    """

    last = {}

    for currency in CURRENCIES:
        ticker = wss_query(
            rpc, ["database", "get_ticker", [currency, cache["asset"], False]]
        )
        last[currency] = float(precision(ticker["latest"], 16))
        if last[currency] == 0:
            raise ValueError("zero price last")

    return last


def rpc_pool_last(rpc, cache):
    last = {}
    # get asset ids and precisions
    currency_objs = wss_query(rpc, ["database", "lookup_asset_symbols", [CURRENCIES]])
    # for all currency names and data pairs
    for currency, get_obj in zip(CURRENCIES, currency_objs):
        # get all the pools for this pair
        pools = [
            i
            for i in wss_query(
                rpc, ["database", "get_liquidity_pools_by_asset_b", [get_obj["id"]]]
            )
            if i["asset_a"] == "1.3.0"
        ]
        if not pools:
            continue
        # choose pool with the maximum amount of BTS staked
        pool = max(
            pools,
            key=lambda x: int(x["balance_a"]),
        )
        # calculate the last price given a and b balances w/ respective precision
        bal_a = int(pool["balance_a"]) / 10**5
        bal_b = int(pool["balance_b"]) / 10 ** get_obj["precision"]
        if bal_a < 50000:
            continue
        last[currency] = bal_b / bal_a
    # a dictionary of pool prices
    return last


# STATISTICAL DATA CURATION
# ======================================================================
def initialize_storage(storage):
    """Initialize storage dictionary with default values"""
    storage["access"] = 0
    storage["data_latency"] = 0
    storage["mean_ping"] = 0.5


def get_node_info():
    """Get and shuffle nodes, return first node and set bandwidth depth"""
    nodes = get_nodes()
    static_nodes = public_nodes()
    shuffle(nodes)
    return nodes[0], nodes, static_nodes


def handle_lists(storage, node):
    """Manage blacklists and whitelists"""
    black = race_read(doc="blacklist.txt")[-storage["bw_depth"] :]
    white = race_read(doc="whitelist.txt")[-storage["bw_depth"] :]

    try:
        start = time()
        metanode = bitshares_trustless_client()
        storage["access"] = time() - start
        ping = storage["mean_ping"] = metanode["ping"]
        blacklist = metanode["blacklist"][-storage["bw_depth"] :]
        whitelist = metanode["whitelist"][-storage["bw_depth"] :]
        blocktime = metanode["blocktime"]
        storage["data_latency"] = time() - blocktime
        del metanode

        if len(blacklist) > len(black):
            black = blacklist
            race_write("blacklist.txt", json_dump(black))
        if len(whitelist) > len(white):
            white = whitelist
            race_write("whitelist.txt", json_dump(white))

        return black, white, blocktime, ping
    except BaseException:
        return black, white, None, None


def calculate_metrics(
    handshake_bs,
    ping_bs,
    block_bs,
    reject_bs,
    handshake_latency,
    handshake_max,
    ping_latency,
    ping_max,
    block_latency,
    block_max,
):
    """Calculate timing metrics and maintain history"""
    set_timing = "                  " + "speed/max/ratio/cause/rate"
    if handshake_max == 5:
        set_timing = "                  " + it("cyan", "RESOLVING MEAN NETWORK SPEED")

    ping_r = ping_latency / ping_max
    block_r = block_latency / block_max
    handshake_r = handshake_latency / handshake_max

    ping_b = int(bool(int(ping_r)))
    block_b = int(bool(int(block_r)))
    handshake_b = int(bool(int(handshake_r)))
    reject_b = int(bool(ping_b + block_b + handshake_b))

    ping_bs.append(ping_b)
    block_bs.append(block_b)
    reject_bs.append(reject_b)
    handshake_bs.append(handshake_b)

    ping_bs = ping_bs[-100:]
    block_bs = block_bs[-100:]
    reject_bs = reject_bs[-100:]
    handshake_bs = handshake_bs[-100:]

    ping_p = sum(ping_bs) / max(1, len(ping_bs))
    block_p = sum(block_bs) / max(1, len(block_bs))
    reject_p = sum(reject_bs) / max(1, len(reject_bs))
    handshake_p = sum(handshake_bs) / max(1, len(handshake_bs))

    return (
        set_timing,
        ping_r,
        block_r,
        handshake_r,
        ping_b,
        block_b,
        handshake_b,
        reject_b,
        ping_p,
        block_p,
        reject_p,
        handshake_p,
        ping_bs,
        block_bs,
        reject_bs,
        handshake_bs,
    )


def get_system_metrics(storage, process, cache):
    """Get system resource metrics"""
    try:
        proc = psutil_Process()
        descriptors = proc.num_fds()
        usage = "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }'"
        cpu = "%.3f" % (float(popen(usage).readline()))
        ram = "%.3f" % (100 * float(proc.memory_percent()))
        io_count = list(proc.io_counters())[:2]

        metanode = bitshares_trustless_client()
        m_last, ping, keys = {}, 0.5, ["bifurcating the metanode...."]
        try:
            keys = metanode["keys"]
            ping = storage["mean_ping"] = metanode["ping"]
            m_last = metanode["last"]
        except Exception as error:
            if DEV or True:
                print(trace(error))
        del metanode

        return descriptors, cpu, ram, io_count, m_last, ping, keys
    except Exception as error:
        if DEV or True:
            print(trace(error))
        return None, None, None, None, {}, 0.5, ["bifurcating the metanode...."]


def process_price_data(m_last):
    """Process price data and calculate medians"""
    usds, btcs = [], []
    usd_dict, btc_dict = {}, {}

    try:
        for key, val in m_last.items():
            if "BTC" in key:
                btcs.append(val)
                btc_dict[key] = sigfig(val, 4)
            elif "USD" in key:
                usds.append(val)
                usd_dict[key] = sigfig(val, 4)
        usd = sigfig(median(usds), 4)
        btc = sigfig(median(btcs), 4)
        implied_btcusd = usd / btc
    except Exception as error:
        print(trace(error))
        usd, btc, implied_btcusd = None, None, None

    return usd, btc, implied_btcusd, usd_dict, btc_dict


def print_metanode_stats(local_vars):
    runtime = int(time()) - local_vars["cache"]["begin"]
    optimizing = (
        it("cyan", "OPTIMIZING".ljust(7))
        if (time() - local_vars["cache"]["begin"]) > 200
        else "".ljust(7)
    )
    reject = it("cyan", "X".ljust(7)) if local_vars["reject_b"] else "".ljust(7)

    alert = (
        it("cyan", "    BUILDING BLACK AND WHITE LISTS")
        if (
            len(local_vars["white"]) < local_vars["storage"]["bw_depth"]
            or len(local_vars["black"]) < local_vars["storage"]["bw_depth"]
        )
        else ""
    )
    if local_vars["nodes"] == local_vars["static_nodes"]:
        alert += " ::WARN:: USING STATIC NODE LIST"

    upm = len(local_vars["storage"].get("updates", []))

    print()
    print(
        "runtime:epoch:pid:upm",
        it("green", runtime),
        local_vars["epoch"],
        local_vars["pid"],
        upm,
    )
    try:
        print(
            "fds:processes        ",
            local_vars["descriptors"],
            local_vars["process"],
            "of",
            PROCESSES,
        )
    except:
        print("processes:           ", local_vars["process"], "of", PROCESSES)
    try:
        print(
            "cpu:ram:io_count     ",
            local_vars["cpu"],
            local_vars["ram"],
            local_vars["io_count"],
        )
    except:
        pass
    print(
        "utilization:node     ",
        str(local_vars["util"] + 1).ljust(3),
        local_vars["node"],
    )
    print(
        "total:white:black    ",
        # len(local_vars["static_nodes"]),
        len(local_vars["nodes"]),
        len(local_vars["white"]),
        len(local_vars["black"]),
        alert,
    )
    print(local_vars["set_timing"])
    print(
        "block latency        ",
        "%.2f %.1f %.1f %s %.2f"
        % (
            local_vars["block_latency"],
            local_vars["block_max"],
            local_vars["block_r"],
            str(local_vars["block_b"]).ljust(7),
            local_vars["block_p"],
        ),
    )
    print(
        "handshake            ",
        "%.2f %.1f %.1f %s %.2f"
        % (
            local_vars["handshake_latency"],
            local_vars["handshake_max"],
            local_vars["handshake_r"],
            str(local_vars["handshake_b"]).ljust(7),
            local_vars["handshake_p"],
        ),
    )
    print(
        "ping                 ",
        "%.2f %.1f %.1f %s %.2f"
        % (
            local_vars["ping_latency"],
            local_vars["ping_max"],
            local_vars["ping_r"],
            str(local_vars["ping_b"]).ljust(7),
            local_vars["ping_p"],
        ),
    )
    print(
        "mean ping            ",
        (it("purple", "%.3f" % local_vars["ping"])),
        "       %s %.2f" % (reject, local_vars["reject_p"]),
        optimizing,
    )
    print("")


def dex_table(local_vars):
    dex_string = ""
    # DEX
    try:
        gateways = sorted(list({i.split(".", 1)[0] for i in CURRENCIES}))
        gateway_tokens = sorted(list({i.split(".", 1)[1] for i in CURRENCIES}))

        # gateway_table is len(gateway_tokens)+1 rows and len(gateways)+1 columns
        table = [[" " * 16] + [i.ljust(10) for i in gateway_tokens]]
        for gateway in gateways:
            row = [gateway.ljust(10)] + [
                str(sigfig(local_vars["last"].get(f"{gateway}.{token}", -1), 4)).ljust(
                    10
                )
                for token in gateway_tokens
            ]
            row = [
                i
                if not any(j.isdigit() for j in i)
                else it("green", i)
                if "-1" not in i
                else it("yellow", i)
                for i in row
            ]
            table.append(row)

        # table is now len(gateway_tokens)+1 columns and len(gateways)+1 rows
        table = np.array(table).T
        dex_string = "\n".join("".join(row) for row in table)
    except Exception as error:
        if DEV:
            print(trace(error))
        print(
            it("red", "WARN:"),
            "gathering DEX prices failed, maybe the metanode isn't live yet?",
        )
    return dex_string


def cex_table(local_vars):
    cex_string = ""
    # CEX
    try:
        cex = race_read("pricefeed_cex.txt")

        if cex:
            # sort by pair
            cex = dict(sorted(cex.items()))

            exchanges = []
            for key, val in cex.items():
                exchanges.extend(list(val["data"].keys()))
            exchanges = sorted(list(set(exchanges)))

            pairs = list(cex.keys())
            just_size = max(map(len, pairs)) + 2

            table = [exchanges + ["median"]]
            for coin, data in cex.items():
                table.append([data["data"].get(exchange, -1) for exchange in exchanges])
                table[-1].append(data["median"])
            n_prices = list([len([i for i in j if i != -1]) - 1 for j in table[1:]])
            table = list(zip(*table))

            exchange_just = max(map(len, exchanges)) + 2

            # print header
            cex_string += " " * exchange_just + "".join(
                it(
                    "white"
                    if count >= 7
                    else "yellow"
                    if count >= 5
                    else "red"
                    if count >= 2
                    else "cyan",
                    coin.ljust(just_size),
                )
                for coin, count in zip(pairs, n_prices)
            )
            for rdx, row in enumerate(table):
                cex_string += "\n" + (
                    (
                        row[0].ljust(exchange_just)
                        if row[0] != "median"
                        else it("purple", row[0].center(exchange_just))
                    )
                    + "".join(
                        [
                            it(
                                (
                                    "green"
                                    if i != -1 or rdx >= len(exchanges)
                                    else "red"
                                    if exchanges[rdx] in EXCHANGES[pairs[idx]]
                                    else "yellow"
                                )
                                if row[0] != "median"
                                else "cyan",
                                str(sigfig(i, 4)).ljust(just_size),
                            )
                            for idx, i in enumerate(row[1:])
                        ]
                    )
                )
            cex_string = (
                it("yellow", " CEX ".center(string_width(cex_string), "═"))
                + "\n\n"
                + cex_string
            )
    except Exception as error:
        if DEV:
            print(trace(error))
        print(
            it("red", "WARN:"),
            "gathering CEX prices failed, maybe they aren't done yet?",
        )
    return cex_string


def forex_table(local_vars):
    forex_string = ""
    try:
        forex = race_read("pricefeed_forex.txt")
        if forex:
            # sort the pairs and sources
            forex["aggregate"] = dict(sorted(forex["aggregate"].items()))
            forex["sources"] = dict(sorted(forex["sources"].items()))

            # get the lists of pairs and sources
            pairs = list(forex["aggregate"].keys())
            sources = list(forex["sources"].keys())
            just_size = max(map(len, pairs)) + 2

            table = [sources]
            for pair, data in forex["aggregate"].items():
                data = dict([i[::-1] for i in data])
                table.append([data.get(source, -1) for source in sources])
            table = list(zip(*table))
            # table is now rows=source; cols=pair

            # add median column
            table.append(["median"] + [forex["medians"][pair][0] for pair in pairs])

            n_prices = [forex["medians"][pair][1] for pair in pairs]

            source_just = max(map(len, sources)) + 2

            # print header
            forex_string += " " * source_just + "".join(
                it(
                    "white"
                    if count >= 7
                    else "yellow"
                    if count >= 5
                    else "red"
                    if count >= 2
                    else "cyan",
                    coin.ljust(just_size),
                )
                for coin, count in zip(pairs, n_prices)
            )
            for rdx, row in enumerate(table):
                forex_string += "\n" + (
                    (
                        it("red", row[0].ljust(source_just))
                        if all(i == -1 for i in row[1:])
                        else row[0].ljust(source_just)
                        if row[0] != "median"
                        else it("purple", row[0].center(source_just))
                    )
                    + "".join(
                        [
                            it(
                                ("green" if i != -1 else "yellow")
                                if row[0] != "median"
                                else "cyan",
                                str(sigfig(i, 4)).ljust(just_size),
                            )
                            for idx, i in enumerate(row[1:])
                        ]
                    )
                )
            forex_string = (
                it(
                    "purple",
                    " FOREX / AGGREGATORS ".center(string_width(forex_string), "═"),
                )
                + "\n\n"
                + forex_string
            )
    except Exception as error:
        if DEV:
            print(trace(error))
        print(
            it("red", "WARN:"),
            "gathering FOREX prices failed, maybe they aren't done yet?",
        )
    return forex_string


def final_table(local_vars):
    final_string = ""
    try:
        final = race_read("pricefeed_final.txt")
        if final:
            table = []
            for pair, price in sorted(final["feed"].items()):
                table.append([pair, str(sigfig(price, 5))])
            just = max([max(map(len, row)) for row in table])
            final_string = "\n".join(
                "".join([row[0].ljust(just), it("cyan", row[1]).ljust(just)])
                for row in table
            )
    except Exception as error:
        # if DEV:
        print(trace(error))
        print(
            it("red", "WARN:"),
            "gathering final feed failed, maybe it isn't done yet?",
        )
    return final_string


def print_status(local_vars):
    """Handle all printing operations using the local variables of thresh"""
    logo_string = print_logo(False)
    print("\033c")

    dex_string = dex_table(local_vars)
    cex_string = cex_table(local_vars)
    forex_string = forex_table(local_vars)
    final_string = final_table(local_vars)

    try:
        # find the maximum width of the DEX table
        width = string_width(dex_string)

        # all the " "*6 is for padding off the left side

        # center the logo across that width, and print it and the DEX table
        print()
        print(
            it(
                "green",
                "\n".join(" " * 6 + i.center(width) for i in logo_string.split("\n")),
            )
        )
        print("\n")
        # while ensuring the dex table's header is full width;
        # note this is a Calvin S unicode character, not an equals sign
        print(" " * 6 + it("green", " DEX ".center(width, "═")))
        print("\n")
        print(dex_string.replace("\n", "\n" + " " * 6))

        forex_width = string_width(forex_string)
        forex_height = len(forex_string.split("\n"))

        # print the FOREX table "hanging" off the side of the DEX table

        print(
            at(
                (
                    width + 12,
                    2,
                    forex_width,
                    forex_height,
                ),
                forex_string,
            )
        )
        print("\n")

        if final_string:
            print(
                at(
                    (
                        width + 18 + forex_width,
                        2,
                        string_width(final_string),
                        2,
                    ),
                    it("green", " FINAL FEED ".center(string_width(final_string), "═")),
                )
            )
            print(
                at(
                    (
                        width + 18 + forex_width,
                        4,
                        string_width(final_string),
                        len(final_string.split("\n")),
                    ),
                    final_string,
                )
            )
        # reset cursor to the bottom of the forex table
        print(at((1, forex_height + 3, 1, 1), ""))

        # center the CEX table on the combined width of the FOREX and DEX tables
        cex_width = string_width(cex_string)
        delta = (width + 12 + forex_width) - cex_width
        if delta > 0:
            cex_string = cex_string.replace("\n", "\n" + (" " * (delta // 2)))

        print(cex_string)

        if DEV:
            print_metanode_stats(local_vars)
        final = race_read("pricefeed_final.txt")
        if final:
            print("\n\n")
            print(it("cyan", "BTS:BTC sources:"), race_read("bts_btc_pipe.txt"))
            print("FEED CLOCK", it("yellow", final["time"]))
            stale = time() - final["time"]["unix"]
            if stale > 4000:
                print(it("red", f"WARNING YOUR FEED IS STALE BY {stale} SECONDS"))
    except Exception as error:
        print(trace(error))
        print(
            it("red", "WARN:"),
            "Printing source tables failed!  Retrying on next thresh...",
        )


def thresh(storage, process, epoch, pid, cache):
    """
    Make calls for data, shake out any errors
    There are 20 threshing process running in parallel
    They are each periodically terminated and respawned
    """
    handshake_bs, ping_bs, block_bs, reject_bs = [], [], [], []
    initialize_storage(storage)

    while True:
        try:
            node, nodes, static_nodes = get_node_info()
            storage["bw_depth"] = max(int(len(nodes) / 6), 1)

            black, white, blocktime, ping = handle_lists(storage, node)
            if node in black:
                raise ValueError("blacklisted")
            if node in white:
                raise ValueError("whitelisted")

            rpc, handshake_latency, handshake_max = wss_handshake(storage, node)
            utilizations = UTILIZATIONS if (time() - cache["begin"]) >= 100 else 1

            for util in range(utilizations):
                sleep(THRESH_PAUSE)
                ping_latency, ping_max = rpc_ping_latency(rpc, storage)
                block_latency, block_max, blocktime = rpc_block_latency(rpc, storage)

                (
                    set_timing,
                    ping_r,
                    block_r,
                    handshake_r,
                    ping_b,
                    block_b,
                    handshake_b,
                    reject_b,
                    ping_p,
                    block_p,
                    reject_p,
                    handshake_p,
                    ping_bs,
                    block_bs,
                    reject_bs,
                    handshake_bs,
                ) = calculate_metrics(
                    handshake_bs,
                    ping_bs,
                    block_bs,
                    reject_bs,
                    handshake_latency,
                    handshake_max,
                    ping_latency,
                    ping_max,
                    block_latency,
                    block_max,
                )

                last = rpc_pool_last(rpc, cache)
                now = to_iso_date(time())
                then = to_iso_date(time() - 3 * 86400)
                ids = [cache["asset_id"], cache["currency_id"]]
                precisions = [cache["asset_precision"], cache["currency_precision"]]

                (
                    descriptors,
                    cpu,
                    ram,
                    io_count,
                    m_last,
                    ping,
                    keys,
                ) = get_system_metrics(storage, process, cache)
                usd, btc, implied_btcusd, usd_dict, btc_dict = process_price_data(
                    m_last
                )

                print_status(locals())
                calculate_cross_rates()

                maven = {
                    "ping": (19 * storage["mean_ping"] + ping_latency) / 20,
                    "last": last,
                    "whitelist": white,
                    "blacklist": black,
                    "blocktime": blocktime,
                }
                nascent_trend(maven)
                winnow(storage, "whitelist", node)

                del maven, last, io_count, ram, cpu, keys, now

            sleep(0.0001)
            rpc.close()

        except Exception as error:
            try:
                if DEV:
                    print(trace(error))
                sleep(0.0001)
                rpc.close()
            except:
                pass
            try:
                msg = trace(error) + node
                if all(
                    x not in msg
                    for x in [
                        "ValueError",
                        "StatisticsError",
                        "result",
                        "timeout",
                        "SSL",
                    ]
                ):
                    if all(
                        x not in msg
                        for x in [
                            "WebSocketTimeoutException",
                            "WebSocketBadStatusException",
                            "WebSocketAddressException",
                            "ConnectionResetError",
                            "ConnectionRefusedError",
                        ]
                    ):
                        msg += "\n" + str(format_exc())
                if DEV:  # or ((time() - cache["begin"]) > 60):
                    print(msg)
                if "listed" not in msg:
                    race_append(doc="metanodelog.txt", text=msg)
                winnow(storage, "blacklist", node)
                del msg
            except:
                pass
            continue


def bifurcation(storage, cache):
    """
    Given 7 dictionaries of data (mavens) find the most common
    Send good (statistical mode) data to pricefeed_dex
    """
    print()
    validation_atmpt = 1
    while True:
        try:
            # initialize the dex_data dictionary
            dex_data = {}
            # initialize lists to sort data from each maven by key
            last = []
            whitelist = []
            blacklist = []
            blocktime = []
            pings = []
            # gather list of maven opinions from the nascent_trend()
            mavens = race_read(doc="mavens.txt")
            # sort maven data for statistical mode analysis by key
            len_m = len(mavens)
            for maven in mavens:
                # stringify lists for statistical mode of json text
                last.append(json_dump(maven["last"]))
                blocktime.append(maven["blocktime"])
                whitelist.append(maven["whitelist"])
                blacklist.append(maven["blacklist"])
                pings.append(maven["ping"])
            # the mean ping of the mavens is passed to the dex_data
            ping = int(1000 * sum(pings) / (len(pings) + 0.00000001)) / 1000.0
            ping = min(1, ping)
            # find the youngest bitshares blocktime in our dataset
            try:
                blocktime = max(blocktime)
                validation_atmpt = 1
            except Exception:
                print(f"\033[Avalidating the nascent trend... {validation_atmpt}")
                validation_atmpt += 1
                sleep(1)
                continue
            # get the mode of the mavens for the last, slicing progressively more recent
            # chunks if there are multiple modes
            slice_size = 0
            while slice_size < len_m:
                try:
                    last = mode(last[slice_size:])
                    break
                except Exception:
                    slice_size += 1
            else:
                # if there is no mode, we need more data
                sleep(1)
                continue
            last = json_load(last)

            # attempt a full whitelist and blacklist
            white_l = []
            for i in whitelist:
                white_l += i
            whitelist = list(set(white_l))[-storage["bw_depth"] :]
            black_l = []
            for i in blacklist:
                black_l += i
            blacklist = list(set(black_l))[-storage["bw_depth"] :]
            # if you made it this far without statistics error
            # truncate and rewrite the dex_data with curated data
            # Must be JSON type
            # 'STRING', 'INT', 'FLOAT', '{DICT}', or '[LIST]'
            dex_data["ping"] = ping  # FLOAT about 0.500
            dex_data["last"] = last  # DICT
            dex_data["whitelist"] = whitelist  # LIST
            dex_data["blacklist"] = blacklist  # LIST
            dex_data["blocktime"] = int(blocktime)  # INT
            dex_data["asset"] = cache["asset"]  # STRING SYMBOL
            dex_data["asset_id"] = cache["asset_id"]  # STRING A.B.C
            dex_data["asset_precision"] = int(cache["asset_precision"])  # INT
            dex_data["currency"] = cache["currency"]  # STRING SYMBOL
            dex_data["currency_id"] = cache["currency_id"]  # STRING A.B.C
            dex_data["pair"] = cache["pair"]  # STRING A:B
            # add index to dex_data
            dex_data["keys"] = list(dex_data.keys())
            # solitary process with write storage['access'] to pricefeed_dex.txt
            dex_data = json_dump(dex_data)
            race_write(doc="pricefeed_dex.txt", text=dex_data)
            print("pricefeed_dex.txt updated")

            storage["updates"].append(time())
            storage["updates"] = [t for t in storage["updates"] if (time() - t) < 60]

            sleep(BIFURCATION_PAUSE)  # take a deep breath
            # clear namespace
            del dex_data
            del mavens
            del maven
            del last
            del whitelist
            del blacklist
            del blocktime
            del len_m
            del black_l
            del white_l

        except Exception as error:  # wait a second and try again
            # common msg is "no mode statistics error"
            if DEV:
                msg = trace(error)
                print(msg)
                race_append(doc="pricefeed_dexlog.txt", text=msg)
            sleep(1)
            continue  # from top of while loop NOT pass through error


def get_cache(storage, cache, nodes):
    """
    Acquire and store asset ids, and asset precisions
    This is called once prior to spawning additional processes
    """
    storage["bw_depth"] = 10
    storage["updates"] = []

    def wwc():
        """
        Winnowing Websocket Connections...
        """
        print("\033c")
        # cache = logo(cache)
        print(
            it(
                "cyan",
                """
            +===============================+
              ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
              ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
              ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
                MARKET - PEGGED - ASSETS
            +===============================+

            The right of nullification is a natural right,
            which all admit to be a remedy against insupportable oppression.
                $$$ James Madison $$$

            If it had not been for the justice of our cause,
            and the consequent interposition of Providence,
            in which we had faith, we must have been ruined.
                $$$ Ben Franklin $$$

            Resistance and disobedience in economic activity
            is the most moral human action possible.
                $$$ Samuel E. Konkin III $$$
            """,
            )
        )
        print("")
        print(ctime(), "\n")
        print(wwc.__doc__, "\n")

    asset_ids, currency_ids = [], []
    asset_precisions, currency_precisions = [], []
    # trustless of multiple nodes
    wwc()
    while True:
        try:
            black = race_read(doc="blacklist.txt")
            white = race_read(doc="whitelist.txt")
            # switch nodes
            nodes = get_nodes()
            shuffle(nodes)
            node = nodes[0]
            print(it("green", "DEX: "), node)
            if node in black:
                raise ValueError("blacklisted")
            if node in white:
                raise ValueError("whitelisted")
            # reconnect and make calls
            rpc, _, _ = wss_handshake(storage, node)
            (
                asset_id,
                asset_precision,
                currency_id,
                currency_precision,
            ) = rpc_lookup_asset_symbols(rpc)
            # prepare for statistical mode of cache items
            asset_ids.append(asset_id)
            asset_precisions.append(asset_precision)
            currency_ids.append(json_dump(currency_id))
            currency_precisions.append(json_dump(currency_precision))
            # mode of cache
            if len(asset_ids) > 4:
                print(cache)
                try:
                    cache["begin"] = int(time())
                    cache["asset_id"] = mode(asset_ids)
                    cache["asset_precision"] = mode(asset_precisions)
                    cache["currency_id"] = json_load(mode(currency_ids))
                    cache["currency_precision"] = json_load(mode(currency_precisions))
                    enableTrace(False)
                    print_market(storage, cache)
                    winnow(storage, "whitelist", node)
                    break
                except BaseException:
                    winnow(storage, "blacklist", node)
                    continue
        except Exception as error:
            # print(trace(error))
            continue
    return storage, cache


def winnow(storage, list_type, node):  # DONE
    """
    Seperate good nodes from bad
    """
    if list_type == "blacklist":
        black = race_read(doc="blacklist.txt")
        if isinstance(black, list):
            if node in black:
                black.remove(node)
            black.append(node)
            black = black[-storage["bw_depth"] :]
            race_write(doc="blacklist.txt", text=black)
        else:
            race_write(doc="blacklist.txt", text=[node])
    if list_type == "whitelist":
        white = race_read(doc="whitelist.txt")
        if isinstance(white, list):
            if node in white:
                white.remove(node)
            white.append(node)
            white = white[-storage["bw_depth"] :]
            race_write(doc="whitelist.txt", text=white)
        else:
            race_write(doc="whitelist.txt", text=[node])
    try:
        del white
        del black
        del node
    except BaseException:
        pass


def latency_test(storage):
    """
    In loop, latency test the static list to produce nodes.txt
    Qualify round 1 = good chain id, 1000ms ping, 5000ms handshake
    All three ending suffixes are tested for each static list domain
    Only one of each suffix is allowed to pass
    latency() itself is a is a multiprocess child of spawn
    All tests done by latency() are multiprocess timeout wrapped
    """

    def test(node, signal, storage):
        """
        < 5 second hanshake
        < 1 second ping AND good chain id
        < 4.5 second blocktime
        """
        try:
            rpc, _, _ = wss_handshake(storage, node)
            rpc_ping_latency(rpc, storage)
            rpc_block_latency(rpc, storage)
            signal.value = 1  # if no exceptions pipe true response
        except BaseException:
            signal.value = 0

    def validate(unique):
        """
        remove suffixes for each domain, then remove duplicates
        """
        for item, unique_item in enumerate(unique):
            if unique_item.endswith("/"):
                unique[item] = unique_item[:-1]
        for item, unique_item in enumerate(unique):
            if unique_item.endswith("/ws"):
                unique[item] = unique_item[:-3]
        for item, unique_item in enumerate(unique):
            if unique_item.endswith("/wss"):
                unique[item] = unique_item[:-4]
        return sorted(list(set(unique)))

    def suffix(no_suffix):
        """
        add suffixes of each type for each validated domain
        """
        wss_suffix = [(i + "/wss") for i in no_suffix]
        ws_suffix = [(i + "/ws") for i in no_suffix]
        suffixed = no_suffix + wss_suffix + ws_suffix
        return sorted(suffixed)

    static_nodes = public_nodes()
    while True:
        start = time()
        whitelist = []
        blacklist = []
        suffixed_nodes = suffix(validate(static_nodes))
        for node in suffixed_nodes:
            # do not retest whitelisted domains with another suffix
            if validate([node])[0] not in validate(whitelist):
                # wrap test in timed multiprocess
                signal = Value("d", 0)
                t_process = Process(target=test, args=(node, signal, storage))
                t_process.daemon = False
                t_process.start()
                t_process.join(LATENCY_TIMEOUT)
                # kill hung process and blacklist the node
                if t_process.is_alive():
                    t_process.join()
                    t_process.terminate()
                    blacklist.append(node)
                # bad chain id, ping, handshake, or blocktime
                elif signal.value == 0:
                    blacklist.append(node)
                # good chain id, ping, handshake, and blocktime
                elif signal.value == 1:
                    # if domain is not already in list
                    whitelist.append(node)
        # nodes.txt is used as pricefeed_dex's primary universe
        race_write("nodes.txt", json_dump(whitelist))
        race_write("blacklist2.txt", json_dump(blacklist))
        # repeat latency testing periodically per LATENCY_REPEAT
        sleep(max(0, (LATENCY_REPEAT - (time() - start))))


def spawn(storage, cache):
    """
    Multiprocessing handler spawns all parallel processes
    """
    # initialize one latency testing process
    l_process = Process(target=latency_test, args=(storage,))
    l_process.daemon = False
    l_process.start()
    # initialize one bifurcation process
    b_process = Process(target=bifurcation, args=(storage, cache))
    b_process.daemon = False
    b_process.start()
    # initialize multiple threshing processes
    epoch = 0
    proc_id = 0
    multinode = {}
    for proc in range(PROCESSES):
        proc_id += 1
        multinode[str(proc)] = Process(
            target=thresh, args=(storage, proc, epoch, proc_id, cache)
        )
        multinode[str(proc)].daemon = False
        multinode[str(proc)].start()
        sleep(0.01)
    # kill and respawn threshing processes periodically for durability
    # even if anything gets hung pricefeed_dex always moves on
    # a = process of PROCESSES; b = respawn epoch; c = process id
    # every time a process is respawned it gets new process id
    while True:
        epoch += 1
        race_write(doc="pricefeed_dexlog.txt", text="")
        for proc in range(PROCESSES):
            proc_id += 1
            sleep(TIMEOUT / 2 + TIMEOUT * random())
            try:
                multinode[str(proc)].terminate()
            except Exception as error:
                msg = trace(error)
                print("terminate() WARNING", msg)
                race_append(doc="pricefeed_dexlog.txt", text=msg)
            try:
                multinode[str(proc)] = Process(
                    target=thresh, args=(storage, proc, epoch, proc_id, cache)
                )
                multinode[str(proc)].daemon = False
                multinode[str(proc)].start()
            except Exception as error:
                msg = trace(error)
                print("process() WARNING", msg)
                race_append(doc="pricefeed_dexlog.txt", text=msg)


def nascent_trend(maven):
    """
    Append data from recently polled node to vetted list of dictionaries
    """
    mavens = race_read(doc="mavens.txt")
    if isinstance(mavens, list):
        mavens.append(maven)
        mavens = mavens[-MAVENS:]
        race_write(doc="mavens.txt", text=json_dump(mavens))
    else:
        race_write(doc="mavens.txt", text=json_dump([maven]))
    del mavens


# HELPER FUNCTIONS
# ======================================================================
def calculate_cross_rates():
    feed = race_read("pricefeed_final.txt")
    if "feed" in feed:
        feed = feed["feed"]
    else:
        print("Feed not ready yet; skipping cross rates")
        return

    # Use all the BTS: prices
    feed = {k.split(":")[1]: v for k, v in feed.items() if k.startswith("BTS:")}

    # Initialize a dictionary to hold cross rates
    cross_rates = {}

    # Calculate cross rates
    for base_currency, base_price in feed.items():
        for quote_currency, quote_price in feed.items():
            if base_currency != quote_currency:
                # Calculate the cross rate
                cross_rate = base_price / quote_price
                cross_rates[f"{base_currency}/{quote_currency}"] = cross_rate

    race_write("honest_cross_rates.txt", cross_rates)


def print_market(storage, cache):
    """
    pricefeed_dex header containing with cached values
    """
    print("\033c")
    print_logo()
    print("")
    print(
        ctime(),
        it("purple", ("%.5f" % storage["access"])),
        "read",
        it("purple", ("%.1f" % storage["data_latency"])),
        "data",
    )
    print("==================================================")
    currencies = [
        (key, val, cache["currency_precision"][key])
        for key, val in cache["currency_id"].items()
    ]

    print("CURRENCIES: ", currencies)
    print("ASSET:      ", cache["asset"], cache["asset_id"], cache["asset_precision"])
    print("==================================================")
    print("")


def remove_chars(string, chars):
    """
    Return string without given characters
    """
    return "".join(c for c in string if c not in set(chars))


def precision(number, places):
    """
    String representation of float to n decimal places
    """
    return ("%." + str(places) + "f") % float(number)


def from_iso_date(date):
    """
    Unix epoch given iso8601 datetime
    """
    return int(timegm(strptime(str(date), "%Y-%m-%dT%H:%M:%S")))


def to_iso_date(unix):
    """
    iso8601 datetime given unix epoch
    """
    return datetime.utcfromtimestamp(int(unix)).isoformat()


def welcome(cache):
    """
    Announce version and print logo, log current local time
    """
    print("\033c")
    race_write(doc="pricefeed_dexlog.txt", text=str(ctime()))
    return cache


def version(cache):
    """
    Get version number from VERSION name
    Label terminal window
    """
    cache["version_number"] = "".join(item for item in VERSION if item in "0123456789.")
    stdout.write("\x1b]2;" + "Bitshares pricefeed_dex" + "\x07")  # terminal title bar
    return cache


def sign_in(cache):
    """
    skip sign in... install global "CURRENCIES"
    """
    cache["pair"] = {}
    cache["currency"] = {}
    cache["asset"] = ASSET

    for currency in CURRENCIES:
        cache["pair"][currency] = []
        cache["currency"][currency] = []
    for currency in CURRENCIES:
        cache["pair"][currency].append(cache["asset"] + ":" + currency)
        cache["currency"][currency].append(currency)
    return cache


def initialize():
    """
    Clear text IPC channels
    Initialize storage and cache
    """
    storage = {"data_latency": 0, "access": 0, "mean_ping": 0.5}
    now = int(time())
    cache = {"begin": now}
    if DEV:
        enableTrace(True)
    race_write(doc="blacklist.txt", text=json_dump([]))
    race_write(doc="whitelist.txt", text=json_dump([]))
    race_write(doc="pricefeed_dexlog.txt", text=json_dump(""))
    race_write(doc="pricefeed_dex.txt", text=json_dump({}))
    race_write(doc="mavens.txt", text=json_dump([]))
    race_write(doc="watchdog.txt", text=json_dump([now, now]))
    race_write(doc="nodes.txt", text=json_dump(public_nodes()))
    return storage, cache


def get_nodes():
    """
    Dynamic list if long enough else static list
    """
    nodes = race_read(doc="nodes.txt")
    if len(nodes) < MIN_NODES:
        nodes = public_nodes()
    return nodes


def pricefeed_dex():
    """
    Primary event backbone
    """
    storage, cache = initialize()
    cache = version(cache)
    cache = welcome(cache)
    cache = sign_in(cache)
    storage, cache = get_cache(storage, cache, get_nodes())
    spawn(storage, cache)


if __name__ == "__main__":
    pricefeed_dex()
