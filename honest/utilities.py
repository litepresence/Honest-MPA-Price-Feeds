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

import json
# STANDARD PYTHON MODULES
import math
import os
import re
import shutil
import subprocess
import sys
import time
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
        "default": 0,
        "white": 0,
    }
    return ("\033[%sm" % emphasis[style]) + str(text) + "\033[0m"


def at(
    spot: tuple,  # (col, row, width, height,)
    data: str,  # return to row, col and insert this multi line block text
):
    """
    format string w/ escape sequence
    to clear a terminal area at specific location of specified size
    and print a multi line text in that area
    """
    final = "".join(
        f"\033[{spot[1] + i};{spot[0]}H" + " " * spot[2] for i in range(spot[3])
    )
    for ldx, line in enumerate(data.split("\n")):
        final += f"\033[{spot[1]+ldx};{spot[0]}H" + line
    return final


def print_logo(output=True):
    """
    ╔═══════════════════════════════╗
    ║  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗ ║
    ║  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║  ║
    ║  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩  ║
    ║    MARKET - PEGGED - ASSETS   ║
    ╚═══════════════════════════════╝
    """
    if output:
        print(
            it(
                "green",
                "\n".join(
                    i.ljust(33).center(shutil.get_terminal_size().columns)
                    for i in print_logo.__doc__.replace("\n    ", "\n").split("\n")
                ),
            )
        )
    else:
        return "\n".join(
            i.ljust(33) for i in print_logo.__doc__.replace("\n    ", "\n").split("\n")
        )


def string_width(string):
    string = re.sub(r"\033\[.*?m", "", string)
    return max(map(len, string.split("\n")))


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
    # print(msg)
    return msg


def logger(msg, typ):
    spots = [PATH + "pipe/error_log.txt", "error_log.txt", "error_log"]
    idx = 0
    while True:  # keep trying until we log somewhere
        spot = spots[idx]
        try:
            with open(spot, "a") as handle:
                handle.write(
                    "---------------- "
                    + time.ctime()
                    + f" - error during {typ} "
                    + f"----------------\n{msg}\n\n"
                )
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


def file_operation(mode, doc="", text=None):
    """
    Generic File Operation
    """
    doc = os.path.join(PATH, "pipe", doc)
    i = 0
    while True:
        try:
            time.sleep(0.05 * i**2)
            i += 1
            with open(doc, mode) as handle:
                if mode == "a+":
                    handle.write(text)
                elif mode == "w+":
                    handle.write(str(text))
                elif mode == "r":
                    return json.loads(handle.read())
                break
        except Exception as error:
            msg = f"{type(error).__name__}: {error.args} in file_operation()"
            print(msg)
            if i > 10:  # Limit the number of retries
                break


def race_append(doc="", text=""):
    """
    Concurrent Append to File Operation
    """
    file_operation("a+", doc, text)


def race_write(doc="", text=""):
    """
    Concurrent Write to File Operation
    """
    file_operation("w+", doc, text)


def race_read_json(doc=""):
    """
    Concurrent Read JSON from File Operation
    """
    return file_operation("r", doc)


def race_read(doc=""):
    """
    Concurrent Read from File Operation
    """
    doc = PATH + "pipe/" + doc
    iteration = 0
    while True:
        time.sleep(0.0001 * iteration**2)
        iteration += 1
        try:
            with open(doc, "r") as handle:
                ret = handle.read().replace("'", '"')
                try:
                    return json.loads(ret)
                except json.JSONDecodeError:
                    # Attempt to fix malformed JSON
                    for fix in [
                        lambda x: x.split("]")[0] + "]",
                        lambda x: x.split("}")[0] + "}",
                    ]:
                        try:
                            ret = fix(ret)
                            return json.loads(ret)
                        except json.JSONDecodeError:
                            continue
                    print("race_read() failed to parse JSON: %s" % str(ret))
                    return {} if "{" in ret else []
        except FileNotFoundError:
            return []
        except Exception as error:
            print(trace(error))
            continue


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


def correct_pair(exchange, pair, reverse=False):
    asset, currency = pair.split("/")
    new_pair = []
    lookup = {
        "coinex": {"EOS": "A"},
        "hitbtc": {"EOS": "A"},
        "kucoin": {"EOS": "A"},
        "mexc": {"EOS": "A"},
        "xt": {"EOS": "A"}
    }
    if reverse:
        lookup = {k:{nt:t for t, nt in v.items()} for k, v in lookup.items()}
    for token in [asset, currency]:
        new_pair.append(lookup.get(exchange, {}).get(token, token))
    return "/".join(new_pair)


def new_git_commits(upstream_branch="origin/master"):
    # Fetch the latest changes from the upstream repository
    subprocess.run(["git", "fetch"], check=True)

    # Get the current branch name
    current_branch = (
        subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        .strip()
        .decode("utf-8")
    )

    # Compare the local branch with the upstream branch
    result = subprocess.run(
        ["git", "rev-list", "--count", f"{current_branch}..{upstream_branch}"],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        print("Error checking for new commits.")
        return

    new_commits_count = int(result.stdout.strip())

    return new_commits_count


def is_git_repo():
    try:
        # Run the git command to check if inside a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip() == "true"
    except subprocess.CalledProcessError:
        return False
