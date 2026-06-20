# fmt: off
EXCHANGES = {
    "ADA:BTC":  ['binance', 'bitfinex',           'bitstamp',          'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc',               'poloniex', 'upbit', 'xt'],
    "ALGO:BTC": ['binance',                                   'bybit', 'coinbase', 'coinex', 'cryptocom',           'hitbtc',        'kraken', 'kucoin',                                   'upbit',     ],
    "ATOM:BTC": ['binance',             'bitget',                      'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc',        'kraken', 'kucoin', 'mexc',               'poloniex', 'upbit',     ],
    "BTC:USD":  ['binance', 'bitfinex',           'bitstamp',          'coinbase',           'cryptocom',                            'kraken',                   'okx', 'p2b',                          ],
    "BTC:USDT": ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc', 'okx', 'p2b', 'poloniex', 'upbit', 'xt'],
    "BTS:USDT": ['binance',                                                                               'gateio',                                      'mexc',               'poloniex',              ],
    "DOT:BTC":  ['binance',                                   'bybit', 'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken', 'kucoin', 'mexc',               'poloniex', 'upbit',     ],
    "EOS:BTC":  ['binance',                                                        'coinex',                        'hitbtc',                  'kucoin', 'mexc',                           'upbit',     ],
    "EOS:USDT": [           'bitfinex',                                            'coinex',                        'hitbtc',                  'kucoin', 'mexc',                           'upbit',     ],
    "ETH:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc', 'okx',        'poloniex', 'upbit', 'xt'],
    "FIL:BTC":  ['binance',                                            'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken',                                 'poloniex', 'upbit', 'xt'],
    "FIL:USDT": ['binance', 'bitfinex', 'bitget',             'bybit',             'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx',           'kucoin', 'mexc', 'okx',        'poloniex', 'upbit', 'xt'],
    "LTC:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc', 'okx', 'p2b', 'poloniex',          'xt'],
    "SOL:BTC":  ['binance', 'bitfinex', 'bitget',             'bybit', 'coinbase', 'coinex', 'cryptocom',           'hitbtc', 'htx', 'kraken',           'mexc', 'okx',        'poloniex', 'upbit', 'xt'],
    "XLM:BTC":  ['binance', 'bitfinex',           'bitstamp', 'bybit', 'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken', 'kucoin', 'mexc',        'p2b', 'poloniex', 'upbit', 'xt'],
    "XMR:BTC":  ['binance', 'bitfinex',                                            'coinex',                        'hitbtc',        'kraken', 'kucoin',                       'poloniex',              ],
    "XMR:USDT": ['binance', 'bitfinex',                                            'coinex',                        'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc',               'poloniex',          'xt'],
    "XRP:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit',             'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'mexc',               'poloniex', 'upbit', 'xt'],
}
# fmt: on
BLACKLIST = ["binance", "bybit"]
EXCHANGES = {k: [i for i in v if i not in BLACKLIST] for k, v in EXCHANGES.items()}
