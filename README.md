# Honest-MPA-Price-Feeds
Honest Price Feeds for Bitshares Market Pegged Assets

We are currently feeding an HONEST price hourly to 9 BitShares Market Pegged Assets: 

These are backed by the BTS core token as collateral:
- HONEST.CNY (CHINESE YUAN)
- HONEST.BTC (BITCOIN)
- HONEST.USD (US DOLLAR)
- HONEST.XAU (GOLD)
- HONEST.XAG (SILVER)
- HONEST.ETH (ETHEREUM)
- HONEST.XRP (RIPPLE)

These are backed by HONEST.BTC as collateral:
- HONEST.ETH1 (ETHEREUM)
- HONEST.XRP1 (RIPPLE)

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
  
On your system, you may need to specify the python sub-version explicitly, thus:
  
    python3.8 pricefeed_final.py 
  
Then press enter 4 times to skip publication, jsonbin, sceletus, and cancel functionality for now.  Just confirm a demo works and you have all dependencies loaded.   Once it is loaded; it takes about 3 minutes, exit the script:

    ctrl + shift + \

to set up jsonbin.io functionality:

config_api.py will need the configuration dictionary values updated for `jsonbin key` edited and the script saved to add functionality.  You get that key at jsonbin.io in the api keys tab after signing up for their service.   After installing the secret, run that script once in the terminal with the command:

    python3 jsonbin.py 
    
The script will print a `BIN ID`.  You install that in the config_api.py script where it belongs as the `jsonbin id` just under where you just installed the `jsonbin key`.   

Then you can test the jsonbin.io functionality of the `pricefeed_final.py` script (press y+Enter when prompted at startup by the jsonbin question... just press enter to skipp all other functions for now) and it will now use the `jsonbin.py` with your `BIN_ID` as a module to upload your data matrix for the public to see

to view your jsonbin, visit:

https://api.jsonbin.io/b/<your_bin_id>/latest

In config_api.py you have a place to store this web address marked `jsonbin url`; this is not strictly necessary, but you should at the very least bookmark your jsonbin in a web browser to check up on it later.  

Next you will need to sign up at several forex sites to access their api data.   Open the config_api.py file again and it will contain several urls for you to visit and attain keys.   Install the keys into the dictionary provided, in their respective places then save the file. 

Be sure to inform us in the HONEST mpa development room of your `jsonbin id` so we can add it to the announce thread at www.bitsharestalk.org

Finally, the pricefeed script for the HONEST mpa's provides additional functionality called `SCELETUS`.  This aspect of the script performs a dust quantity wash trade once per hour to provide a historical chart reference rate.   Each price feed producer is expected to assist with this process as a marketing tool to display the accuracy of our pricefeeds over time.  This annual cost of these operations is expected to be less than $10.   Each user has been assigned markets to sceletus, open config_sceletus.py to find your markets, and edit the uncommented return statement accordingly.   You will also need to manually purchase about 100 BTS (currently $3 value) of each instrument you've been assigned to sceletus.  

You are now ready to deploy live.   Run pricefeed_final.py in the terminal.  Choose `y + Enter` for all four initial questions asked by the script.  Then enter your BitShares `username` and `wif`.   Press `Enter` one last time and you are now an offical price feed producer for HONEST market pegged assets.   Welcome to the team!

    
To sign up as a feed producer for HONEST market pegged assets on Bitshares Blockchain find me on telegram, I'm a chat mod in the groups:

https://t.me/bitshares_community
https://t.me/bitsharesDEX

or via email:

finitestate@tutamail.com

We are seeking python competent individuals, with a linux box, familiar with Austrian economics, with reliable high speed internet, who have a strong ethical outlook towards the crypto community. 

For more information, please visit the ANNOUNCEMENT thread at: https://bitsharestalk.org/index.php?topic=32035


HONEST BDFL,

litepresence2020
