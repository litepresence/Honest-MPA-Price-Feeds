# Honest-MPA-Price-Feeds
Honest Price Feeds for Bitshares Market Pegged Assets

I am currently feeding an honest price hourly to 

# HONEST.CNY
on the Bitshares DEX

# Installation

you should be on a linux box with latest python version installed (3.7 or better)

you will need to pip install the following dependencies manually:

- requests
- cfscrape
- psutil
- websocket-client
- getpass
- ecdsa
- secp256k1

then clone the repo, be sure to include the `/pipe/` folder

then in terminal:

  python3 pricefeed_final.py 
  
or maybe on your system:
  
  python3.8 pricefeed_final.py 
  
then press enter twice to skip jsonbin and publication functionality for now

to set up jsonbin.io functionality

jsonbin.py will need the global constant JSONBIN_SECRET installed to add functionality, you get that at jsonbin.io in the api keys tab.   After installing the secret, run that script once in the terminal 

    python3 jsonbin.py 
    
it will spit out a BIN_ID you install that in the script... then you can test the jsonbin.io functionality of the pricefeed_final.py script (press y+Enter when prompted at startup) and it will use the jsonbin.py as a module.

to view your jsonbin, visit:

    https://api.jsonbin.io/b/<<< your bin id >>>/latest
    
to sign up as a feed producer for HONEST market pegged assets on Bitshares Blockchain find me on telegram, I'm a chat mod in the group:

https://t.me/bitshares_community

or via email:

finitestate@tutamail.com


