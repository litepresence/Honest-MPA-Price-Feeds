<img src="https://github.com/litepresence/Honest-MPA-Price-Feeds/blob/master/docs/Screenshot.png">	


# Honest-MPA-Price-Feeds
Honest Price Feeds for Bitshares Market Pegged Assets

We are currently feeding an HONEST price hourly to 46 BitShares Market Pegged Assets: 

These are backed by the BTS core token as collateral, meaning you "borrow them into existence" with Bitshares:

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

(The `SHORT` tokens are fed the inverse (`1 / `) of their base price, see [this document](short_tokens.md) for more details.)

These are backed by HONEST.BTC as collateral, meaning you "borrow them into existence" with HONEST Bitcoin:

    HONEST.ETH1
    HONEST.XRP1

NOTE: The HONEST.BTC backed MPA's are unique in the Bitshares ecosystem as they are the only MPA backed MPA's on the DEX.   In this regard they are an exotic, experimental financial instrument. 

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


> The pricefeed script for the HONEST mpa's used to provide additional functionality called `sceletus`.  This aspect of the script performed a dust quantity wash trade once per hour to provide a historical chart reference rate.   This functionality has since been removed to simplify the script, but there remains a `honest_cross_rates.txt` file in the `pipe` folder so that custom or 3rd party sceletus scripts may use HONEST's curated price data.


You are now ready to deploy live.   Run `HONEST.py` in the terminal.  Choose `y + Enter` to enable publishing.  

    NOTE: You should certainly familiarize yourself with the scripts provided at this point
    you are about to enter your private keys which provide COMPLETE ACCESS TO YOUR FUNDS
    you SHOULD PERSONALLY ENSURE that you have read, understand, and trust the source code

Then enter your BitShares `username` and `wif`.   Press `Enter` one last time and you are now an offical price feed producer for HONEST market pegged assets.   Welcome to the team!

From time to time this Github repository will be updated.  Please check in regularly at the HONEST mpa development room on telegram.  Whenever you update, we suggest using `git pull` rather than the `Download ZIP` button, so that should there be any errors in the latest development branch, it would then be easier to revert using `git checkout <commit-hash>`.


To sign up as a feed producer for HONEST market pegged assets on Bitshares Blockchain find me on telegram, I'm a chat mod in the groups:

https://t.me/bitshares_community

https://t.me/bitsharesDEX

or via email:

finitestate@tutamail.com

We are seeking python competent individuals, with a linux box, familiar with Austrian economics, with reliable high speed internet, who have a strong ethical outlook towards the crypto community. 

For more information, please visit the ANNOUNCEMENT thread at: https://bitsharestalk.org/index.php?topic=32035


HONEST BDFL,

litepresence2020 & squidKid-deluxe 2025
