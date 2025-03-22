# fmt: off
EXCHANGES = {
    "ADA:BTC":  ['binance', 'bitfinex',           'bitstamp',          'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin',            'mexc',               'poloniex', 'upbit', 'xt'],
    "ALGO:BTC": ['binance',                                   'bybit', 'coinbase', 'coinex', 'cryptocom',           'hitbtc',        'kraken', 'kucoin', 'latoken',                                  'upbit',     ],
    "ATOM:BTC": ['binance',             'bitget',                      'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc',        'kraken', 'kucoin', 'latoken', 'mexc',               'poloniex', 'upbit',     ],
    "BTC:USD":  ['binance', 'bitfinex',           'bitstamp',          'coinbase',           'cryptocom',                            'kraken',                              'okx', 'p2b',                          ],
    "BTC:USDT": ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'latoken', 'mexc', 'okx', 'p2b', 'poloniex', 'upbit', 'xt'],
    "BTS:USDT": ['binance',                                                                               'gateio',                                      'latoken', 'mexc',               'poloniex',              ],
    "DOT:BTC":  ['binance',                                   'bybit', 'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken', 'kucoin', 'latoken', 'mexc',               'poloniex', 'upbit',     ],
    "EOS:BTC":  ['binance', 'bitfinex',                                'coinbase', 'coinex',                        'hitbtc',                  'kucoin', 'latoken', 'mexc',               'poloniex', 'upbit', 'xt'],
    "ETH:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'latoken', 'mexc', 'okx',        'poloniex', 'upbit', 'xt'],
    "FIL:BTC":  ['binance',                                            'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken',                                            'poloniex', 'upbit', 'xt'],
    "LTC:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit', 'coinbase', 'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'latoken', 'mexc', 'okx', 'p2b', 'poloniex',          'xt'],
    "SOL:BTC":  ['binance', 'bitfinex', 'bitget',             'bybit', 'coinbase', 'coinex', 'cryptocom',           'hitbtc', 'htx', 'kraken',                      'mexc', 'okx',        'poloniex', 'upbit', 'xt'],
    "XLM:BTC":  ['binance', 'bitfinex',           'bitstamp', 'bybit', 'coinbase', 'coinex',              'gateio', 'hitbtc',        'kraken', 'kucoin', 'latoken', 'mexc',        'p2b', 'poloniex', 'upbit', 'xt'],
    "XMR:BTC":  ['binance', 'bitfinex',                                            'coinex',                        'hitbtc',        'kraken', 'kucoin', 'latoken',                       'poloniex',              ],
    "XRP:BTC":  ['binance', 'bitfinex', 'bitget', 'bitstamp', 'bybit',             'coinex', 'cryptocom', 'gateio', 'hitbtc', 'htx', 'kraken', 'kucoin', 'latoken', 'mexc',               'poloniex', 'upbit', 'xt'],
}
# fmt: on
BLACKLIST = ["binance", "bybit"]
EXCHANGES = {k: [i for i in v if i not in BLACKLIST] for k, v in EXCHANGES.items()}
