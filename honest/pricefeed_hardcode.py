"""
use this script to publish a feed with hard code
"""
from getpass import getpass
from pricefeed_final import publish_feed

# input prices here must include cny, btc, and usd rate
prices = {"feed": {"BTS:CNY": 0.126912, "BTS:BTC": 0.00000215, "BTS:USD": 0.0185317}}


name = input("\n\nBitshares DEX account name:\n\n")
wif = getpass("\n\nBitshares DEX wif:\n\n")
publish_feed(prices, name, wif)
