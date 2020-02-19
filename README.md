# Honest-MPA-Price-Feeds
Honest Price Feeds for Bitshares Market Pegged Assets

We are currently feeding an HONEST price hourly to 9 BitShares Market Pegged Assets: 

These are backed by the BTS core token as collateral:

    HONEST.CNY (CHINESE YUAN)
    HONEST.BTC (BITCOIN)
    HONEST.USD (US DOLLAR)
    HONEST.XAU (GOLD)
    HONEST.XAG (SILVER)
    HONEST.ETH (ETHEREUM)
    HONEST.XRP (RIPPLE)

These are backed by HONEST.BTC as collateral:

    HONEST.ETH1 (ETHEREUM)
    HONEST.XRP1 (RIPPLE)

# Installation
You should be on a linux box with latest python version installed (3.7 or better).

First, perform these commands:

    sudo apt-get update
    sudo apt-get install pkg-config
    sudo apt-get install libsecp256k1-dev

You will then need to manually pip3 install the following dependencies (sorry no setup.py yet):

    pip3 install requests
    pip3 install cfscrape
    pip3 install psutil
    pip3 install websocket-client
    pip3 install ecdsa
    pip3 install secp256k1

Then clone the repo, be sure to include the empty `/pipe/` folder!  It will be used for text pipe inter process communication.

Next, in terminal, navigate to the folder containing pricefeed_final.py and run it:

    python3 pricefeed_final.py 
  
On your system, you may need to specify the python sub-version explicitly, like this:
  
    python3.8 pricefeed_final.py 
  
Then press `Enter` 4 times to skip `publish`, `jsonbin`, `sceletus`, and `cancel` functionality for now.  Just confirm a demo works and you have all dependencies loaded.   Once it is loaded; it takes about 3 minutes, exit the script:

    ctrl + shift + \

to set up www.jsonbin.io functionality:

`config_api.py` will need the configuration dictionary values updated for `jsonbin: key:` edited and the script saved.  You get that `key` at www.jsonbin.io in the `api keys` tab, after signing up for their service.   After installing the `key`, run the jsonbin.py script ONCE in the terminal with the command:

    python3 jsonbin.py 
    
The script will print a `BIN ID`.  Next, install the `id` you just generated in the `config_api.py` script where it belongs as the `jsonbin: id:`; just under where you just installed the `jsonbin: key:`.   

Then you can now test the `jsonbin` functionality of the `pricefeed_final.py` script.  In terminal:

    python3 pricefeed_final.py

Press `y + Enter` when prompted at startup by the `jsonbin` question.   For all other question, just press `Enter` to skip the other functions for now.   `pricefeed_final.py` will now use the `jsonbin.py` with the `BIN ID` you installed in `config_api.py` as a module to upload your data matrix for the public to see.

To view your `jsonbin` and ensure everything is working correctly, visit:

https://api.jsonbin.io/b/<your_bin_id>/latest (be sure to install your bin id where it goes in the link)

In `config_api.py` you have a place to store this web address marked `jsonbin: url:`; this is not strictly necessary, but you should at the very least bookmark your `jsonbin` in a web browser, to check up on it later.  Be sure to include `/latest` on the end of the url, as the `jsonbin` will contain a historic copy of every upload you make.  Without `latest` the url points to the first upload and will appear to not update.

Next, you will need to sign up at several forex sites to access their api data.   Open the `config_api.py` file again.  It contains several forex data site urls for you to visit and attain keys.  Each of these sites provides FREE data, all you need is an email address.  Install the keys into the dictionary provided, in their respective places; then save the file.  Also, save your password for each site someplace safe. 

Be sure to inform us in the HONEST mpa development room of your `jsonbin id` so we can add it to the announce thread at https://bitsharestalk.org/index.php?topic=32035

Finally, the pricefeed script for the HONEST mpa's provides additional functionality called `SCELETUS`.  This aspect of the script performs a dust quantity wash trade once per hour to provide a historical chart reference rate.   Each price feed producer is expected to assist with this process as a marketing tool to display the accuracy of our pricefeeds over time.  The annual blockchain transaction cost of these operations is expected to be less than $10.   Each user has been assigned markets to sceletus.  Open `config_sceletus.py` to find the markets assigned to you.  Edit the uncommented return statement accordingly with the commented out statement assigned to you, then save the file.   You will also need to manually purchase or borrow about 100 BTS (currently $3 value) of each instrument you've been assigned to sceletus to enact the buy and sell wash trade.  It should be noted both the buy and sell will be performed by one account.  

You are now ready to deploy live.   Run `pricefeed_final.py` in the terminal.  Choose `y + Enter` for all four initial questions asked by the script.  

    NOTE: You should certainly familiarize yourself with the scripts provided at this point
    you are about to enter your private keys which provide COMPLETE ACCESS TO YOUR FUNDS
    you SHOULD PERSONALLY ENSURE that you have read, understand, and trust the source code

Then enter your BitShares `username` and `wif`.   Press `Enter` one last time and you are now an offical price feed producer for HONEST market pegged assets.   Welcome to the team!

From time to time the github will be updated.   Please check in regularly at the HONEST mpa development room on telegram.   Whenever you git clone the repo to update, please save a copy of the previous version on your local hard drive.   This will make reverting easier should there be any errors in the latest development branch.   
    
To sign up as a feed producer for HONEST market pegged assets on Bitshares Blockchain find me on telegram, I'm a chat mod in the groups:

https://t.me/bitshares_community
https://t.me/bitsharesDEX

or via email:

finitestate@tutamail.com

We are seeking python competent individuals, with a linux box, familiar with Austrian economics, with reliable high speed internet, who have a strong ethical outlook towards the crypto community. 

For more information, please visit the ANNOUNCEMENT thread at: https://bitsharestalk.org/index.php?topic=32035


HONEST BDFL,

litepresence2020
