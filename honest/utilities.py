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
import os
import time
from json import loads as json_loads
from multiprocessing import Process, Value

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


def sigfig(price):
    """
    format price to max 8 significant figures, return as float
    """
    return float("{:g}".format(float("{:.8g}".format(price))))


def race_write(doc="", text=""):
    """
    Concurrent Write to File Operation
    """
    text = str(text)
    i = 0
    doc = PATH + "pipe/" + doc
    while True:
        try:
            time.sleep(0.05 * i ** 2)
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
            time.sleep(0.05 * i ** 2)
            i += 1
            with open(doc, "r") as handle:
                data = json_loads(handle.read())
                handle.close()
                return data
        except Exception as error:
            msg = str(type(error).__name__) + str(error.args)
            msg += " race_read_json()"
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
    """

    markets = ret_markets()
    data2 = {}
    for key, val in data.items():
        if key[-3:] == "USD":
            data2[key[-3:] + ":" + key[:3]] = 1 / val
        else:
            data2[key] = val
    data = {}
    for key, val in data2.items():
        if key[-3:] == "CNH":
            data["USD:CNY"] = val
        else:
            data[key] = val
    for key, val in data2.items():
        if key[-3:] == "RUR":
            data["USD:RUB"] = val
        else:
            data[key] = val
    data = dict(sorted(data.items()))
    data = {k: sigfig(v) for k, v in data.items()}
    data = {k: v for k, v in data.items() if k in markets}
    return data
