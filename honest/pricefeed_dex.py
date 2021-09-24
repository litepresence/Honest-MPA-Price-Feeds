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

# STANDARD PYTHON MODULES
from time import time, sleep, ctime, strptime
from random import shuffle, random
from multiprocessing import Process, Value
from json import loads as json_load
from json import dumps as json_dump
from traceback import format_exc
from datetime import datetime
from statistics import mode, median
from calendar import timegm
from sys import stdout
from os import popen
import os

# THIRD PARTY MODULES
from psutil import Process as psutil_Process
from websocket import create_connection as wss
from websocket import enableTrace

# HONEST PRICE FEED MODULES
from utilities import sigfig, it
from config_nodes import public_nodes

# ======================================================================
VERSION = "HONEST MPA DEX FEED 0.00000001"
# ======================================================================
DEV = False
COLOR = True
MAVENS = 1  # 7
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
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"
# ======================================================================

CURRENCIES = [
    "GDEX.BTC",
    "XBTSX.BTC",
    "GDEX.USDT",
    "XBTSX.USDT",
]
ASSET = "BTS"


# INTER PROCESS COMMUNICATION VIA TEXT
# ======================================================================
def bitshares_trustless_client():
    """
    Include this definition in your script to storage['access'] pricefeed_dex.txt
    Deploy your bot script in the same folder as pricefeed_dex.py
    """
    doc = PATH + "pipe/pricefeed_dex.txt"

    while True:
        try:
            with open(doc, "r") as handle:
                ret = handle.read()  # .replace("'",'"')
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


def race_append(doc="", text=""):  # DONE
    """
    Concurrent Append to File Operation
    """
    doc = PATH + "pipe/" + doc
    iteration = 0
    while True:
        sleep(0.0001 * iteration ** 2)
        iteration += 1
        try:
            if iteration > 10:
                break
            with open(doc, "a+") as handle:
                handle.write(text)
                handle.close()
                break
        except Exception as error:
            print(trace(error))
            try:
                handle.close()
            except BaseException:
                pass
        finally:
            try:
                handle.close()
            except BaseException:
                pass


def race_write(doc="", text=""):  # DONE
    """
    Concurrent Write to File Operation
    """
    doc = PATH + "pipe/" + doc
    if not isinstance(text, str):
        text = str(text)
    iteration = 0
    while True:
        sleep(0.0001 * iteration ** 2)
        iteration += 1
        try:
            with open(doc, "w+") as handle:
                handle.write(text)
                handle.close()
                break
        except Exception as error:
            print(trace(error))
            try:
                handle.close()
            except BaseException:
                pass
        finally:
            try:
                handle.close()
            except BaseException:
                pass


def race_read(doc=""):
    """
    Concurrent Read from File Operation
    """
    doc = PATH + "pipe/" + doc
    iteration = 0
    while True:
        sleep(0.0001 * iteration ** 2)
        iteration += 1
        try:
            with open(doc, "r") as handle:
                ret = handle.read().replace("'", '"')
                handle.close()
                try:
                    ret = json_load(ret)
                except BaseException:
                    try:
                        ret = ret.split("]")[0] + "]"
                        ret = json_load(ret)
                    except BaseException:
                        try:
                            ret = ret.split("}")[0] + "}"
                            ret = json_load(ret)
                        except BaseException:
                            print("race_read() failed %s" % str(ret))
                            ret = {} if "{" in ret else []
                break
        except FileNotFoundError:
            ret = []
        except Exception as error:
            if DEV:
                print(trace(error))
            try:
                handle.close()
            except BaseException:
                pass
        finally:
            try:
                handle.close()
            except BaseException:
                pass
    return ret


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
        print(22222)
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


# STATISTICAL DATA CURATION
# ======================================================================
def thresh(storage, process, epoch, pid, cache):
    """
    Make calls for data, shake out any errors
    There are 20 threshing process running in parallel
    They are each periodically terminated and respawned
    """
    handshake_bs = []
    ping_bs = []
    block_bs = []
    reject_bs = []
    storage["access"] = 0
    storage["data_latency"] = 0
    while True:
        storage["mean_ping"] = 0.5
        try:
            nodes = get_nodes()
            static_nodes = public_nodes()
            shuffle(nodes)
            node = nodes[0]
            storage["bw_depth"] = max(int(len(nodes) / 6), 1)
            # CHECK BLACK AND WHITE LISTS
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
            except BaseException:
                pass
            if node in black:
                raise ValueError("blacklisted")
            if node in white:
                raise ValueError("whitelisted")
            # connect to websocket
            rpc, handshake_latency, handshake_max = wss_handshake(storage, node)
            # use each node several times
            utilizations = UTILIZATIONS
            if (time() - cache["begin"]) < 100:
                utilizations = 1
            for util in range(utilizations):
                sleep(THRESH_PAUSE)
                # Database calls w/ data validations
                ping_latency, ping_max = rpc_ping_latency(rpc, storage)
                block_latency, block_max, blocktime = rpc_block_latency(rpc, storage)
                set_timing = "                  " + "speed/max/ratio/cause/rate"
                if handshake_max == 5:
                    set_timing = "                  " + it(
                        "cyan", "RESOLVING MEAN NETWORK SPEED"
                    )
                # timing analysis for development
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
                ping_b = str(ping_b).ljust(7)
                block_b = str(block_b).ljust(7)
                handshake_b = str(handshake_b).ljust(7)
                reject = "".ljust(7)
                if reject_b:
                    reject = it("cyan", "X".ljust(7))
                optimizing = it("cyan", "OPTIMIZING".ljust(7))
                if (time() - cache["begin"]) > 200:
                    optimizing = "".ljust(7)
                # last, history, orderbook, balances, orders
                last = rpc_last(rpc, cache)
                # print(last)
                now = to_iso_date(time())
                then = to_iso_date(time() - 3 * 86400)
                ids = [cache["asset_id"], cache["currency_id"]]
                precisions = [cache["asset_precision"], cache["currency_precision"]]
                # CPU, RAM, io_count data REQUIRES MODULE INSTALL
                try:
                    proc = psutil_Process()
                    descriptors = proc.num_fds()
                    usage = (
                        "grep 'cpu ' /proc/stat | awk "
                        + "'{usage=($2+$4)*100/($2+$4+$5)}"
                        + " END {print usage }' "
                    )
                    cpu = "%.3f" % (float(popen(usage).readline()))
                    ram = "%.3f" % (100 * float(proc.memory_percent()))
                    io_count = list(proc.io_counters())[:2]
                except Exception as error:
                    if DEV:
                        print(trace(error))
                metanode = bitshares_trustless_client()
                m_last = {}
                ping = 0.5
                keys = ["bifurcating the metanode...."]
                try:
                    keys = metanode["keys"]
                    ping = storage["mean_ping"] = metanode["ping"]
                    m_last = metanode["last"]
                except BaseException:
                    pass
                del metanode
                try:
                    cex = race_read("pricefeed_cex.txt")
                    forex = race_read("pricefeed_forex.txt")
                    final = race_read("pricefeed_final.txt")
                except:
                    pass
                # aggregate gateway:bts data
                usds = []
                btcs = []
                usd_dict = {}
                btc_dict = {}
                try:
                    for key, val in m_last.items():
                        if "BTC" in key:
                            btcs.append(val)
                            btc_dict[key] = val
                        elif "USD" in key:
                            usds.append(val)
                            usd_dict[key] = val
                    # eliminate outliers
                    usd = median(usds)
                    btc = median(btcs)
                    # calculate the gateway btcusd for reference only
                    implied_btcusd = usd / btc
                except:
                    print(it("cyan", "WARN: GATHERING PRICES"))
                sceletus_output = {}
                try:
                    sceletus_output = race_read(doc="sceletus_output.txt")
                except:
                    pass
                try:
                    honest_cross_rates = race_read(doc="honest_cross_rates.txt")
                except:
                    pass

                runtime = int(time()) - cache["begin"]
                # storage['bw_depth'] = max(int(len(nodes) / 6), 1)
                if (len(white) < storage["bw_depth"]) or (
                    len(black) < storage["bw_depth"]
                ):
                    alert = it("cyan", "    BUILDING BLACK AND WHITE LISTS")
                else:
                    alert = ""
                if nodes == static_nodes:
                    alert += " ::WARN:: USING STATIC NODE LIST"
                upm = 0
                try:
                    upm = len(storage["updates"])
                except:
                    pass
                # in the event data passes all tests, then:
                # print, winnow the node, and nascent trend the maven
                print_market(storage, cache)
                print(keys)
                print("")
                print("runtime:epoch:pid:upm", it("green", runtime), epoch, pid, upm)
                try:
                    print(
                        "fds:processes        ", descriptors, process, "of", PROCESSES
                    )
                except BaseException:
                    print("processes:           ", process, "of", PROCESSES)
                try:
                    print("cpu:ram:io_count     ", cpu, ram, io_count)
                except BaseException:
                    pass
                print("utilization:node     ", str(util + 1).ljust(3), node)
                print(
                    "total:white:black    ",
                    len(static_nodes),
                    len(nodes),
                    len(white),
                    len(black),
                    alert,
                )
                print(set_timing)
                print(
                    "block latency        ",
                    "%.2f %.1f %.1f %s %.2f"
                    % (block_latency, block_max, block_r, block_b, block_p),
                )
                print(
                    "handshake            ",
                    "%.2f %.1f %.1f %s %.2f"
                    % (
                        handshake_latency,
                        handshake_max,
                        handshake_r,
                        handshake_b,
                        handshake_p,
                    ),
                )
                print(
                    "ping                 ",
                    "%.2f %.1f %.1f %s %.2f"
                    % (ping_latency, ping_max, ping_r, ping_b, ping_p),
                )
                print(
                    "mean ping            ",
                    (it("purple", ("%.3f" % ping))),
                    "       %s %.2f" % (reject, reject_p),
                    optimizing,
                )
                print("")
                try:
                    print(
                        "DEX BTS:BTC",
                        it("cyan", ("%.16f" % btc)),
                        it("purple", btc_dict),
                    )  # json_dump(btc_dict, indent=0, sort_keys=True)))
                    print(
                        "DEX BTS:USD", "%.16f" % usd, it("purple", usd_dict),
                    )
                    print(
                        "DEX BTC:USD",
                        it("yellow", ("%.4f" % implied_btcusd)),
                        "(IMPLIED)",
                    )
                except:
                    pass
                try:
                    for key, val in cex.items():
                        print(
                            "CEX",
                            key,
                            it("cyan", ("%.8f" % val["median"])),
                            {k: ("%.8f" % v["last"]) for k, v in val["data"].items()},
                        )
                    print(
                        "\nFOREX  "
                        + "inverse ::: pair ::: min ::: mid ::: max ::: qty ::: source"
                    )
                    for key, val in forex["medians"].items():
                        fxdata = [i[0] for i in forex["aggregate"][key]]
                        print(
                            it("cyan", str(sigfig(1 / val[0])).rjust(12)),
                            it("green", key),
                            str(min(fxdata)).ljust(11),
                            it("cyan", str(val[0]).ljust(11)),
                            str(max(fxdata)).ljust(11),
                            len(fxdata),
                            " ".join([i[1][:4] for i in forex["aggregate"][key]]),
                        )
                    print(
                        "FINAL INVERSE",
                        {k: sigfig(v) for k, v in final["inverse"].items()},
                    )
                    print("FINAL FEED", it("green", final["feed"]))
                    print("FEED CLOCK", it("yellow", final["time"]))
                    try:
                        print("HONEST CROSS RATES", honest_cross_rates)
                    except:
                        pass
                    try:
                        print(
                            "SCELETUS  ", it("purple", sceletus_output),
                        )
                    except:
                        pass
                    stale = time() - final["time"]["unix"]
                    if stale > 4000:
                        print(
                            it("red", f"WARNING YOUR FEED IS STALE BY {stale} SECONDS")
                        )
                except:
                    pass

                # send the maven dictionary to nascent_trend()
                # Must be JSON type
                # 'STRING', 'INT', 'FLOAT', '{DICT}', or '[LIST]'
                maven = {}
                maven["ping"] = (19 * storage["mean_ping"] + ping_latency) / 20  # FLOAT
                maven["last"] = last  # precision() STRING
                maven["whitelist"] = white  # LIST
                maven["blacklist"] = black  # LIST
                maven["blocktime"] = blocktime  # INT
                nascent_trend(maven)
                # winnow this node to the whitelist
                winnow(storage, "whitelist", node)
                # clear namespace
                del maven
                del last
                del io_count
                del alert
                del ram
                del cpu
                del keys
                del now
                del runtime
                del descriptors
                del proc
            try:
                sleep(0.0001)
                rpc.close()
            except Exception as error:
                if DEV:
                    print(trace(error))
            continue
        except Exception as error:
            try:
                if DEV:
                    print(trace(error))
                sleep(0.0001)
                rpc.close()
            except BaseException:
                pass
            try:
                msg = trace(error) + node
                if (
                    ("ValueError" not in msg)
                    and ("StatisticsError" not in msg)
                    and ("result" not in msg)
                    and ("timeout" not in msg)
                    and ("SSL" not in msg)
                ):
                    if (
                        ("WebSocketTimeoutException" not in msg)
                        and ("WebSocketBadStatusException" not in msg)
                        and ("WebSocketAddressException" not in msg)
                        and ("ConnectionResetError" not in msg)
                        and ("ConnectionRefusedError" not in msg)
                    ):
                        msg += "\n" + str(format_exc())
                if DEV:  # or ((time() - cache["begin"]) > 60):
                    print(msg)
                if "listed" not in msg:
                    race_append(doc="metanodelog.txt", text=msg)
                winnow(storage, "blacklist", node)
                del msg
            except BaseException:
                pass
            continue


def bifurcation(storage, cache):
    """
    Given 7 dictionaries of data (mavens) find the most common
    Send good (statistical mode) data to pricefeed_dex
    """
    while True:
        try:
            sleep(BIFURCATION_PAUSE)  # take a deep breath
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
            for i in range(len_m):
                maven = mavens[i]
                last.append(json_dump(maven["last"]))
                blocktime.append(maven["blocktime"])
                whitelist.append(maven["whitelist"])
                blacklist.append(maven["blacklist"])
                pings.append(maven["ping"])
                # stringify lists for statistical mode of json text
            # the mean ping of the mavens is passed to the dex_data
            ping = int(1000 * sum(pings) / (len(pings) + 0.00000001)) / 1000.0
            ping = min(1, ping)
            # find the youngest bitshares blocktime in our dataset
            try:
                blocktime = max(blocktime)
            except BaseException:
                print("validating the nascent trend...")
                continue
            # get the mode of the mavens for each metric
            # allow 1 or 2 less than total & most recent for mode
            # accept "no mode" statistics error as possibility
            try:
                last = json_load(mode(last))
            except BaseException:
                try:
                    last = mode(last[-(len_m - 1) :])
                except BaseException:
                    last = mode(last[-(len_m - 2) :])

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
    while True:
        try:
            wwc()
            black = race_read(doc="blacklist.txt")
            white = race_read(doc="whitelist.txt")
            # switch nodes
            nodes = get_nodes()
            shuffle(nodes)
            node = nodes[0]
            print(node)
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
            print(trace(error))
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
def print_logo():
    """
    +===============================+
      ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
      ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
      ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
        MARKET - PEGGED - ASSETS
    +===============================+
    """
    print(it("green", print_logo.__doc__))


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


def trace(error):
    """
    Stack trace upon exception
    """
    msg = str(type(error).__name__) + str(error.args)
    if DEV:
        msg += str(format_exc()) + " " + ctime()
    return msg


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
