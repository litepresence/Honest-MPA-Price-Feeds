"""
CANCEL ALL ORDERS IN ALL MARKETS

litepresence2020
"""

from json import dumps as json_dumps
from json import loads as json_loads
from getpass import getpass
import time

from pricefeed_sceletus import reconnect
from dex_manual_signing import broker
from utilities import race_read_json, it


def wss_query(rpc, params):
    """
    Send and receive websocket requests
    """
    query = json_dumps({"method": "call", "params": params, "jsonrpc": "2.0", "id": 1})
    rpc.send(query)
    ret = json_loads(rpc.recv())
    try:
        return ret["result"]  # if there is result key take it
    except BaseException:
        return ret


def rpc_open_orders(rpc, account_name):
    """
    return a list of open orders, for one account, in ALL MARKETS
    """
    ret = wss_query(rpc, ["database", "get_full_accounts", [[account_name], "false"]])
    try:
        limit_orders = ret[0][1]["limit_orders"]
    except:
        limit_orders = []
    return [order["id"] for order in limit_orders]


def rpc_account_id(rpc, account_name):
    """
    given an account name return an account id
    """
    ret = wss_query(rpc, ["database", "lookup_accounts", [account_name, 1]])
    return ret[0][1]


def main():
    """
    primary event circuit
    """
    nodes = race_read_json(doc="nodes.txt")

    print("\033c")
    print("\n\nCANCEL ALL OPEN ORDERS IN ALL DEX MARKETS\n\n")
    account_name = input("\n  Bitshares" + it("yellow", " AGENT NAME:\n\n           "))
    rpc = reconnect(None)
    account_id = rpc_account_id(rpc, account_name)
    print("\n\n", account_name, account_id, "\n\n")
    orders = rpc_open_orders(rpc, account_name)
    orders = list(set(orders))
    orders.sort()
    if orders:
        print(orders, "\n\n")
        user_resp = input("proceed to cancel these orders? y/n ").lower()
        if user_resp == "y":
            wif = getpass("\n  Bitshares" + it("yellow", " AGENT WIF:\n           "))
            print("           *****************")
            time.sleep(2)
            order = {
                "edicts": [{"op": "cancel", "ids": orders},],
                "header": {
                    "asset_id": "1.3.1",  # placeholder
                    "currency_id": "1.3.1",  # placeholder
                    "asset_precision": 5,  # placeholder
                    "currency_precision": 5,  # placeholder
                    "account_id": account_id,
                    "account_name": account_name,
                    "wif": wif,
                },
                "nodes": nodes,
            }

            broker(order)
    else:
        print("\n\nThere are no open orders to cancel\n\n")


def cancel_all_markets(account_name, wif):
    """
    clone of main for importation as a module within botscript
    acts in triplicate in case first two nodes report bad data
    """
    nodes = race_read_json(doc="nodes.txt")
    for _ in range(3):
        rpc = reconnect(None)
        account_id = rpc_account_id(rpc, account_name)
        orders = rpc_open_orders(rpc, account_name)
        orders = list(set(orders))
        orders.sort()
        if orders:
            order = {
                "edicts": [{"op": "cancel", "ids": orders},],
                "header": {
                    "asset_id": "1.3.1",  # placeholder
                    "currency_id": "1.3.1",  # placeholder
                    "asset_precision": 5,  # placeholder
                    "currency_precision": 5,  # placeholder
                    "account_id": account_id,
                    "account_name": account_name,
                    "wif": wif,
                },
                "nodes": nodes,
            }
            broker(order)


if __name__ == "__main__":

    main()
