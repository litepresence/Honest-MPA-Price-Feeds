# STANDARD PYTHON MODULES
import argparse
import ast
import glob
import json
import os
import sys
from collections import defaultdict
from datetime import datetime
from statistics import median
from time import mktime, strptime

# THIRD PARTY MODULES
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.style as mplstyle
import numpy as np

# HONEST PRICE FEED MODULES
from exchanges import EXCHANGES
from HONEST import gather_dex_btsbtc
from utilities import at, it, print_logo, sigfig, string_width, trace

mplstyle.use("dark_background")

CURRENCIES = [
    "GDEX.BTC",
    "XBTSX.BTC",
    "GDEX.USDT",
    "XBTSX.USDT",
    "IOB.XRP",
    "BTWTY.EOS",
]
ASSET = "BTS"


def dex_table(last):
    dex_string = ""
    # DEX
    gateways = sorted(list({i.split(".", 1)[0] for i in CURRENCIES}))
    gateway_tokens = sorted(list({i.split(".", 1)[1] for i in CURRENCIES}))

    # gateway_table is len(gateway_tokens)+1 rows and len(gateways)+1 columns
    table = [[" " * 16] + [i.ljust(10) for i in gateway_tokens]]
    for gateway in gateways:
        row = [gateway.ljust(10)] + [
            str(sigfig(last.get(f"{gateway}.{token}", -1), 4)).ljust(10)
            for token in gateway_tokens
        ]
        row = [
            (
                i
                if not any(j.isdigit() for j in i)
                else it("green", i) if "-1" not in i else it("yellow", i)
            )
            for i in row
        ]
        table.append(row)

    # table is now len(gateway_tokens)+1 columns and len(gateways)+1 rows
    table = np.array(table).T
    dex_string = "\n".join("".join(row) for row in table)
    return dex_string


def cex_table(cex):
    cex_string = ""
    # CEX
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
            (
                "white"
                if count >= 7
                else "yellow" if count >= 5 else "red" if count >= 2 else "cyan"
            ),
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
                            (
                                "green"
                                if i != -1 or rdx >= len(exchanges)
                                else (
                                    "red"
                                    if exchanges[rdx] in EXCHANGES.get(pairs[idx], [])
                                    else "yellow"
                                )
                            )
                            if row[0] != "median"
                            else "cyan"
                        ),
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
    return cex_string


def forex_table(forex):
    forex_string = ""
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
            (
                "white"
                if count >= 7
                else "yellow" if count >= 5 else "red" if count >= 2 else "cyan"
            ),
            coin.ljust(just_size),
        )
        for coin, count in zip(pairs, n_prices)
    )
    for rdx, row in enumerate(table):
        forex_string += "\n" + (
            (
                it("red", row[0].ljust(source_just))
                if all(i == -1 for i in row[1:])
                else (
                    row[0].ljust(source_just)
                    if row[0] != "median"
                    else it("purple", row[0].center(source_just))
                )
            )
            + "".join(
                [
                    it(
                        (
                            ("green" if i != -1 else "yellow")
                            if row[0] != "median"
                            else "cyan"
                        ),
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
    return forex_string


def final_table(final):
    final_string = ""

    table = []
    for pair, price in sorted(final["feed"].items()):
        table.append([pair, str(sigfig(price, 5))])
    just = max([max(map(len, row)) for row in table])
    final_string = "\n".join(
        "".join([row[0].ljust(just), it("cyan", row[1]).ljust(just)]) for row in table
    )

    return final_string


def calculate_btsbtc_price(cex, exchange):
    """
    Calculate BTS:BTC price for a given exchange using CEX data.
    """
    btsusd_price = cex["BTS:USDT"]["data"][exchange]
    btcusd_price = cex["BTC:USDT"]["data"][exchange]
    return btsusd_price * (1 / btcusd_price)


def acquire_btsbtc(data):
    btcusd = data["cex"]["BTC:USD"]["median"]

    # Get BTS:BTC prices from CEX
    cex_btsbtc_dict = {
        exchange: calculate_btsbtc_price(data["cex"], exchange)
        for exchange in data["cex"]["BTS:USDT"]["data"]
        if exchange in data["cex"]["BTC:USDT"]["data"]
    }

    agg_btsbtc_dict = {
        source: price / btcusd
        for price, source in data["forex"]["aggregate"].get("BTS:USD", [])
    }

    # Gather DEX BTS:BTC prices
    dex_btsbtc_list, dex_btsbtc_dict = gather_dex_btsbtc(data["dex"], data["cex"])

    agg_btsbtc_list = list(agg_btsbtc_dict.values())
    cex_btsbtc_list = list(cex_btsbtc_dict.values())

    # Finalize BTS:BTC by taking the median of all prices
    btsbtc = median(dex_btsbtc_list + cex_btsbtc_list + agg_btsbtc_list)
    return {
        k: sigfig(v, 4)
        for k, v in {
            **dex_btsbtc_dict,
            **cex_btsbtc_dict,
            **agg_btsbtc_dict,
        }.items()
    }


def print_status(data, log_file=""):
    """Handle all printing operations using the local variables of thresh"""
    logo_string = print_logo(False)
    print("\033c")
    if log_file:
        print(it("yellow", f" rendering {log_file} "))

    dex_string = dex_table(data["dex"]["last"])
    cex_string = cex_table(data["cex"])
    forex_string = forex_table(data["forex"])
    final_string = final_table(data)

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

        print("\n\n")
        print(it("cyan", "BTS:BTC sources:"), acquire_btsbtc(data))
        print("FEED CLOCK", it("yellow", data["time"]))
    except Exception as error:
        print(trace(error))
        print(
            it("red", "WARN:"),
            "Printing source tables failed!  Retrying on next thresh...",
        )


def parse_log(text):
    """
    price logs are written by HONEST.py as json.dumps;
    fall back to ast.literal_eval for older python-literal logs
    """
    try:
        return json.loads(text)
    except ValueError:
        return ast.literal_eval(text)


def log_date(path):
    """unix timestamp from a price_log_<ctime>.txt filename"""
    return mktime(
        strptime(os.path.basename(path).split("price_log_")[1].rsplit(".", 1)[0])
    )


def main():
    parser = argparse.ArgumentParser(
        description="Render and plot HONEST price feed logs.",
        epilog=(
            "With no arguments, every price_log_*.txt in the pipe directory "
            "is plotted as a BTS:BTC price history.  Give one or more price log "
            "files to render their source tables instead."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="price_log files to render as tables; default: plot all logs",
    )
    parser.add_argument(
        "-p",
        "--pipe",
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "pipe"),
        help="directory containing price_log_*.txt (default: pipe/ beside this script)",
    )
    parser.add_argument(
        "-s",
        "--save",
        metavar="FILE",
        help="save the plot to FILE (e.g. history.png) instead of opening a window",
    )
    parser.add_argument(
        "-l",
        "--latest",
        action="store_true",
        help="render only the most recent price log as tables",
    )
    parser.add_argument(
        "-n",
        "--count",
        type=int,
        metavar="N",
        help="render the N most recent price logs as tables",
    )
    args = parser.parse_args()

    # --latest / --count: render the most recent price log(s) as tables
    if args.latest or args.count:
        if args.count and args.count <= 0:
            print(it("red", "--count must be a positive integer"))
            sys.exit(1)

        pattern = os.path.join(args.pipe, "price_log_*")
        files = sorted(glob.glob(pattern), key=log_date)
        if not files:
            print(it("red", f"No price logs found in {args.pipe}"))
            print(
                "\nPrice logs are only written when the feed is run with "
                "--publish, e.g.\n\n    python HONEST.py --publish --headless\n\n"
                "with USERNAME and WIF set in the environment.\n"
                "Use --pipe DIR to look for logs kept somewhere else."
            )
            sys.exit(1)
        render_files = files[-1:] if args.latest else files[-args.count:]
        if args.files:
            print(it("yellow", "Ignoring explicit files; --latest/--count takes precedence"))
        for file in render_files:
            with open(file, "r") as handle:
                try:
                    data = parse_log(handle.read())
                except Exception as error:
                    print(it("red", f"{file} is not a valid price log: {trace(error)}"))
                    continue
            print_status(data, log_file=file)
        return

    if args.files:
        for file in args.files:
            if not os.path.isfile(file):
                parser.error(f"no such price log: {file}")
            with open(file, "r") as handle:
                try:
                    data = parse_log(handle.read())
                except Exception as error:
                    parser.error(f"{file} is not a valid price log: {trace(error)}")
            print_status(data, log_file=file)
        return

    plot_all(args.pipe, save=args.save)


def plot_all(pipe_dir, save=None):
    pattern = os.path.join(pipe_dir, "price_log_*")
    files = sorted(glob.glob(pattern), key=log_date)

    if not files:
        print(it("red", f"No price logs found in {pipe_dir}"))
        print(
            "\nPrice logs are only written when the feed is run with "
            "--publish, e.g.\n\n    python HONEST.py --publish --headless\n\n"
            "with USERNAME and WIF set in the environment.\n"
            "Use --pipe DIR to plot logs kept somewhere else."
        )
        sys.exit(1)

    datapoints = defaultdict(list)
    interactive = sys.stdout.isatty()
    print(f"Loading {len(files)} price logs from {pipe_dir}")

    for fdx, file in enumerate(files):
        if interactive:
            print(f"\r{fdx * 100 / len(files):.0f}% done", end="", flush=True)
        with open(file, "r") as handle:
            try:
                data = parse_log(handle.read())
                for key, value in acquire_btsbtc(data).items():
                    datapoints[key].append((log_date(file), value))
            except Exception as error:
                print(it("yellow", f"skipping {file}: {trace(error)}"))
    if interactive:
        print("\r100% done")

    if not datapoints:
        print(it("red", "No BTS:BTC datapoints could be read from the logs"))
        sys.exit(1)

    for label, data in sorted(datapoints.items()):
        dates = [datetime.fromtimestamp(date) for date, _ in data]
        prices = [price for _, price in data]
        plt.plot(dates, prices, label=label)

    plt.gca().xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(mdates.AutoDateLocator())
    )
    plt.title("BTS:BTC price feed history")
    plt.ylabel("BTS per BTC")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="best", fontsize="small")
    plt.gcf().autofmt_xdate()

    if save:
        plt.savefig(save, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {os.path.abspath(save)}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
