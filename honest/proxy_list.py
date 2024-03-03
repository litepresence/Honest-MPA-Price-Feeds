"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+


Acquire a list of non US based socks5 proxy servers

litepresence + squidKid-deluxe 2024
"""

# STANDARD MODULES
import base64
import json
import random
import re
import socket
import threading
import time
from pprint import pprint
from statistics import StatisticsError, mode

# THIRD PATRY MODULES
import requests
import socks


def openproxyspace(proxy_list):
    """
    Web scrape a socks5 proxy list from openproxy.space
    """

    proxies = []
    url = "https://openproxy.space/list/socks5"
    try:
        ret = requests.get(url, timeout=10).text
        ret = (
            ret.replace(" ", "")
            .split("FRESHSOCKS5PROXYLIST")[3]
            .split(",data:")[1]
            .split(",added:")[0]
        )
        ret = ret.split("code")
        ret = [i for i in ret if "US" not in i and "CA" not in i and "UK" not in i]
        ret = [i.split(",active:")[0] for i in ret]
        ret = [i.split(",items:")[1] for i in ret[1:]]
        ret = [json.loads(i) for i in ret]
        proxies = [element for sublist in ret for element in sublist]
    except Exception as e:
        print(f"failed to fetch openproxy.space {e}")
    proxy_list.extend(proxies)


def proxyscrapecom(proxy_list):
    """
    Web scrape a socks5 proxy list from api.proxyscrape.com
    """
    url = "https://api.proxyscrape.com/v3/free-proxy-list/get"
    params = {
        "request": "displayproxies",
        "protocol": "socks5",
        "timeout": 15000,
        "proxy_format": "ipport",
        "format": "json",
    }
    proxies = []
    try:
        ret = requests.get(url, params=params, timeout=10)
        ret = ret.json()["proxies"]
        ret = [
            p
            for p in ret
            if "alive" in p and "ip_data" in p and "port" in p and "ip" in p
        ]
        proxies = [
            p["proxy"]
            for p in ret
            if p["alive"] and not (p["ip_data"]["countryCode"] in ["US", "CA", "UK"])
        ]
    except Exception as e:
        print(f"failed to fetch api.proxyscrape.com {e}")

    proxy_list.extend(proxies)


def freeproxycz(proxy_list):
    """
    Web scrape a socks5 proxy list from free-proxy.cz
    """
    uri = "http://free-proxy.cz/en/proxylist/country/all/socks5/ping/all/"
    proxies = []
    for page in range(5):
        try:
            url = uri + str(page + 1)
            ret = requests.get(url, timeout=10).text
            ret = ret.split('<table id="proxy_list">')[1]
            ret = ret.split("<tbody>")[1]
            ret = ret.split("</tbody>")[0]
            ret = ret.split("Base64.decode")
            ret = [
                i.split("/span")[0]
                for i in ret
                if "/span" in i
                and "United States" not in i
                and "Canada" not in i
                and "United Kingdom" not in i
            ]
            proxies = [
                base64.b64decode(i.split('"')[1]).decode("utf-8")
                + ":"
                + i.split('"')[6].split(">")[1].split("<")[0]
                for i in ret
            ]
            proxy_list.extend(proxies)
        except Exception as e:
            print(f"failed to fetch free-proxy.cz {e}")
            break


def freeproxyworld(proxy_list):
    """
    Web scrape a socks5 proxy list from freeproxy.world
    """
    uri = "https://www.freeproxy.world/?type=socks5&anonymity=&country=&speed=&port=&page="
    for page in range(5):
        try:
            page = str(page + 1)
            url = uri + page
            ret = requests.get(url, timeout=10).text
            ret = ret.replace("\n", "")
            ret = ret.split("<legend>Proxy List - By Free Proxy World</legend>")[1]
            ret = ret.split("<footer")[0]
            ret = ret.split('<td class="show-ip-div">')
            ret = [
                i
                for i in ret
                if "US" not in i and "CA" not in i and "UK" not in i and "port" in i
            ]
            ret = [i.split("</a>")[0] for i in ret]
            proxies = [i.split("<")[0] + ":" + i.split(">")[-1] for i in ret]
            proxy_list.extend(proxies)
        except Exception as e:
            print(f"failed to fetch freeproxy.world {e}")
            break


def socksproxynet(proxy_list):
    """
    Web scrape a socks5 proxy list from socks-proxy.net
    """

    url = "https://www.socks-proxy.net/"
    try:
        ret = requests.get(url, timeout=10).text
        ret = ret.split("<tr>")
        ret = [
            i.replace("</td>", "").replace(">", "").split("<td")
            for i in ret
            if "ago</td></tr>" in i
        ][:-1]
        proxies = [i[1] + ":" + i[2] for i in ret if i[3] not in ["US", "CA", "UK"]]
        proxy_list.extend(proxies)
    except Exception as e:
        print(f"failed to fetch socks-proxy.net {e}")


def proxylistdownload(proxy_list):
    """
    Web scrape a socks5 proxy list from proxy-list.download
    """
    try:
        url = "https://www.proxy-list.download/SOCKS4"
        ret = requests.get(url, timeout=10).text

        ret = ret.split("</span></td>")
        ret = [
            i.replace("\n", "").replace(" ", "").replace("</td>", "")
            for i in ret
            if "US" not in i and "CA" not in i and "UK" not in i and "country" in i
        ]
        proxies = [i.split("<td>")[1] + ":" + i.split("<td>")[2] for i in ret]

        proxy_list.extend(proxies)
    except Exception as e:
        print(f"failed to fetch proxy-list.download {e}")


def filter_broken_links(links):
    """
    Filter all links to be in

    xxx.xxx.xxx.xxx:0-36635

    format.
    """
    # Regular expression pattern for standard IP:Port format
    ip_port_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+$"
    filtered_links = []
    for link in links:
        # Check if the link matches the IP:Port pattern
        if re.match(ip_port_pattern, link) and int(link.split(":")[1]) <= 65535:
            filtered_links.append(link)
        else:
            print(f"Broken link detected and removed: {link}")

    return filtered_links


class ProxyManager:
    """
    Stateful proxy management class, including blacklisting of unsupported proxies and whitelisting
    of fast proxies.
    """

    def __init__(self):
        self.whitelist = []
        self.responses = []
        self.proxies = []
        self.blacklist = []

    def get_proxy_list(self):
        """
        Spawn thread to concurrently get all available proxy lists and merge them
        """
        # Create lists to store the results
        children = []

        # Loop through all lists
        for target in [
            proxyscrapecom,
            openproxyspace,
            freeproxycz,
            freeproxyworld,
            socksproxynet,
            proxylistdownload,
        ]:
            children.append(
                threading.Thread(target=target, args=(self.proxies,), daemon=True)
            )

        for child in children:
            child.start()

        for child in children:
            child.join()

        random.shuffle(self.proxies)

        # Eliminate duplicates and malformed servers
        self.proxies = filter_broken_links(list(set(self.proxies)))

    def make_request(self, proxy, *args, **kwargs):
        """
        Make request using a given SOCKS4 proxy, otherwise
        act as direct replacement for requests.get
        """
        try:
            # Set the SOCKS proxy server address and port
            proxy_host, proxy_port = proxy.split(":")

            # Create a SOCKS5 proxy connection
            socks.setdefaultproxy(socks.SOCKS4, proxy_host, int(proxy_port))
            socket.socket = socks.socksocket

            # Make the request using the requests library
            response = requests.get(
                *args, **kwargs, timeout=10
            )  # Set a timeout for the request

            # Check if the request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    # US-based
                    if isinstance(data, dict) and data.get("code", None) == 0:
                        self.blacklist.append(proxy)
                        return
                    self.responses.append(data)
                    self.whitelist.append(proxy)
                    print(f"PROXY SUCCESS {proxy}")
                except requests.exceptions.JSONDecodeError:
                    if proxy in self.whitelist:
                        self.whitelist = [i for i in self.whitelist if i != proxy]
            elif proxy in self.whitelist:
                self.whitelist = [i for i in self.whitelist if i != proxy]
        except Exception as e:
            pass

    def check_mode(self):
        """
        Check if there at least three responses, with two matching
        """
        if len(self.responses) >= 3:
            try:
                return json.loads(mode([json.dumps(i) for i in self.responses]))
            except StatisticsError as e:
                return None

    def get(self, *args, **kwargs):
        """
        Act as direct replacement for requests.get, but pass all requests through proxies
        """
        # Always update the proxy list
        self.get_proxy_list()
        # reset responses
        self.responses = []
        # check whitelisted proxies first, and exclude blacklisted proxies
        proxies = self.whitelist + [i for i in self.proxies if i not in self.blacklist]
        mode_response = []
        # iterate through all proxies
        for i, proxy in enumerate(proxies):
            # check if we have a mode yet
            mode_response = self.check_mode()
            # if we do, break
            if mode_response is not None:
                break
            # spawn thread to try another proxy
            thread = threading.Thread(
                target=self.make_request,
                args=(
                    proxy,
                    *args,
                ),
                kwargs=kwargs,
            )
            thread.start()
            # sleep to prevent overloading of URL
            time.sleep(min(1, 0.005 * i))
        return mode_response


def main():
    """
    Unit test
    """
    # proxies = []
    # proxyscrapecom(proxies)
    # openproxyspace(proxies)
    # freeproxycz(proxies)
    # freeproxyworld(proxies)
    # socksproxynet(proxies)
    # proxylistdownload(proxies)
    # print("\033c")
    # print(proxies)
    # print(len(proxies))
    # exit()

    proxm = ProxyManager()
    print(proxm.get("https://api.binance.com/api/v1/ticker/allPrices"))


if __name__ == "__main__":
    main()
