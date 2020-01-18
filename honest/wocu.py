"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

live forex rates scraped from wocu.com

litepresence2020
"""

# STANDARD PYTHON MODULES
from json import dumps as json_dumps

# THIRD PARTY MODULES
import requests

# PRICE FEED MODULES
from utilities import race_write, refine_data

URL = "http://54.154.247.217/wocutab.php"


def wocu(signal):
    """
    make api call for data, reformat to dict
    """
    try:
        raw = requests.get(URL, timeout=(6, 30)).text
        ret = (
            raw.split("<body>")[1]
            .split("</body>")[0]
            .split("<th style ='color:#50b5e0'>Currency</th>")[1]
            .split("</table>")[0]
        )
        ret = (
            ret.replace("<td style ='color:#50b5e0'>", "")
            .replace("</td></tr><tr align='center'>", ",")
            .replace("</td>", ",")
            .replace("</td>", ",")
            .split("USD")[2]
            .split(";</tr>")[0]
            .replace("</tr>", "")
        )
        ret = '["' + ret.strip(",").replace(",", '","') + '"]'
        json_ret = json_loads(ret)
        data = {}
        for idx, item in enumerate(json_ret):
            if item.isalpha():
                data["USD:" + item] = float(json_ret[idx + 2])
        data = refine_data(data)
        data = {k: v for k, v in data.items() if k not in ["USD:XAU"]}
        race_write("wocu_forex.txt", json_dumps(data))
        signal.value = 1
    except:
        print("wocu failed to load")


if __name__ == "__main__":

    wocu(None)
