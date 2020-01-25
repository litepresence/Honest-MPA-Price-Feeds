"""
this will be imported by various forex scripts which require api keys
"""

def api_keys():
    """
    enter your api keys here for additional data sources
    also enter your jsonbin.io key, id, and url here
    """
    return {
        "fscapi": "",
        "barchart": "",
        "worldcoinindex": "",
        "fxmarket": "",
        "apiforex": "",
        "fixerio": "",
        "openexchangerates":"",
        "currencyconverter": "",
        "jsonbin":{
            "key":"",
            "id":"",
            "url":"https://api.jsonbin.io/b/<your id here>/latest" # just for reference
        },
    }
