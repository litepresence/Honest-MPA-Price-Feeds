"""
Acquire a list of non US based socks5 proxy servers
Provide Statistical Mode Response
Unit Tested On Binance Public API from US based VPN

litepresence + squidKid-deluxe 2024
"""

# STANDARD MODULES
import base64
import json
import os
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
from utilities import it, race_read, race_write

PINGS = [
    "http://pingomatic.com",
    "http://pingler.com",
    "http://indexkings.com",
    "http://totalping.com",
    "http://pingfarm.com",
    "http://pingmyurl.com",
    "http://addurl.nu/",
    "http://googleping.com",
    "http://pingsitemap.com",
    "http://pingbomb.com",
    "http://mypagerank.net",
    "http://ping.in",
    "http://coreblog.org/ping",
    "http://feedshark.brainbliss.com",
    "http://pingoat.net",
    "http://backlinkping.com",
    "http://nimtools.com/online-ping-website-tool",
    "http://blo.gs/ping.php",
    "http://blogbuzzer.com",
    "http://weblogs.com",
    "http://pingmyblog.com",
    "http://bulkping.com",
    "http://auto-ping.com",
    "http://rpc.weblogs.com",
    "http://autopinger.com",
    "http://icerocket.com",
    "http://blogsnow.com/ping",
    "http://weblogalot.com/ping",
    "http://bulkfeeds.net/rpc",
    "http://ipings.com",
    "http://feedsubmitter.com",
    "http://pingerati.net",
    "http://pingmylink.com",
    "http://syncr.com",
    "http://blogpingtool.com",
    "http://blogmatcher.com",
    "http://pinggator.com",
    "http://geourl.org/ping",
    "http://pingates.com",
]


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
        link = re.sub(r"\s+", "", link)
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
        self.whitelist = set()
        self.proxies = list()
        self.blacklist = set()
        self.tick = 0
        self.blacklist = self.load_list("black")

    def initial_blacklist(self):
        print(it("cyan", "PROXY:"), "Starting proxy checking...")
        children = []
        for proxy in [i for i in self.proxies if i not in self.blacklist]:
            children.append(
                threading.Thread(
                    target=self.make_request,
                    args=("get", proxy),
                    kwargs={"url": random.choice(PINGS)},
                )
            )
            children[-1].start()
            time.sleep(0.05)

        print(it("cyan", "PROXY:"), "All proxy checks started, waiting for responses...")

        for child in children:
            child.join()
        self.save_list(self.blacklist, "black")
        self.save_list(self.whitelist, "white")
        self.save_list([i for i in self.proxies if i not in self.blacklist], "grey")
        print(it("cyan", "PROXY:"), f"Proxy checking done! {len(self.blacklist)} blacklisted, {len(self.proxies)} left.")

    def get_proxy(self):
        if random.random() > 0.5 and self.whitelist:
            return random.choice(self.whitelist)
        else:
            proxy = random.choice(self.proxies)
            while proxy in self.blacklist:
                proxy = random.choice(self.proxies)
            self.whitelist.add(proxy)
            return proxy

    def blacklist_proxy(self, proxy):
        self.blacklist.add(proxy)
        self.whitelist = {i for i in self.whitelist if i != proxy}

    def get_proxy_list(self):
        """
        Spawn thread to concurrently get all available proxy lists and merge them
        """
        print(it("cyan", "PROXY:"), "Fetching lists of proxies...")
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

        self.proxies = list(self.proxies)

        random.shuffle(self.proxies)

        # Eliminate duplicates and malformed servers
        self.proxies = list(set(filter_broken_links(set(self.proxies))))
        self.initial_blacklist()

    def make_request(self, type, proxy, *args, **kwargs):
        """
        Make request using a given SOCKS4 proxy, otherwise
        act as direct replacement for requests.get
        """
        data = None
        try:
            # Set the SOCKS proxy server address and port
            proxy_host, proxy_port = proxy.split(":")

            session = requests.Session()

            # Directly set the proxy for this specific session using the proxies attribute
            session.proxies = {
                'http': f'socks5://{proxy_host}:{proxy_port}',
                'https': f'socks5://{proxy_host}:{proxy_port}',
            }
            resp = session.get(*args, timeout=5, **kwargs)
            if resp.status_code == 200:
                data = resp.text
        except Exception as e:
            self.blacklist.add(proxy)
        return data

    def save_list(self, typelist, name):
        race_write(f"proxy_{name}list.txt", list(typelist))

    def load_list(self, name):
        return set(race_read(f"proxy_{name}list.txt"))
