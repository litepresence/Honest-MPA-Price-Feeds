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
    A REQUEST:

    As sceletus'ing all the cross rates for any one individual would be to much to ask...
    I'm hopeful that feed producers will  be willing to split up the duties.
    for example... one of us takes the honest to honest pairs...
    another takes the honest to gateway.btc pairs...
    another takes honest to bitassets, etc.

    you will need about 500 BTS worth of each asset you will be sceletus'ing

    CURRENT RECOMMENDED SETTINGS:

    @litepresence 10 markets (intra honest pairings)

    return {
        "currencies": [],
        "honest_assets": ["HONEST.CNY", "HONEST.USD", "HONEST.BTC", "HONEST.XAU", "HONEST.XAG"],
        "honest_to_honest": True,
        "exclude_pairs": [],  # currency:asset,
    }

    @JBahai 5 markets (BTS to honest pairs)

    return {
        "currencies": ["BTS"],
        "honest_assets": ["HONEST.CNY", "HONEST.USD", "HONEST.BTC", "HONEST.XAU", "HONEST.XAG"],
        "honest_to_honest": False,
        "exclude_pairs": [],  # currency:asset,
    }

    @AmmarYousef 5 markets (bitBTC and GDEX.BTC to H.CNY, H.USD and H.BTC)

    return {
        "currencies": ["GDEX.BTC"],
        "honest_assets": ["HONEST.CNY", "HONEST.USD", "HONEST.BTC", "HONEST.XAU", "HONEST.XAG"],
        "honest_to_honest": False,
        "exclude_pairs": [],  # currency:asset,
    }

    @Don_Gabriel  9 markets bitCNY and bitUSD to H.CNY, H.USD and H.BTC

    return {
        "currencies": ["USD", "CNY", "BTC"],
        "honest_assets": ["HONEST.CNY", "HONEST.USD", "HONEST.BTC"],
        "honest_to_honest": False,
        "exclude_pairs": [],  # currency:asset,
    }

    @KenCode 8 markets
    return {
    "currencies": ["HONEST.BTC", "BTS"],
        "honest_assets": [
            "HONEST.ETH",
            "HONEST.XRP",
            "HONEST.ETH1",
            "HONEST.XRP1",
        ],
        "honest_to_honest": False,
        "exclude_pairs": [],
    }

    """

    # configuration for user @litepresence
    return {
        "currencies": ["BTS"],
        "honest_assets": [
            "HONEST.USD",
            "HONEST.BTC",
        ],
        "honest_to_honest": True,
        "exclude_pairs": [],  # currency:asset,
    }
