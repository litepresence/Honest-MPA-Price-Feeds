WHITEPAPER
================

HONEST Market Pegged Assets (Bitshares Private MPA's) Price Feed Methodology

PART A
===================

Using direct exchange public API ties, the MEDIAN BTC:USD from "legitimate" top high volume audited markets is calculated.   We are currently including:

- Coinbase BTC:USD
- Bitfinex BTC:USD
- Kracken XBT:USD
- Bittrex BTC:USD
- Bitstamp BTC:USD

These exchanges pairs have been shown to move within 1% of each other for several consecutive years by independent auditors.   We will at our discretion include or disclude exchanges to accurately define a global BTC:USD real time median price.   We are choosing median over mean as mean can be skewed by a single outlier.

We considering the auditing processes as described by these sources:

- Exchange Server Security Ranking at hacken.io
- adjusted legitimate volume at https://www.coingecko.com/en/exchanges  
- adjusted legitimate volume at https://www.comaps.io/exchanges/24h/1
- liquidity ranking at https://coinmarketcap.com/rankings/exchanges/liquidity/

As well as methodologies on Cryptocurrency Exchange Legitimacy described in these reports:

- Bitwise https://www.sec.gov/comments/sr-nysearca-2019-01/srnysearca201901-5164833-183434.pdf
- Chainalysis https://blog.chainalysis.com/reports/fake-trade-volume-cryptocurrency-exchanges
- Alameda Research https://ftx.com/volume-report-paper.pdf
- Comaps https://medium.com/comaps/methodology-for-reporting-reliable-liquidity-indicators-of-the-cryptocurrency-market-f8a278af7628
- Coingecko https://blog.coingecko.com/trust-score-2/

It should be understood that there are less than 15 legitimate volume exchanges in the world today despite the fact that we find hundreds of exchanges reporting high volume internally.  Most of this is fraudulent and we find it imparative to provide clean HONEST pricefeeds from exchanges with real audited volume. 

Additionally, we are puposefully excluding these otherwise "legitimate volume" TETHER markets to mitigate pricefeed risks associated with the USD:USDT derivative class:

- Poloniex BTC:USDT
- Binance BTC:USDT

Likewise we will not consider feeds from other USD derivatives such as USDC, etc. 

PART B
====================

Bittrex, Binance, and Poloniex offer BTC:BTS markets.   We will create a MEDIAN of these prices and consider it as our global median centralized exchange Bitshares to Bitcoin ratio.  These three exchange feeds were chosen with the same methodology described in PART A

PART C
====================

Using the methodolgy described in the metanode whitepaper at liteprence.com we will be collecting Bitshares public API data from the statistical MODE of all public feeds; the most common reported prices, streaming real time.  

We will be considering 4 gateway Bitcoin to Bitshares prices:

- GDEX.BTC:BTS
- RUDEX.BTC:BTS
- SPARKDEX.BTC:BTS 
- XBTSX.BTC:BTS 

Like the Centralized Exchange Prices, we will take the MEDIAN of these prices as reported by the MODE of public API's. 

The dex also has "USD":BTS pairs:

- GDEX.USDT:BTS
- RUDEX.USDT:BTS
- SPARKDEX.USD:BTS 
- XBTSX.USDT:BTS 

of them, only sparkdex is actually a USD gateway, the remainder are TETHER derivatives.   Sparkdex at this time has low volume and wih the remainder of USD markets being tether we have chosen to ignore these dex markets in our calculations.


PART D
====================

In forex markets we are able to cast a much broad net to gain reliable pricing of USD:FOREX pairs.   Using web scraping methods as well as direct api ties to free data sources we attain data with resolution of 1 HOUR or lower latency from the following sources:

Web Scraping (most are low latency (< 5 seconds "last price") all are less than 1 hour delay):

- fxcm
- wocu
- oanda
- liveusd
- fxempire
- cryptocompare
- bitcoinaverage
- alphavantage
- freeforex
- finviz
- yahoo
- wsj
- duckduckgo
- bloomberg

Direct API ties with keys for free data once per hour. (Most are 1 hour delay, some as low as 5 minute)

- fcsapi
- WorldCoinIndex
- datadt
- barchart
- fxmarketapi
- api.forex
- fixer.io
- OpenExchangeRates
- AlphaVantage
- currencyconverterapi
- truefx

*NOTE: as of Jan 18th the API based wrappers are not yet developed

Given these various sources for free data, our goal will be to maintain a population size of at least 10 sources of hourly or finer resolution data for forex markets we support. We will not include any 24 hour delayed data, moving averages, or otherwise post calculated data.   Given the exact prices provided by each of these sources we will be reporting the MEDIAN USD:FOREX for each pair we support.

FOREX:BTS AGGREATES
====================

The median CEX BTC:BTS and the median DEX gatewayBTC:BTS will then be averaged to find the mean of medians BTC:BTS price thusly:

Final Feed Price for HONEST.BTC:BTS = (cexBTC:BTS + dexBTC:BTS)/2

The HONEST.USD:BTS price is then:

HONEST.USD:BTS = cexBTC:USD * HONEST.BTC:BTS

then the HONEST forex prices will use the values derived in part D:

HONEST.CNY:BTS = HONEST.USD:BTS * medianUSD:CNY

etc.

Initially, we will be creating 3 pricefeeds:

HONEST.BTC:BTS
HONEST.USD:BTS
HONEST.CNY:BTS

THE FUTURE
====================

In time, we hope to add EUR, RUB, JPY, KRW HONEST market: 

- HONEST.RUB:BTS = HONEST.USD:BTS * medianUSD:RUB
- HONEST.EUR:BTS = HONEST.USD:BTS * medianUSD:EUR
- HONEST.JPY:BTS = HONEST.USD:BTS * medianUSD:JPY
- HONEST.KRW:BTS = HONEST.USD:BTS * medianUSD:KRW

Upon success of these markets, using similiar methology, we will seek to bring you additional Market Pegged Assets with HONEST feed prices for top crypto markets, initially supporting:

- HONEST.LTC
- HONEST.ETH
- HONEST.EOS
- HONEST.XRP

FINAL NOTE
==================

Our company, HONEST will be maintaining (TBD) pricefeed producers.   Pricefeed producers will be chosen from our associate HONEST members through lottery and switched quarterly.   We will seek to use low cost or zero cost hosting services to post our price feeds to the DEX.   We will be updating hour feeds hourly.   A thorough and live accounting our individual streaming feeds will also be made available through jsonbin.io.   Market fees from the markets supported by HONEST MPA's will be split amongst pricefeed producers.   The market volume created by producing HONEST pricefeeds will incentivize hour pricefeed producers to keep their feeds forever HONEST. 

HONEST CTO and BDFL,

litepresence2020 


Woe to the pot which claims the kettle is not black!


