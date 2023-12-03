"""
+===============================+
  ╦ ╦  ╔═╗  ╔╗╔  ╔═╗  ╔═╗  ╔╦╗
  ╠═╣  ║ ║  ║║║  ║╣   ╚═╗   ║
  ╩ ╩  ╚═╝  ╝╚╝  ╚═╝  ╚═╝   ╩
    MARKET - PEGGED - ASSETS
+===============================+

publish pricefeeds and update feed producers with ECDSA via public API
this is a fork of manualsigning.py

litepresence2020
"""

# STANDARD PYTHON MODULES
from binascii import hexlify  # binary text to hexidecimal
from binascii import unhexlify  # hexidecimal to binary text
from hashlib import sha256  # message digest algorithm
from hashlib import new as hashlib_new  # access algorithm library
from struct import pack  # convert to string representation of C struct
from struct import unpack_from  # convert back to PY variable
from time import time, ctime, gmtime, asctime, strptime, strftime, sleep
from multiprocessing import Process, Value  # encapsulate processes
from decimal import Decimal as decimal  # higher precision than float
from json import dumps as json_dumps  # serialize object to string
from json import loads as json_loads  # deserialize string to object
from collections import OrderedDict
from datetime import datetime
from calendar import timegm
from random import shuffle
from pprint import pprint  # pretty printing
import os

# THIRD PARTY MODULES
from websocket import create_connection as wss  # handshake to node
from secp256k1 import PrivateKey as secp256k1_PrivateKey  # class
from secp256k1 import PublicKey as secp256k1_PublicKey  # class
from secp256k1 import ffi as secp256k1_ffi  # compiled ffi object
from secp256k1 import lib as secp256k1_lib  # library
from ecdsa import numbertheory as ecdsa_numbertheory  # largest import
from ecdsa import VerifyingKey as ecdsa_VerifyingKey  # class
from ecdsa import SigningKey as ecdsa_SigningKey  # class
from ecdsa import SECP256k1 as ecdsa_SECP256k1  # curve
from ecdsa import util as ecdsa_util  # module
from ecdsa import der as ecdsa_der  # module

# HONEST PRICE FEED MODULES
from utilities import race_write, trace, block_print, enable_print, it
from config_nodes import public_nodes


# =======================================================================
VERSION = "Bitshares Price Feed Publisher 0.00000001"
# FIXME: it would be pythonic to pass variables as args where needed
# FIXME: it would be pythonic to move constants to global space
# FIXME: this script could use a soup-to-nuts once over to pylint standards
# =======================================================================
DEV = False  # WARN: will expose your wif in terminal
COLOR = True

# bitsharesbase/operationids.py
OP_IDS = {
    "Asset_update_feed_producers": 13,
    "Asset_publish_feed": 19,
}
# swap keys/values to index names by number
OP_NAMES = {v: k for k, v in OP_IDS.items()}
# bitsharesbase/chains.py
ID = "4018d7844c78f6a6c41c6a552b898022310fc5dec06da467ee7905a8dad512c8"
# bitsharesbase/objecttypes.py used by ObjectId() to confirm a.b.c
TYPES = {
    "account": 2,
    "asset": 3,
}  # 1.2.x  # 1.3.x  # 1.7.x etc.
# base58 encoding and decoding; this is alphabet defined:
BASE58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
# hex encoding and decoding
HEXDIGITS = "0123456789abcdefABCDEF"
# ISO8601 timeformat; 'graphene time'
ISO8601 = "%Y-%m-%dT%H:%M:%S%Z"
# MAX is 4294967295; year 2106 due to 4 byte unsigned integer
END_OF_TIME = 4 * 10**9  # about 75 years in future
# very little
SATOSHI = decimal(0.00000001)
# almost 1
SIXSIG = decimal(0.999999)

# #################################################################
# CONTROL PANEL
# timeout during websocket handshake; default 4 seconds
HANDSHAKE_TIMEOUT = 4
# multiprocessing handler lifespan, default 20 seconds
PROCESS_TIMEOUT = 20
# default True scales elements of oversize gross order to means
AUTOSCALE = True
# multiprocessing incarnations, default 3 attempts
ATTEMPTS = 3
# prevent extreme number of AI generated edicts; default 20
LIMIT = 20
# default True to execute order in primary script process
JOIN = True
# #################################################################


# REMOTE PROCEDURE CALLS TO PUBLIC API NODES
def wss_handshake():
    """
    create a wss handshake in less than X seconds, else try again
    """
    global nodes, ws
    nodes = public_nodes()
    shuffle(nodes)
    handshake = 999
    while handshake > HANDSHAKE_TIMEOUT:
        try:
            try:
                ws.close  # attempt to close open connection
                print(it("purple", "connection terminated"))
            except:
                pass
            start = time()
            nodes.append(nodes.pop(0))  # rotate list
            node = nodes[0]
            print(it("purple", "connecting:"), node)
            ws = wss(node, timeout=HANDSHAKE_TIMEOUT)
            handshake = time() - start
        except:
            continue
    print(it("purple", "connected:"), node, ws)
    print("elapsed %.3f sec" % (time() - start))
    return ws


def wss_query(params):
    """
    this definition will place all remote procedure calls (RPC)
    """
    for _ in range(10):
        try:
            # print(it('purple','RPC ' + params[0]), it('cyan',params[1]))
            # query is 4 element dict {"method":"", "params":"", "jsonrpc":"", "id":""}
            # params is 3 element list ["location", "object", []]
            query = json_dumps(
                {
                    "method": "call",
                    "params": params,
                    "jsonrpc": "2.0",
                    "id": 1,
                }
            )
            # print(query)
            # ws is the websocket connection created by wss_handshake()
            # we will use this connection to send query and receive json
            ws.send(query)
            ret = json_loads(ws.recv())
            try:
                ret = ret["result"]  # if there is result key take it
            except:
                pass
            # print(ret)
            # print('elapsed %.3f sec' % (time() - start))
            return ret
        except Exception as e:
            try:  # attempt to terminate the connection
                ws.close()
            except:
                pass
            trace(e)  # tell me what happened
            # switch nodes
            wss_handshake()
            continue
    raise


def rpc_block_number():
    """
    block number and block prefix
    """
    return wss_query(["database", "get_dynamic_global_properties", []])


def rpc_account_id():
    """
    given an account name return an account id
    """
    ret = wss_query(["database", "lookup_accounts", [account_name, 1]])
    return ret[0][1]


def rpc_fees():
    """
    returns fee without 10^precision
    """
    query = [
        "database",
        "get_required_fees",
        [
            [
                # reference /bitsharesbase/operationids.py
                ["1", {"from": str(account_id)}],  # limit order create (legacy)
                ["2", {"from": str(account_id)}],  # limit order cancel (legacy)
                ["13", {"from": str(account_id)}],  # add a feed producer
                ["19", {"from": str(account_id)}],  # publish a price feed
            ],
            "1.3.0",
        ],
    ]
    ret = wss_query(query)
    create = ret[0]["amount"]
    cancel = ret[1]["amount"]
    producer = ret[2]["amount"]
    publish = ret[3]["amount"]
    return {
        "create": create,
        "cancel": cancel,
        "producer": producer,
        "publish": publish,
    }


def rpc_lookup_asset_symbols(asset_name):
    """
    Given asset name, return asset id and precision
    """
    query = ["database", "lookup_asset_symbols", [[asset_name]]]
    ret = wss_query(query)
    asset_id = ret[-1]["id"]
    asset_precision = ret[-1]["precision"]

    return asset_id, asset_precision


def rpc_key_reference(public_key):
    """
    given public key return account id
    """
    return wss_query(["database", "get_key_references", [[public_key]]])


def rpc_get_transaction_hex_without_sig(tx):
    """
    use this to verify the manually serialized tx buffer
    """
    ret = wss_query(["database", "get_transaction_hex_without_sig", [tx]])
    return bytes(ret, "utf-8")


def rpc_broadcast_transaction(tx):
    """
    upload the signed transaction to the blockchain
    """
    ret = wss_query(["network_broadcast", "broadcast_transaction", [tx]])
    if ret is None:
        print(it("yellow", "*************************************"))
        print("manualSIGNING" + it("red", " has placed your order"))
        print(it("yellow", "*************************************"))
        return tx
    pprint(ret)
    return ret


# DATE FORMATTING
def to_iso_date(unix):
    """
    returns iso8601 datetime given unix epoch
    """
    return datetime.utcfromtimestamp(int(unix)).isoformat()


def from_iso_date(iso):
    """
    returns unix epoch given iso8601 datetime
    """
    return int(timegm(strptime((iso + "UTC"), ISO8601)))


# GRAPHENEBASE TYPES # graphenebase/types.py


class ObjectId:
    """
    encodes a.b.c object ids - serializes the *instance* only!
    """

    def __init__(self, object_str, type_verify=None):
        # if after splitting a.b.c there are 3 pieces:
        if len(object_str.split(".")) == 3:
            # assign those three pieces to a, b, and c
            a, b, c = object_str.split(".")
            # assure they are integers
            self.a = int(a)
            self.b = int(b)
            self.c = int(c)
            # serialize the c element; the "instance"
            self.instance = Id(self.c)
            self.abc = object_str
            # 1.2.x:account, 1.3.x:asset, or 1.7.x:limit
            if type_verify:
                assert TYPES[type_verify] == int(b), (
                    # except raise error showing mismatch
                    "Object id does not match object type! "
                    + "Excpected %d, got %d" % (TYPES[type_verify], int(b))
                )
        else:
            raise Exception("Object id is invalid")

    def __bytes__(self):
        # b'\x00\x00\x00' of serialized c element; the "instance"
        return bytes(self.instance)


class Id:
    """
    serializes the c element of "a.b.c" types
    merged with Varint32()
    """

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return bytes(varint(self.data))


class Array:
    """
    serializes lists as byte strings
    merged with Set() and Varint32()
    """

    def __init__(self, d):
        self.data = d
        self.length = int(len(self.data))

    def __bytes__(self):
        return bytes(varint(self.length)) + b"".join([bytes(a) for a in self.data])


class Uint8:
    """
    byte string of 8 bit unsigned integers
    merged with Bool()
    """

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<B", self.data)


class Uint16:
    """
    byte string of 16 bit unsigned integers
    """

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<H", self.data)


class Uint32:
    """
    byte string of 32 bit unsigned integers
    """

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        return pack("<I", self.data)


class Int64:
    """
    byte string of 64 bit unsigned integers
    """

    def __init__(self, d):
        self.data = int(d)

    def __bytes__(self):
        """
        little endian double long
        """
        return pack("<q", self.data)


class Signature:
    """
    used to disable bytes() method on Signatures in OrderedDicts
    """

    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """
        note does NOT return bytes(self.data)
        """
        return self.data


class PointInTime:
    """
    used to pack ISO8601 time as 4 byte unix epoch integer as bytes
    """

    def __init__(self, d):
        self.data = d

    def __bytes__(self):
        """#"""
        return pack("<I", from_iso_date(self.data))


def fraction(num):
    """
    convert float to limited precision least common denominator fraction
    """
    iteration = 0
    den = 1
    while True:  # move decimal place by factor of 10
        iteration += 1
        num *= 10
        den *= 10
        # escape when numerator is integer or denomenator approaches double long int
        if (int(num) == num) or (den == 10**14):
            break
    # ensure numerator is now an integer
    num = int(num)
    while True:  # remove common factors of 2
        iteration += 1
        if int(num / 2) != num / 2 or int(den / 2) != den / 2:
            break
        num /= 2
        den /= 2
    while True:  # remove common factors of 5
        iteration += 1
        if int(num / 5) != num / 5 or int(den / 5) != den / 5:
            break
        num /= 5
        den /= 5
    return {"base": int(num), "quote": int(den), "iteration": iteration}


# VARINT
def varint(num):
    """
    varint encoding normally saves memory on smaller numbers
    yet retains ability to represent numbers of any magnitude
    """
    data = b""
    while num >= 0x80:
        data += bytes([(num & 0x7F) | 0x80])
        num >>= 7
    data += bytes([num])
    return data


# BASE 58 ENCODE, DECODE, AND CHECK # graphenebase/base58.py
class Base58(object):
    """
    This class serves as an abstraction layer
    to deal with base58 encoded strings
    and their corresponding hex and binary representation
    """

    def __init__(self, data, prefix="BTS"):
        print(it("green", "Base58"))
        print(it("blue", data[:4]))
        self._prefix = prefix
        if all(c in HEXDIGITS for c in data):
            self._hex = data
        elif data[0] in ["5", "6"]:
            self._hex = base58CheckDecode(data)
        elif data[0] in ["K", "L"]:
            self._hex = base58CheckDecode(data)[:-2]
        elif data[: len(self._prefix)] == self._prefix:
            self._hex = gphBase58CheckDecode(data[len(self._prefix) :])
        else:
            raise ValueError("Error loading Base58 object")

    def __format__(self, _format):
        """#"""
        if _format.upper() != "BTS":
            print("Format %s unkown. You've been warned!\n" % _format)
        return _format.upper() + str(self)

    def __repr__(self):
        """
        hex string of data
        """
        return self._hex

    def __str__(self):
        """
        base58 string of data
        """
        return gphBase58CheckEncode(self._hex)

    def __bytes__(self):
        """
        raw bytes of data
        """
        return unhexlify(self._hex)


def base58decode(base58_str):
    """#"""
    print(it("green", "base58decode"))
    base58_text = bytes(base58_str, "ascii")
    n = 0
    leading_zeroes_count = 0
    for b in base58_text:
        n = n * 58 + BASE58.find(b)
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 256:
        div, mod = divmod(n, 256)
        res.insert(0, mod)
        n = div
    res.insert(0, n)
    return hexlify(bytearray(1) * leading_zeroes_count + res).decode("ascii")


def base58encode(hexstring):
    """#"""
    print(it("green", "base58encode"))
    byteseq = bytes(unhexlify(bytes(hexstring, "ascii")))
    n = 0
    leading_zeroes_count = 0
    for c in byteseq:
        n = n * 256 + c
        if n == 0:
            leading_zeroes_count += 1
    res = bytearray()
    while n >= 58:
        div, mod = divmod(n, 58)
        res.insert(0, BASE58[mod])
        n = div
    res.insert(0, BASE58[n])
    ret = (BASE58[:1] * leading_zeroes_count + res).decode("ascii")
    # public_key = 'BTS' + str(ret)
    # print(it('purple',public_key), "public key")
    print("len(ret)", len(ret))
    return ret


def ripemd160(s):
    """
    160-bit cryptographic hash function
    """
    r160 = hashlib_new("ripemd160")  # import the library
    r160.update(unhexlify(s))
    ret = r160.digest()
    print("use hashlib to perform a ripemd160 message digest")
    print(ret)
    return ret


def doublesha256(s):
    """
    double sha256 cryptographic hash function
    """
    ret = sha256(sha256(unhexlify(s)).digest()).digest()
    print("use hashlib to perform a double sha256 message digest")
    print(ret)
    return ret


def base58CheckEncode(version, payload):
    """#"""
    print(it("green", "base58CheckEncode"))
    print(payload, version)
    s = ("%.2x" % version) + payload
    print(s)
    checksum = doublesha256(s)[:4]
    result = s + hexlify(checksum).decode("ascii")
    return base58encode(result)


def gphBase58CheckEncode(s):
    """#"""
    print(it("yellow", "gphBase58CheckEncode"))
    print(s)
    checksum = ripemd160(s)[:4]
    result = s + hexlify(checksum).decode("ascii")
    return base58encode(result)


def base58CheckDecode(s):
    """#"""
    print(it("green", "base58CheckDecode"))
    print(s[:4])
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode("ascii")
    checksum = doublesha256(dec)[:4]
    assert s[-4:] == checksum
    return dec[2:]


def gphBase58CheckDecode(s):
    """#"""
    print(it("yellow", "gphBase58CheckDecode"))
    print(s)
    s = unhexlify(base58decode(s))
    dec = hexlify(s[:-4]).decode("ascii")
    checksum = ripemd160(dec)[:4]
    assert s[-4:] == checksum
    return dec


# ADDRESS AND KEYS
class Address(object):  # cropped litepresence2019
    """
    Example :: Address("BTSFN9r6VYzBK8EKtMewfNbfiGCr56pHDBFi")
    """

    # graphenebase/account.py
    def __init__(self, pubkey=None, prefix="BTS"):
        print(it("red", "Address"), "pubkey", pubkey)
        self.prefix = prefix
        self._pubkey = Base58(pubkey, prefix=prefix)
        self._address = None


class PublicKey(Address):  # graphenebase/account.py
    """
    This class deals with Public Keys and inherits ``Address``.
    :param str pk: Base58 encoded public key
    :param str prefix: Network prefix (defaults to ``BTS``)
    """

    def __init__(self, pk, prefix="BTS"):
        global authenticated  # FIXME: there are better ways to handle this
        print(it("red", "PublicKey"))
        self.prefix = prefix
        self._pk = Base58(pk, prefix=prefix)
        self.address = Address(pubkey=pk, prefix=prefix)
        self.pubkey = self._pk
        public_key = prefix + str(self._pk)
        if login and (len(public_key) == 53):
            try:
                public_key = prefix + str(self._pk)
                print(public_key)
                print(len(public_key))
                account = rpc_key_reference(public_key)
                print(str(account[0][0]))
                print(str(account_id))
                if str(account[0][0]) == str(account_id):
                    authenticated = True
                print("authenticated:", authenticated)
            except:
                pass

    def _derive_y_from_x(self, x, is_even):
        """
        derive y point from x point
        """
        print(it("purple", "           y^2 = x^3 + ax + b          "))
        print(self, x)
        curve = ecdsa_SECP256k1.curve
        a, b, p = curve.a(), curve.b(), curve.p()
        alpha = (pow(x, 3, p) + a * x + b) % p
        beta = ecdsa_numbertheory.square_root_mod_prime(alpha, p)
        if (beta % 2) == is_even:
            beta = p - beta
        print(beta)
        return beta

    def compressed(self):
        """
        Derive compressed public key
        """
        print("PublicKey.compressed")
        order = ecdsa_SECP256k1.generator.order()
        p = ecdsa_VerifyingKey.from_string(
            bytes(self), curve=ecdsa_SECP256k1
        ).pubkey.point
        x_str = ecdsa_util.number_to_string(p.x(), order)
        return hexlify(bytes(chr(2 + (p.y() & 1)), "ascii") + x_str).decode("ascii")

    def unCompressed(self):
        """
        Derive uncompressed key
        """
        print("PublicKey.unCompressed")
        public_key = repr(self._pk)
        prefix = public_key[:2]
        if prefix == "04":
            return public_key
        assert prefix in ["02", "03"]
        x = int(public_key[2:], 16)
        y = self._derive_y_from_x(x, (prefix == "02"))
        return "04" + "%064x" % x + "%064x" % y

    def __repr__(self):
        """
        Gives the hex representation of the Graphene public key.
        """
        # print('PublicKey.__repr__')
        return repr(self._pk)

    def __format__(self, _format):
        """
        formats the instance of:doc:`Base58 <base58>
        ` according to ``_format``
        """
        # print('PublicKey.__format__')
        return format(self._pk, _format)

    def __bytes__(self):
        """
        returns the raw public key (has length 33)
        """
        # print('PublicKey.__bytes__')
        return bytes(self._pk)


class PrivateKey(PublicKey):
    """
    derives the compressed and uncompressed public keys and
    constructs two instances of ``PublicKey``
    Bitshares(MIT) graphenebase/account.py
    Bitshares(MIT) bitsharesbase/account.py
    merged litepresence2019
    """

    def __init__(self, wif=None, prefix="BTS"):
        print(prefix)
        print(it("red", "PrivateKey"))
        print(PublicKey)
        if wif is None:
            self._wif = Base58(hexlify(os.urandom(32)).decode("ascii"))
        elif isinstance(wif, Base58):
            self._wif = wif
        else:
            self._wif = Base58(wif)
        # compress pubkeys only
        self._pubkeyhex, self._pubkeyuncompressedhex = self.compressedpubkey()
        self.pubkey = PublicKey(self._pubkeyhex, prefix=prefix)
        self.uncompressed = PublicKey(self._pubkeyuncompressedhex, prefix=prefix)
        self.uncompressed.address = Address(
            pubkey=self._pubkeyuncompressedhex, prefix=prefix
        )
        self.address = Address(pubkey=self._pubkeyhex, prefix=prefix)

    def compressedpubkey(self):
        """
        Derive uncompressed public key
        """
        print("PrivateKey.compressedpubkey")
        secret = unhexlify(repr(self._wif))
        order = ecdsa_SigningKey.from_string(
            secret, curve=ecdsa_SECP256k1
        ).curve.generator.order()
        p = ecdsa_SigningKey.from_string(
            secret, curve=ecdsa_SECP256k1
        ).verifying_key.pubkey.point
        x_str = ecdsa_util.number_to_string(p.x(), order)
        y_str = ecdsa_util.number_to_string(p.y(), order)
        compressed = hexlify(chr(2 + (p.y() & 1)).encode("ascii") + x_str).decode(
            "ascii"
        )
        uncompressed = hexlify(chr(4).encode("ascii") + x_str + y_str).decode("ascii")
        return [compressed, uncompressed]

    def __bytes__(self):
        """
        returns the raw private key
        """
        # print('PrivateKey.__bytes__')
        return bytes(self._wif)


# SERIALIZATION
class GrapheneObject(object):
    """
    Bitshares(MIT) graphenebase/objects.py
    """

    def __init__(self, data=None):
        self.data = data

    def __bytes__(self):
        # encodes data into wire format'
        if self.data is None:
            return bytes()
        b = b""
        for _, value in self.data.items():
            b += bytes(value, "utf-8") if isinstance(value, str) else bytes(value)
        return b


class Asset(GrapheneObject):
    """
    bitsharesbase/objects.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("amount", Int64(kwargs["amount"])),
                        (
                            "asset_id",
                            ObjectId(kwargs["asset_id"], "asset"),
                        ),
                    ]
                )
            )


class Price(GrapheneObject):
    """
    bitsharesbase/objects.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [("base", Asset(kwargs["base"])), ("quote", Asset(kwargs["quote"]))]
                )
            )


class PriceFeed(GrapheneObject):
    """
    bitsharesbase/objects.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("settlement_price", Price(kwargs["settlement_price"])),
                        (
                            "maintenance_collateral_ratio",
                            Uint16(kwargs["maintenance_collateral_ratio"]),
                        ),
                        (
                            "maximum_short_squeeze_ratio",
                            Uint16(kwargs["maximum_short_squeeze_ratio"]),
                        ),
                        ("core_exchange_rate", Price(kwargs["core_exchange_rate"])),
                    ]
                )
            )


class Operation:
    """
    refactored  litepresence2019, updated 2020
    class GPHOperation():
    Bitshares(MIT) graphenebase/objects.py
    class Operation(GPHOperation):
    Bitshares(MIT) bitsharesbase/objects.py
    """

    def __init__(self, op):
        if not isinstance(op, list):
            raise ValueError("expecting op to be a list")
        if len(op) != 2:
            raise ValueError("expecting op to be two items")
        if not isinstance(op[0], int):
            raise ValueError("expecting op[0] to be integer")
        self.opId = op[0]
        name = OP_NAMES[self.opId]
        self.name = name[0].upper() + name[1:]
        if op[0] == 13:
            self.op = Asset_update_feed_producers(op[1])
        elif op[0] == 19:
            self.op = Asset_publish_feed(op[1])

    def __bytes__(self):
        print(it("yellow", "GPHOperation.__bytes__"))
        return bytes(Id(self.opId)) + bytes(self.op)


class Signed_Transaction(GrapheneObject):
    """
    merged litepresence2019
    Bitshares(MIT) graphenebase/signedtransactions.py
    Bitshares(MIT) bitsharesbase/signedtransactions.py
    """

    def __init__(self, *args, **kwargs):
        """
        Create a signed transaction and
        offer method to create the signature
        (see ``getBlockParams``)
        :param num refNum: parameter ref_block_num
        :param num refPrefix: parameter ref_block_prefix
        :param str expiration: expiration date
        :param Array operations:  array of operations
        """
        print(it("red", "Signed_Transaction"))
        print("args, kwargs", args, kwargs)
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            if (
                "extensions" not in kwargs
                or "extensions" in kwargs
                and not kwargs.get("extensions")
            ):
                kwargs["extensions"] = Array([])
            if "signatures" not in kwargs:
                kwargs["signatures"] = Array([])
            else:
                kwargs["signatures"] = Array(
                    [Signature(unhexlify(a)) for a in kwargs["signatures"]]
                )
            if "operations" in kwargs:
                opklass = self.getOperationKlass()
                if all(not isinstance(a, opklass) for a in kwargs["operations"]):
                    kwargs["operations"] = Array(
                        [opklass(a) for a in kwargs["operations"]]
                    )
                else:
                    kwargs["operations"] = Array(kwargs["operations"])
            super().__init__(
                OrderedDict(
                    [
                        (
                            "ref_block_num",
                            Uint16(kwargs["ref_block_num"]),
                        ),
                        (
                            "ref_block_prefix",
                            Uint32(kwargs["ref_block_prefix"]),
                        ),
                        (
                            "expiration",
                            PointInTime(kwargs["expiration"]),
                        ),
                        ("operations", kwargs["operations"]),
                        ("extensions", kwargs["extensions"]),
                        ("signatures", kwargs["signatures"]),
                    ]
                )
            )

    @property
    def id(self):

        """
        The transaction id of this transaction
        """
        print("Signed_Transaction.id")
        # Store signatures temporarily
        sigs = self.data["signatures"]
        self.data.pop("signatures", None)
        # Generage Hash of the seriliazed version
        h = sha256(bytes(self)).digest()
        # Recover signatures
        self.data["signatures"] = sigs
        # Return properly truncated tx hash
        return hexlify(h[:20]).decode("ascii")

    def getOperationKlass(self):
        """#"""
        print("Signed_Transaction.get_operationKlass")
        return Operation

    def derSigToHexSig(self, s):
        """#"""
        print("Signed_Transaction.derSigToHexSig")
        s, junk = ecdsa_der.remove_sequence(unhexlify(s))
        if junk:
            print("JUNK: %s", hexlify(junk).decode("ascii"))
        assert junk == b""
        x, s = ecdsa_der.remove_integer(s)
        y, s = ecdsa_der.remove_integer(s)
        return "%064x%064x" % (x, y)

    def deriveDigest(self, chain):
        """#"""
        print("Signed_Transaction.deriveDigest")
        print(self, chain)
        # Do not serialize signatures
        sigs = self.data["signatures"]
        self.data["signatures"] = []
        # Get message to sign
        #   bytes(self) will give the wire formated data according to
        #   GrapheneObject and the data given in __init__()
        self.message = unhexlify(ID) + bytes(self)
        self.digest = sha256(self.message).digest()
        # restore signatures
        self.data["signatures"] = sigs

    def verify(self, pubkeys=None, chain="BTS"):
        """#"""
        if pubkeys is None:
            pubkeys = []
        print(it("green", "###############################################"))
        print("Signed_Transaction.verify")
        print(it("green", "self, pubkeys, chain"), self, pubkeys, chain)
        self.deriveDigest(chain)
        print(it("green", "self"))
        print(self)
        signatures = self.data["signatures"].data
        print(it("green", "signatures"))
        print(signatures)
        pubKeysFound = []
        for signature in signatures:
            p = verify_message(self.message, bytes(signature))
            phex = hexlify(p).decode("ascii")
            print("")
            print("")
            print(it("green", "phex"))
            print(it("green", phex))
            print(it("cyan", "len(phex)"), len(str(phex)))
            print("")
            print("")
            pubKeysFound.append(phex)
        for pubkey in pubkeys:
            print(it("green", "for pubkey in pubkeys:"))
            print(it("green", "************ pubkey ************"))
            print(it("blue", "repr(pubkey)"))
            print(repr(pubkey))
            print(it("cyan", "len(pubkey)"), len(str(pubkey)))
            print("")
            if not isinstance(pubkey, PublicKey):
                raise Exception("Pubkeys must be array of 'PublicKey'")
            k = pubkey.unCompressed()[2:]
            print(it("green", ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"))
            print(it("yellow", "k"))
            print(k)
            print(it("cyan", "len(k)"), len(str(k)))
            print(it("yellow", "pubKeysFound"))
            print(pubKeysFound)
            print(it("cyan", "len(pubKeysFound[0])"), len(pubKeysFound[0]))
            print("")
            print(it("green", ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"))
            if k not in pubKeysFound and repr(pubkey) not in pubKeysFound:
                print(
                    it(
                        "blue",
                        "if k not in pubKeysFound and repr(pubkey) "
                        + "not in pubKeysFound:",
                    )
                )
                k = PublicKey(PublicKey(k).compressed())
                f = format(k, "BTS")  # chain_params["prefix"]) # 'BTS'
                print("")
                print(it("red", "FIXME"))
                raise Exception("Signature for %s missing!" % f)
        return pubKeysFound

    def sign(self, wifkeys, chain="BTS"):
        """
        Sign the transaction with the provided private keys.
        """
        # FIXME is this even used????
        print("Signed_Transaction.sign")
        self.deriveDigest(chain)
        # Get Unique private keys
        self.privkeys = []
        [self.privkeys.append(item) for item in wifkeys if item not in self.privkeys]
        # Sign the message with every private key given!
        sigs = []
        for key in self.privkeys:
            signature = sign_message(self.message, key)
            sigs.append(Signature(signature))
        self.data["signatures"] = Array(sigs)
        return self


class Asset_publish_feed(GrapheneObject):
    """
    bitsharesbase/operations.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("publisher", ObjectId(kwargs["publisher"], "account")),
                        ("asset_id", ObjectId(kwargs["asset_id"], "asset")),
                        ("feed", PriceFeed(kwargs["feed"])),
                        ("extensions", Array([])),
                    ]
                )
            )


class Asset_update_feed_producers(GrapheneObject):
    """
    bitsharesbase/operations.py
    """

    def __init__(self, *args, **kwargs):
        if isArgsThisClass(self, args):
            self.data = args[0].data
        else:
            if len(args) == 1 and len(kwargs) == 0:
                kwargs = args[0]
            kwargs["new_feed_producers"] = sorted(
                kwargs["new_feed_producers"], key=lambda x: float(x.split(".")[2])
            )
            super().__init__(
                OrderedDict(
                    [
                        ("fee", Asset(kwargs["fee"])),
                        ("issuer", ObjectId(kwargs["issuer"], "account")),
                        (
                            "asset_to_update",
                            ObjectId(kwargs["asset_to_update"], "asset"),
                        ),
                        (
                            "new_feed_producers",
                            Array(
                                [
                                    ObjectId(o, "account")
                                    for o in kwargs["new_feed_producers"]
                                ]
                            ),
                        ),
                        ("extensions", Array([])),
                    ]
                )
            )


def verify_message(message, signature):
    """
    graphenebase/ecdsa.py stripped of non-secp256k1 methods
    """
    print(it("red", "verify_message...return phex"))
    # require message and signature to be bytes
    if not isinstance(message, bytes):
        message = bytes(message, "utf-8")
    if not isinstance(signature, bytes):
        signature = bytes(signature, "utf-8")
    # digest = hashfn(message).digest()
    sig = signature[1:]
    # recover parameter only
    recoverParameter = bytearray(signature)[0] - 4 - 27
    # "bitwise or"; each bit of the output is 0
    # if the corresponding bit of x AND of y is 0, otherwise it's 1
    ALL_FLAGS = (
        secp256k1_lib.SECP256K1_CONTEXT_VERIFY | secp256k1_lib.SECP256K1_CONTEXT_SIGN
    )
    # ecdsa.PublicKey with additional functions to serialize
    # in uncompressed and compressed formats
    pub = secp256k1_PublicKey(flags=ALL_FLAGS)
    # recover raw signature
    sig = pub.ecdsa_recoverable_deserialize(sig, recoverParameter)
    # recover public key
    verifyPub = secp256k1_PublicKey(pub.ecdsa_recover(message, sig))
    # convert recoverable sig to normal sig
    normalSig = verifyPub.ecdsa_recoverable_convert(sig)
    # verify
    verifyPub.ecdsa_verify(message, normalSig)
    return verifyPub.serialize(compressed=True)


def isArgsThisClass(self, args):
    """
    graphenebase/objects.py
    if there is only one argument and its type name is
    the same as the type name of self
    """
    return len(args) == 1 and type(args[0]).__name__ == type(self).__name__


# PRIMARY TRANSACTION BACKBONE
def build_transaction(order):
    """
    assemble a graphene object from a human readable order input
    """
    global account_id, account_name  # FIXME these should be passed as args
    account_name = str(order["header"]["account_name"])
    account_id = rpc_account_id()
    # VALIDATE INCOMING DATA
    if not isinstance(order["edicts"], list):
        raise ValueError("order parameter edicts must be list: %s" % order["edicts"])
    if not isinstance(order["nodes"], list):
        raise ValueError("order parameter nodes must be list: %s" % order["nodes"])
    if not isinstance(order["header"], dict):
        raise ValueError("order parameter header must be dict: %s" % order["header"])
    try:
        a, b, c = account_id.split(".")
        assert int(a) == 1
        assert int(b) == 2
        assert int(c) == float(c)
    except:
        raise ValueError("invalid object id %s" % account_id)
    # GATHER TRANSACTION HEADER DATA
    # fetch block data via websocket request
    block = rpc_block_number()
    ref_block_num = block["head_block_number"] & 0xFFFF
    ref_block_prefix = unpack_from("<I", unhexlify(block["head_block_id"]), 4)[0]
    # fetch limit order create and cancel fee via websocket request
    fees = rpc_fees()
    # establish transaction expiration
    tx_expiration = to_iso_date(int(time() + 120))
    # initialize tx_operations list
    tx_operations = []
    # SORT INCOMING EDICTS BY TYPE
    publish_edicts = []
    producer_edicts = []
    for edict in order["edicts"]:
        if edict["op"] == "publish":
            publish_edicts.append(edict)
        if edict["op"] == "producer":
            producer_edicts.append(edict)
    # TRANSLATE PRICE FEED PUBLISH ORDERS TO GRAPHENE
    for edict in publish_edicts:
        # make external rpc for id and precision for the asset
        asset_id, asset_precision = rpc_lookup_asset_symbols(edict["asset_name"])
        # repeat for currency
        currency_id, currency_precision = rpc_lookup_asset_symbols(
            edict["currency_name"]
        )
        # adjust settlment price to graphene asset and currency precisions
        adj_settlement = (
            edict["settlement_price"] * 10**asset_precision / 10**currency_precision
        )
        if edict["currency_name"] == "BTS":
            adj_core = adj_settlement
        else:
            adj_core = edict["core_price"] * 10**asset_precision / 10**5
        # FEE ORDERED DICT
        # create publication fee ordered dict
        fee = OrderedDict([("amount", fees["publish"]), ("asset_id", "1.3.0")])
        # SETTLEMENT ORDERED DICT
        # convert settlement price to a base/quote fraction
        s_base = fraction(adj_settlement)["base"]
        s_quote = fraction(adj_settlement)["quote"]
        # create a settlement-base price ordered dict
        settlement_base = OrderedDict([("amount", s_base), ("asset_id", asset_id)])
        # create a quote price ordered dict used w/ settlement base
        settlement_quote = OrderedDict([("amount", s_quote), ("asset_id", currency_id)])
        # combine settlement base and quote price
        settlement_price = OrderedDict(
            [("base", settlement_base), ("quote", settlement_quote)]
        )
        # CORE ORDERED DICT
        # convert core price to a base/quote fraction and multiply base by CER coeff
        c_base = int(fraction(adj_core)["base"] * edict["CER"])
        c_quote = fraction(adj_core)["quote"]
        # create a core-base price ordered dict
        core_base = OrderedDict(
            [
                ("amount", c_base),
                ("asset_id", asset_id),
            ]
        )
        # create a quote price ordered dict used w/ core base
        core_quote = OrderedDict([("amount", c_quote), ("asset_id", "1.3.0")])
        # combine core base and quote price
        core_exchange_rate = OrderedDict([("base", core_base), ("quote", core_quote)])
        # /bitshares/bitshares.py
        feed = OrderedDict(
            (
                [
                    # https://www.finra.org/rules-guidance/key-topics/margin-accounts
                    ("settlement_price", settlement_price),
                    (
                        "maintenance_collateral_ratio",
                        edict["MCR"],  # use graphene precision
                    ),
                    ("maximum_short_squeeze_ratio", edict["MSSR"]),
                    ("core_exchange_rate", core_exchange_rate),
                ]
            )
        )
        operation = [
            19,  # nineteen means "Publish Price Feed"
            OrderedDict(
                [
                    ("fee", fee),
                    ("publisher", account_id),
                    ("asset_id", asset_id),
                    ("feed", feed),
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    # TRANSLATE ADD PRODUCER ORDER TO GRAPHENE
    for edict in producer_edicts:
        fee = OrderedDict([("amount", fees["producer"]), ("asset_id", "1.3.0")])
        operation = [
            13,  # thirteen means "edit the price feed producer list"
            OrderedDict(
                [
                    ("fee", fee),
                    ("issuer", account_id),
                    ("asset_to_update", edict["asset_id"]),
                    ("new_feed_producers", edict["producer_ids"]),
                    ("extensions", []),
                ]
            ),
        ]
        tx_operations.append(operation)
    return {
        "ref_block_num": ref_block_num,
        "ref_block_prefix": ref_block_prefix,
        "expiration": tx_expiration,
        "operations": tx_operations,
        "signatures": [],
        "extensions": [],
    }


def serialize_transaction(tx):
    """
    gist.github.com/xeroc/9bda11add796b603d83eb4b41d38532b
    """
    if tx["operations"] == []:
        return tx, b""
    print(it("blue", "serialize_transaction"))
    print(it("yellow", "IF WE DO EVERYTHING RIGHT:"))
    print(it("green", "rpc_tx_hex = manual_tx_hex"))
    print(tx)
    # RPC call for ordered dicts which are dumped by the query
    print(it("yellow", "get RPC tx hex..."))
    rpc_tx_hex = rpc_get_transaction_hex_without_sig(tx)
    print(it("yellow", "build manual tx hex..."))
    buf = b""  # create an empty byte string buffer
    # add block number, prefix, and tx expiration to the buffer
    buf += pack("<H", tx["ref_block_num"])  # 2 byte int
    buf += pack("<I", tx["ref_block_prefix"])  # 4 byte int
    buf += pack("<I", from_iso_date(tx["expiration"]))  # 4 byte int
    # add length of operations list to buffer
    buf += bytes(varint(len(tx["operations"])))
    # add the operations list to the buffer in graphene type fashion
    for op in tx["operations"]:
        # print(op[0])  # Int (13=update_producers, 19=publish, etc.)
        # print(op[1])  # OrderedDict of operations
        buf += varint(op[0])
        if op[0] == 13:
            buf += bytes(Asset_update_feed_producers(op[1]))
        if op[0] == 19:
            enable_print()
            print(op[1])
            if not DEV:
                block_print()
            buf += bytes(Asset_publish_feed(op[1]))
    # add legth of (empty) extensions list to buffer
    buf += bytes(varint(len(tx["extensions"])))  # effectively varint(0)
    # this the final manual transaction hex, which should match rpc
    manual_tx_hex = hexlify(buf)
    print(it("red", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))
    print("   rpc_tx_hex:  ", rpc_tx_hex)
    print("manual_tx_hex:  ", manual_tx_hex)
    print(it("red", "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"))
    print(it("yellow", "assert (rpc_tx_hex == manual_tx_hex)"))
    # assert rpc_tx_hex == manual_tx_hex, "Serialization Failed"
    print(it("green", "Serialization Success"))
    # prepend the chain ID to the buffer to create final serialized msg
    message = unhexlify(ID) + buf
    return tx, message


def sign_transaction(tx, message):
    """
    graphenebase/ecdsa.py
    tools.ietf.org/html/rfc6979
    @xeroc/steem-transaction-signing-in-a-nutshell
    @dantheman/steem-and-bitshares-cryptographic-security-update
    """
    # deterministic signatures retain the cryptographic
    # security features associated with digital signatures
    # but can be more easily implemented
    # since they do not need high-quality randomness
    # 1 in 4 signatures are randomly canonical; "normal form"
    # using the other three causes vulnerability to maleability attacks
    # as a metaphor; "require reduced fractions in simplest terms"
    def canonical(sig):
        sig = bytearray(sig)
        # 0x80 hex = 10000000 binary = 128 integer
        ret = (
            not (int(sig[0]) & 0x80)
            and not (sig[0] == 0 and not (int(sig[1]) & 0x80))
            and not (int(sig[32]) & 0x80)
            and not (sig[32] == 0 and not (int(sig[33]) & 0x80))
        )
        print(it("green", "canonical"), it("cyan", str(ret)))
        print(sig)
        return ret  # true/false

    # create fixed length representation of arbitrary length data
    # this will thoroughly obfuscate and compress the transaction
    # signing large data is computationally expensive and time consuming
    # the hash of the data is a relatively small
    # thus signing hash is more efficient than signing serialization
    digest = sha256(message).digest()
    print(digest)
    # ECDSA
    # eliptical curve digital signature algorithm
    print("this is where the real hocus pocus lies!")
    # all of the ordering, typing, serializing, and digesting
    # culminates with the message meeting the wif
    # 8 bit string representation of private key
    p = bytes(PrivateKey(wif))
    # create some arbitrary data used by the nonce generation
    ndata = secp256k1_ffi.new("const int *ndata")
    ndata[0] = 0  # it adds "\0x00", then "\0x00\0x00", etc..
    while True:  # repeat process until deterministic and cannonical
        ndata[0] += 1  # increment the arbitrary nonce
        # obtain compiled/binary private key from the wif
        privkey = secp256k1_PrivateKey(p, raw=True)
        print(it("red", str(privkey)))
        print(privkey)
        # create a new recoverable 65 byte ECDSA signature
        sig = secp256k1_ffi.new("secp256k1_ecdsa_recoverable_signature *")
        # parse a compact ECDSA signature (64 bytes + recovery id)
        # returns: 1 = deterministic; 0 = not deterministic
        deterministic = secp256k1_lib.secp256k1_ecdsa_sign_recoverable(
            privkey.ctx,  # initialized context object
            sig,  # array where signature is held
            digest,  # 32-byte message hash being signed
            privkey.private_key,  # 32-byte secret key
            secp256k1_ffi.NULL,  # default nonce function
            ndata,  # incrementing nonce data
        )
        if not deterministic:
            print("not deterministic, try again...")
            continue
        # we derive the recovery parameter
        # which simplifies the verification of the signature
        # it links the signature to a single unique public key
        # without this parameter, the back-end would need to test
        # for multiple public keys instead of just one
        signature, i = privkey.ecdsa_recoverable_serialize(sig)
        # we ensure that the signature is canonical; simplest form
        if canonical(signature):
            # add 4 and 27 to stay compatible with other protocols
            i += 4  # compressed
            i += 27  # compact
            # and have now obtained our signature
            break
    # having derived a valid canonical signature
    # we format it in its hexadecimal representation
    # and add it our transactions signatures
    # note that we do not only add the signature
    # but also the recovery parameter
    # this kind of signature is then called "compact signature"
    signature = hexlify(pack("<B", i) + signature).decode("ascii")
    tx["signatures"].append(signature)
    print(it("blue", 'tx["signatures"].append(signature)'))
    print(signature)
    print("")
    return tx


def verify_transaction(tx):
    """
    gist.github.com/xeroc/9bda11add796b603d83eb4b41d38532b
    once you have derived your new tx including the signatures
    verify your transaction and it's signature
    """
    print(it("blue", "verify_transaction"))
    print(it("blue", "tx2 = Signed_Transaction(**tx)"))
    tx2 = Signed_Transaction(**tx)
    print(tx2)
    print(it("blue", 'tx2.deriveDigest("BTS")'))
    tx2.deriveDigest("BTS")
    print(it("blue", "pubkeys = [PrivateKey(wif).pubkey]"))
    pubkeys = [PrivateKey(wif).pubkey]
    print(pubkeys)
    print(it("blue", 'tx2.verify(pubkeys, "BTS")'))
    tx2.verify(pubkeys, "BTS")
    return tx


# THE BROKER METHOD
def broker(order):
    """
    broker(order) --> execute(signal, order)

    insistent timed multiprocess wrapper for authorized ops
    if command does not execute in time: terminate and respawn
    serves to force disconnect websockets if hung
    up to ATTEMPTS chances; each PROCESS_TIMEOUT long: else abort
    signal is switched to 0 after execution to end the process
    """
    log_in = order["edicts"][0]["op"] == "login"
    signal = Value("i", 0)
    auth = Value("i", 0)
    i = 0
    while (i < ATTEMPTS) and not signal.value:
        i += 1
        print("")
        print("manualSIGNING authentication attempt:", i, ctime())
        child = Process(target=execute, args=(signal, log_in, auth, order))
        child.daemon = False
        child.start()
        if JOIN:  # means main script will not continue till child done
            child.join(PROCESS_TIMEOUT)
        # to parallel process a broker(order) see microDEX.py
    authorized = False
    if log_in and auth.value == 1:
        authorized = True

    return authorized


def execute(signal, log_in, auth, order):
    """
    build, serialize, sign, verify, and broadcast the transaction; log receipt to file
    """
    global nodes, account_id, account_name, wif, login, authenticated

    login = log_in

    start = time()
    if not DEV:  # disable printing with DEV=False
        block_print()
    nodes = order["nodes"]
    account_name = order["header"]["account_name"]
    wif = order["header"]["wif"]
    try:
        account_id = order["header"]["account_id"]
    except:
        pass
    wss_handshake()
    tx, message, signed_tx, verified_tx, broadcasted_tx = "", "", "", "", ""
    if not DEV:
        enable_print()
    try:
        tx = build_transaction(order)
    except Exception as e:
        trace(e)
    if tx["operations"]:  # if there are any orders
        if not DEV:  # disable printing with DEV=False
            block_print()
        authenticated = False
        # perform ecdsa on serialized transaction
        try:
            tx, message = serialize_transaction(tx)
        except Exception as e:
            tx = message = trace(e)
        try:
            signed_tx = sign_transaction(tx, message)
        except Exception as e:
            signed_tx = trace(e)
        if login:
            # PublicKey.__init__ switches "authenticated"
            if not DEV:
                enable_print()
            print("authenticated", authenticated)
            if authenticated:
                auth.value = 1
        else:
            try:
                verified_tx = verify_transaction(signed_tx)
            except Exception as e:
                verified_tx = trace(e)
            if not DEV:
                enable_print()
            try:
                sleep(5)
                broadcasted_tx = rpc_broadcast_transaction(verified_tx)
            except Exception as e:
                broadcasted_tx = trace(e)

        current_time = {
            "unix": int(time()),
            "local": ctime() + " " + strftime("%Z"),
            "utc": asctime(gmtime()) + " UTC",
        }
        receipt = {
            "time": current_time,
            "order": order["edicts"],
            "tx": tx,
            "message": message,
            "signed_tx": signed_tx,
            "verified_tx": verified_tx,
            "broadcasted_tx": broadcasted_tx,
        }
        now = str(ctime())
        # race_write(
        #     doc=(now + order["edicts"][0]["op"] + "_transaction_receipt.txt"),
        #     text=receipt,
        # )
    else:
        print(it("red", "manualSIGNING rejected your order"), order["edicts"])
    print("manualSIGNING process elapsed: %.3f sec" % (time() - start))
    print("")
    signal.value = 1
