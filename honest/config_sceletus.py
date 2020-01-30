"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

litepresence2020


enter your sceletus settings here
the script will build combinations matrix between "currencies" and "honest_assets"
set "honest_to_honest" to True to sceletus the intra HONEST markets
use "exclude_pairs" in format "HONEST.BTC:CNY" to remove markets from matrix
return must be a legitimate python dictionary

total markets to sceletus will be

(len(currencies) * len(honest_assets)) + intra honest pairs

markets will be built in format ASSET:CURRENCY such

BUYING account needs to be funded with each CURRENCY
SELLING account needs to be funded with each ASSET

if you set honest_to_honest to True both accounts will need ASSETS

the MPA's to be sceletus'd should always be in the "honest_assets" group

bitassets such as USD, CNY, BTC should NOT have the "bit" prefix
"""

def config_sceletus():
    """  
    SAMPLE:
    
    return {
        "currencies": ["BTS", "CNY", "USD", "GDEX.BTC", "BTC", "RUDEX.BTC"],
        "honest_assets": ["HONEST.CNY", "HONEST.USD", "HONEST.BTC"],
        "honest_to_honest": False,
        "exclude_pairs": [],  # currency:asset,
    }
    """
    
    return {
        "currencies": ["BTS", "CNY", "USD", "GDEX.BTC"], 
        "honest_assets": ["HONEST.CNY"], 
        "honest_to_honest": False,
        "exclude_pairs": [], 
    }
