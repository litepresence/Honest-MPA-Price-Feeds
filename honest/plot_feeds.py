"""
A stand alone app for querying @sschiessl's custom API
to obtain historical price feed data for HONEST mpa's
"""
import json
import math
import time

# import necessary modules
from matplotlib import pyplot as plt
from requests import get

URL = "https://api.bitshares.ws/openexplorer/pricefeed"

PUBLISHER_IDS = {
    "1.2.581357": "@litepresence.com",
    "1.2.420263": "@Don_Gabriel",
    "1.2.20638": "@JBahai",
    "1.2.1691170": "@AmmarYousef",
    "1.2.1790240": "@christophersanborn",
}

ASSET_IDS = {
    "1.3.5641": "HONEST.CNY",
    "1.3.5649": "HONEST.USD",
    "1.3.5650": "HONEST.BTC",
    "1.3.5651": "HONEST.XAU",
    "1.3.5652": "HONEST.XAG",
    "1.3.5659": "HONEST.ETH",
    "1.3.5660": "HONEST.XRP",
    "1.3.5662": "HONEST.ETH1",
    "1.3.5661": "HONEST.XRP1",
}

DAYS = 275


def get_data():
    """
    Using multiple requests,
    get all the needed data from api.bitshares.ws
    and collate into format:

    {
        "1.3.x": {
                "1.2.x": [
                    [], # list of feed prices published
                    [] # list of respective block numbers
                ],
                ... # additional producers for this asset
        },
        ... # additional assets
    }

    """
    honest_feeds = {}
    # for all the HONEST mpa's
    for asset in list(ASSET_IDS.keys()):
        print(asset, ASSET_IDS[asset])
        asset_data = {}
        # for each feed producer
        for publisher in list(PUBLISHER_IDS.keys()):
            asset_data[publisher] = [[], []]
            # for every 4 day time block counting backwards from current
            failed = 0
            for period in range(int(math.ceil(DAYS / 4))):
                from_date = f"now-{min((period+1)*4, DAYS)}d"
                to_date = f"now-{period*4}d".replace("-0d", "")
                params = {
                    "asset": asset,
                    "publisher": publisher,
                    "from_date": from_date,
                    "to_date": to_date,
                }
                print(params, PUBLISHER_IDS[publisher])
                params.update({"as_list": True})
                # pause to respect api limits then make external request
                time.sleep(2)
                data = get(URL, params=params).json()
                try:
                    feed = list(data[ASSET_IDS[asset]].values())[0]["feed"][::-1]
                    blocks = data["blocks"][::-1]
                    # append the price feed data for this publisher and time period
                    asset_data[publisher][0] += feed
                    asset_data[publisher][1] += blocks
                    failed = 0
                except KeyError:
                    failed += 1
                    print(data["detail"], "failed", failed)
                    print(ASSET_IDS[asset], PUBLISHER_IDS[publisher])
                    # if 20 days of no data stop searching for this asset/producer
                    if failed == 5:
                        break

        honest_feeds[asset] = asset_data

    return honest_feeds


def plot_data(honest_feeds):
    """
    print a subplot of price feeds for each asset
    each subplot will contain a line for each producer
    """
    plt.figure()
    plot_num = 1
    for asset, publishers in honest_feeds.items():
        plt.subplot(len(list(honest_feeds.keys())), 1, plot_num)
        plt.ylabel(ASSET_IDS[asset])
        for publisher, feeds in publishers.items():
            plt.plot(
                feeds[1],
                feeds[0],
                label=(PUBLISHER_IDS[publisher] + " " + str(len(feeds[0]))),
            )
        plt.legend(loc="upper left")
        plot_num += 1
    plt.show()


def main():
    """
    gather price feeds for all producers of all HONEST assets
    write data to file
    print feeds in subplots per asset
    """
    print("\033c")
    print("GATHERING HONEST PRICE FEED HISTORICAL DATA...\n")
    honest_feeds = get_data()
    # print(honest_feeds, "\n")
    doc = str(int(time.time())) + "_" + str(DAYS) + ".txt"
    print("\nPRINTING DATA TO FILE:", doc, "\n")
    with open(doc, "w+") as handle:
        handle.write(json.dumps(honest_feeds))
    print("PLOTTING...\n")
    plot_data(honest_feeds)


if __name__ == "__main__":
    main()
