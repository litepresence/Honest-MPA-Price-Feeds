"""
this will be imported by various forex scripts which require api keys
"""


def config_apikeys():
    """
    enter your api keys here for additional data sources, get keys at:

    barchart.com
    fcsapi.com
    fixer.io
    free.currencyconverterapi.com
    fxmarketapi.com
    openexchangerates.org

    also enter your jsonbin.io key, id, and url here
    """
    return {
        "barchart": "",
        "fscapi": "",
        "fixerio": "",
        "currencyconverter": "",
        "fxmarket": "",
        "openexchangerates": "",
        "jsonbin": {
            "key": "",
            "id": "",
            "url": "https://api.jsonbin.io/b/<your id here>/latest",  # just for reference
        },
    }
