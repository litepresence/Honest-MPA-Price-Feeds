"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

data formatting and text pipe IPC utilities

litepresence2020
"""

# STANDARD PYTHON MODULES
import math
import os
import sys
import time
from json import loads as json_loads
from traceback import format_exc

# GLOBAL VARIABLES
ATTEMPTS = 3
PATH = str(os.path.dirname(os.path.abspath(__file__))) + "/"


def it(style, text):
    """
    Color printing in terminal
    """
    emphasis = {
        "red": 91,
        "green": 92,
        "yellow": 93,
        "blue": 94,
        "purple": 95,
        "cyan": 96,
    }
    return ("\033[%sm" % emphasis[style]) + str(text) + "\033[0m"


def block_print():
    """
    temporarily disable printing
    """
    sys.stdout = open(os.devnull, "w")


def enable_print():
    """
    re-enable printing
    """
    sys.stdout = sys.__stdout__


def trace(error):
    """
    print and return stack trace upon exception
    """
    msg = str(type(error).__name__) + "\n"
    msg += str(error.args) + "\n"
    msg += str(format_exc()) + "\n"
    print(msg)
    return msg


def logger(msg, typ):
    spots = [PATH + "pipe/error_log.txt", "error_log.txt", "error_log"]
    idx = 0
    while True: # keep trying until we log somewhere
        spot = spots[idx]
        try:
            with open(spot, "a") as handle:
                handle.write(f"---------------- error during {typ} ----------------\n{msg}\n\n")
                handle.close()
            break
        except:
            pass
        idx += 1
        idx %= 3


def sigfig(number, n=8):
    """
    :usage: print([sigfig(123456.789, i) for i in range(1, 10)])
    :param float(number):
    :param int(precision):
    :return:
    """
    return round(number, n - int(math.floor(math.log10(abs(number)))) - 1)


def race_write(doc="", text=""):
    """
    Concurrent Write to File Operation
    """
    text = str(text)
    i = 0
    doc = PATH + "pipe/" + doc
    while True:
        try:
            time.sleep(0.05 * i**2)
            i += 1
            with open(doc, "w+") as handle:
                handle.write(text)
                handle.close()
                break
        except Exception as error:
            msg = str(type(error).__name__) + str(error.args)
            msg += " race_write()"
            print(msg)
            try:
                handle.close()
            except:
                pass
            continue
        finally:
            try:
                handle.close()
            except:
                pass


def race_read_json(doc=""):
    """
    Concurrent Read JSON from File Operation
    """
    doc = PATH + "pipe/" + doc
    i = 0
    while True:
        try:
            time.sleep(0.05 * i**2)
            i += 1
            with open(doc, "r") as handle:
                data = json_loads(handle.read())
                handle.close()
                return data
        except Exception as error:
            msg = str(type(error).__name__) + str(error.args)
            msg += " race_read_json() " + doc
            print(msg)
            try:
                handle.close()
            except:
                pass
            continue
        finally:
            try:
                handle.close()
            except:
                pass


def from_iso_date(date):
    """
    returns unix epoch given YYYY-MM-DD
    """
    return int(time.mktime(time.strptime(str(date), "%Y-%m-%d %H:%M:%S")))


def ret_markets():
    """
    currently supported markets
    """
    return [
        "USD:CNY",
        "USD:EUR",
        "USD:GBP",
        "USD:RUB",
        "USD:JPY",
        "USD:KRW",
        "USD:XAG",
        "USD:XAU",
    ]


def refine_data(data):
    """
    ensure USD base
    sort dictionaries by key
    return only data in specified forex markets
    ensure values are all float format and to matching precision
    EPIC ONE LINER:
    return {
    k: v
    for k, v in {
      k: sigfig(v)
      for k, v in dict(
        sorted(
          {
            k if k[-3:] != "RUR" else "USD:RUB": v
            for k, v in {
              k if k[-3:] != "CNH" else "USD:CNY": v
              for k, v in {
                k[-3:] + ":" + k[:3] if k[-3:] == "USD" else k: v
                for k, v in {
                  k: 1 / v if k[-3:] == "USD" else v
                  for k, v in data.items()
                }.items()
              }.items()
            }.items()
          }.items()
        )
      ).items()
    }.items()
    if k in ret_markets()
    }
    """
    markets = ret_markets()
    # if pair is backwards, invert price
    data = {k: 1 / v if k[-3:] == "USD" else v for k, v in data.items()}
    # flip backwards pairs
    data = {k[-3:] + ":" + k[:3] if k[-3:] == "USD" else k: v for k, v in data.items()}
    # correct exchange eccentricities, CNH == CNY, RUR == RUB
    data = {k if k[-3:] != "CNH" else "USD:CNY": v for k, v in data.items()}
    data = {k if k[-3:] != "RUR" else "USD:RUB": v for k, v in data.items()}
    # sort the dict
    data = dict(sorted(data.items()))
    # ensure that all values are in float format and to the correct precision
    data = {k: sigfig(v) for k, v in data.items()}
    # ensure all pairs exist in configured pairs
    data = {k: v for k, v in data.items() if k in markets}
    return data
