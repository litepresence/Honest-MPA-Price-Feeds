# STANDARD PYTHON MODULES
import time
from pprint import pprint
from json import dumps as json_dumps
from json import loads as json_loads
from multiprocessing import Process, Value

# THIRD PARTY MODULES
import requests
import cfscrape

# PRICE FEED MODULES
from utilities import it, sigfig, from_iso_date, race_write, race_read_json, refine_data

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
