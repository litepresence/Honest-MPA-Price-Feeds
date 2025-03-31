<img src="https://github.com/litepresence/Honest-MPA-Price-Feeds/blob/master/docs/Screenshot.png">	


# Honest-MPA-Price-Feeds
Honest Price Feeds for Bitshares Market Pegged Assets

We are currently feeding an HONEST price hourly to 46 BitShares Market Pegged Assets: 

These are all fundamentally backed by the Bitshares core token (BTS) as collateral, meaning you "borrow them into existence" with BTS:

    HONEST.CNY
    HONEST.USD
    HONEST.BTC
    HONEST.XAU
    HONEST.XAG
    HONEST.ETH
    HONEST.XRP
    HONEST.USDSHORT
    HONEST.BTCSHORT
    HONEST.ADA
    HONEST.DOT
    HONEST.LTC
    HONEST.SOL
    HONEST.XMR
    HONEST.ATOM
    HONEST.XLM
    HONEST.ALGO
    HONEST.FIL
    HONEST.EOS
    HONEST.RUB
    HONEST.EUR
    HONEST.GBP
    HONEST.JPY
    HONEST.KRW
    HONEST.ADASHORT
    HONEST.DOTSHORT
    HONEST.LTCSHORT
    HONEST.SOLSHORT
    HONEST.XMRSHORT
    HONEST.ATOMSHORT
    HONEST.XLMSHORT
    HONEST.ALGOSHORT
    HONEST.FILSHORT
    HONEST.EOSSHORT
    HONEST.RUBSHORT
    HONEST.EURSHORT
    HONEST.GBPSHORT
    HONEST.JPYSHORT
    HONEST.KRWSHORT
    HONEST.XRPSHORT
    HONEST.ETHSHORT
    HONEST.XAUSHORT
    HONEST.XAGSHORT
    HONEST.CNYSHORT

(The `SHORT` tokens are fed the inverse (`1 / oracle`) of their base price, see [this document](short_tokens.md) to learn more about HONEST SHORT.)

The following two tokens are backed by HONEST.BTC as collateral, meaning you "borrow them into existence" with HONEST.BTC:

    HONEST.ETH1
    HONEST.XRP1

The HONEST.BTC backed MPA's are unique in the Bitshares ecosystem as they are the only MPA backed MPA's on the DEX.   

# Installation
You should be on a linux box with latest python version installed (3.7 or better).

First, perform these commands:

```bash
sudo apt-get update
sudo apt-get install pkg-config
sudo apt-get install libffi-dev
sudo apt-get install libsecp256k1-dev
```
You will then need to install the `requirements.txt`:

```bash
pip install -r requirements.txt
```

If that fails you may need to set up a virtual enviroment for python3.9+, which is outside the scope of this document.  See [here](https://realpython.com/python-virtual-environments-a-primer/) for instructions.

HONEST feeds use a package called `bitshares-signing` that is having trouble getting pypi installation to work, thus you must install it via git & pip:

```bash
git clone https://github.com/squidKid-deluxe/bitshares-signing.git
cd bitshares-signing
pip install -e .
```

> This is a temporary workaround and will be fixed in the near future.

---


There is a streaming file `honest_cross_rates.txt` in the `pipe` folder so that custom or 3rd party integrations may use HONEST's curated price data.


You are now ready to deploy live.   Run `HONEST.py` in the terminal.  Choose `y + Enter` to enable publishing.  

    NOTE: You should certainly familiarize yourself with the scripts provided at this point
    you are about to enter your private keys which provide COMPLETE ACCESS TO YOUR FUNDS
    you SHOULD PERSONALLY ENSURE that you have read, understand, and trust the source code

Then enter your BitShares `username` and `wif`.   Press `Enter` one last time and you are now an offical price feed producer for HONEST market pegged assets.   Welcome to the team!

From time to time this Github repository will be updated.  Please check in regularly at the HONEST mpa development room on telegram.  Whenever you update, we suggest using `git pull` rather than the `Download ZIP` button, so that should there be any errors in the latest development branch, it would then be easier to revert using `git checkout <commit-hash>`.


I'm a chat mod in https://t.me/bitsharesDEV

or contact me via email:

f i n i t e s t a t e @tutamail.com

HONEST BDFL,

litepresence
