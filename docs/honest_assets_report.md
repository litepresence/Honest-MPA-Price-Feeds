# HONEST Market Pegged Assets — Live Attributes

Generated 2026-08-08T21:33:07Z UTC from live blockchain data (head block 113303223 via wss://dex.iobanker.com/ws).

Fee semantics (BSIP-81): `market_fee_percent` = **maker** fee, `taker_fee_percent` (asset extension) = **taker** fee. When `taker_fee_percent` is unset the taker fee falls back to the maker rate. Percent values are stored in hundredths of a percent (100 == 1%).

## 1. Maker / Taker Fees

Columns uniformly padded by `md_table` helper so the table lines up even in fixed-width output.

| Asset            | Maker | Taker | taker explicit     | max_market_fee   | fee enabled |
| ---------------- | ----- | ----- | ------------------ | ---------------- | ----------- |
| HONEST.ADA       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ADASHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ALGO      | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ALGOSHORT | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ATOM      | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ATOMSHORT | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.BTC       | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.BTCSHORT  | 0.00% | 0.20% | yes                | 1000000000       | yes         |
| HONEST.CNY       | 0.10% | 0.10% | no (same as maker) | 1000000000000000 | yes         |
| HONEST.CNYSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.DOT       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.DOTSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.EOS       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.EOSSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.ETH       | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.ETH1      | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.ETHSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.EUR       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.EURSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.FIL       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.FILSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.GBP       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.GBPSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.JPY       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.JPYSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.KRW       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.KRWSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.LTC       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.LTCSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.RUB       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.RUBSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.SOL       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.SOLSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.USD       | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.USDSHORT  | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.XAG       | 0.10% | 0.10% | no (same as maker) | 1000000000000000 | yes         |
| HONEST.XAGSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XAU       | 0.10% | 0.10% | no (same as maker) | 0                | yes         |
| HONEST.XAUSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XLM       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XLMSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XMR       | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XMRSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |
| HONEST.XRP       | 0.00% | 0.20% | yes                | 1000000000000000 | yes         |
| HONEST.XRP1      | 0.10% | 0.10% | no (same as maker) | 1000000000000000 | yes         |
| HONEST.XRPSHORT  | 0.00% | 0.00% | no (same as maker) | 100000000000000  | yes         |

## 2. Claimable / Accumulated Fees (unclaimed revenue)

`accumulated_fees` sit in each asset's dynamic object and are claimable by the issuer (e.g. via `asset_claim_fees`) _in that asset_. `accumulated_collateral_fees` are BTS collected from margin calls. The `~value (BTS)` column converts the on-chain `accumulated_fees` from MPA units into BTS using the MPA's live median feed: `value = accumulated_fees/10^precision * (feed_quote_BTS / feed_base_MPA)`.

**BTC-collateralized MPAs (HONEST.ETH1, HONEST.XRP1) have a feed denominated in HONEST.BTC, not BTS.** For those, the BTS per-asset factor of their BTS-backed counterpart (HONEST.ETH / HONEST.XRP) is used instead; this is shown in the `feed` column as `via <counterpart>`.

| Asset            | accumulated_fees (asset units) | ~value (BTS) | accumulated_collat (BTS) | feed           |
| ---------------- | ------------------------------ | ------------ | ------------------------ | -------------- |
| HONEST.ADA       | 0.0000                         | 0.00         | 0.10                     | yes            |
| HONEST.ADASHORT  | 0.0000                         | 0.00         | 0.01                     | yes            |
| HONEST.ALGO      | 0.0000                         | 0.00         | 0.04                     | yes            |
| HONEST.ALGOSHORT | 0.0000                         | 0.00         | 0.04                     | yes            |
| HONEST.ATOM      | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.ATOMSHORT | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.BTC       | 0.0003                         | 16133.85     | 2867.13                  | yes            |
| HONEST.BTCSHORT  | 4475612.0200                   | 0.07         | 0.00                     | yes            |
| HONEST.CNY       | 0.0000                         | 0.00         | 543.40                   | yes            |
| HONEST.CNYSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.DOT       | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.DOTSHORT  | 0.0000                         | 0.00         | 0.02                     | yes            |
| HONEST.EOS       | 0.0000                         | 0.00         | 1672.23                  | yes            |
| HONEST.EOSSHORT  | 0.0000                         | 0.00         | 4.18                     | yes            |
| HONEST.ETH       | 0.0000                         | 70.20        | 1387.75                  | yes            |
| HONEST.ETH1      | 0.0586                         | 102873.66    | 0.27                     | via HONEST.ETH |
| HONEST.ETHSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.EUR       | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.EURSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.FIL       | 0.0000                         | 0.00         | 0.05                     | yes            |
| HONEST.FILSHORT  | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.GBP       | 0.0000                         | 0.00         | 0.02                     | yes            |
| HONEST.GBPSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.JPY       | 0.0000                         | 0.00         | 0.02                     | yes            |
| HONEST.JPYSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.KRW       | 0.0000                         | 0.00         | 0.02                     | yes            |
| HONEST.KRWSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.LTC       | 0.0000                         | 0.00         | 48.51                    | yes            |
| HONEST.LTCSHORT  | 0.0000                         | 0.00         | 0.06                     | yes            |
| HONEST.RUB       | 0.0000                         | 0.00         | 5.06                     | yes            |
| HONEST.RUBSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.SOL       | 0.0000                         | 0.00         | 9.82                     | yes            |
| HONEST.SOLSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.USD       | 16.1262                        | 14746.57     | 8759.79                  | yes            |
| HONEST.USDSHORT  | 401.2705                       | 0.44         | 0.00                     | yes            |
| HONEST.XAG       | 0.0001                         | 4.07         | 1.55                     | yes            |
| HONEST.XAGSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.XAU       | 0.0001                         | 407.33       | 6115.57                  | yes            |
| HONEST.XAUSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.XLM       | 0.0000                         | 0.00         | 3.33                     | yes            |
| HONEST.XLMSHORT  | 0.0000                         | 0.00         | 0.01                     | yes            |
| HONEST.XMR       | 0.0000                         | 0.00         | 0.67                     | yes            |
| HONEST.XMRSHORT  | 0.0000                         | 0.00         | 0.04                     | yes            |
| HONEST.XRP       | 1.7602                         | 1677.46      | 3.80                     | yes            |
| HONEST.XRP1      | 0.0454                         | 43.29        | 0.00                     | via HONEST.XRP |
| HONEST.XRPSHORT  | 0.0000                         | 0.00         | 0.01                     | yes            |

### Totals

- **accumulated fees (BTS value, approx):** 135,956.94 BTS
- **accumulated collateral fees:** 21,423.64 BTS
- **combined claimable (approx):** 157,380.58 BTS

## 3. Supply & Money (dynamic state)

`current_supply` is what is minted/circulating, `confidential_supply` the blinded portion, and `fee_pool` the asset's own BTS-valued fee reserve (claimable by the issuer). All shown in asset units.

| Asset            | current_supply     | confidential_supply | fee_pool |
| ---------------- | ------------------ | ------------------- | -------- |
| HONEST.ADA       | 0.1940             | 0.0000              | 0.0000   |
| HONEST.ADASHORT  | 523.8289           | 0.0000              | 0.0000   |
| HONEST.ALGO      | 0.2436             | 0.0000              | 0.0000   |
| HONEST.ALGOSHORT | 720.2089           | 0.0000              | 0.0000   |
| HONEST.ATOM      | 0.0042             | 0.0000              | 0.0000   |
| HONEST.ATOMSHORT | 11,111.5288        | 0.0000              | 0.0000   |
| HONEST.BTC       | 0.0320             | 0.0000              | 0.0000   |
| HONEST.BTCSHORT  | 2,508,484,268.5200 | 0.0000              | 0.0000   |
| HONEST.CNY       | 107.0976           | 0.0000              | 0.0000   |
| HONEST.CNYSHORT  | 579.1732           | 0.0000              | 0.0000   |
| HONEST.DOT       | 0.0217             | 0.0000              | 0.0000   |
| HONEST.DOTSHORT  | 7,512.4193         | 0.0000              | 0.0000   |
| HONEST.EOS       | 10.6585            | 0.0000              | 0.0000   |
| HONEST.EOSSHORT  | 239,906.7278       | 0.0000              | 0.0000   |
| HONEST.ETH       | 0.0660             | 0.0000              | 0.0000   |
| HONEST.ETH1      | 0.0673             | 0.0000              | 0.0000   |
| HONEST.ETHSHORT  | 1,331,981.8900     | 0.0000              | 0.0000   |
| HONEST.EUR       | 0.0403             | 0.0000              | 0.0000   |
| HONEST.EURSHORT  | 1,612.9240         | 0.0000              | 0.0000   |
| HONEST.FIL       | 0.0138             | 0.0000              | 0.0000   |
| HONEST.FILSHORT  | 6,359.2658         | 0.0000              | 0.0000   |
| HONEST.GBP       | 0.0518             | 0.0000              | 0.0000   |
| HONEST.GBPSHORT  | 2,627.6180         | 0.0000              | 0.0000   |
| HONEST.JPY       | 21.0893            | 0.0000              | 0.0000   |
| HONEST.JPYSHORT  | 100.8109           | 0.0000              | 0.0000   |
| HONEST.KRW       | 80.5917            | 0.0000              | 0.0000   |
| HONEST.KRWSHORT  | 4.0835             | 0.0000              | 0.0000   |
| HONEST.LTC       | 3.3777             | 0.0000              | 0.0000   |
| HONEST.LTCSHORT  | 691,968.1023       | 0.0000              | 0.0000   |
| HONEST.RUB       | 14.2632            | 0.0000              | 0.0000   |
| HONEST.RUBSHORT  | 21.8345            | 0.0000              | 0.0000   |
| HONEST.SOL       | 0.0210             | 0.0000              | 0.0000   |
| HONEST.SOLSHORT  | 39,091.6102        | 0.0000              | 0.0000   |
| HONEST.USD       | 1,740.2270         | 0.0000              | 0.0000   |
| HONEST.USDSHORT  | 441,416.2855       | 0.0000              | 0.0000   |
| HONEST.XAG       | 0.2400             | 0.0000              | 0.0000   |
| HONEST.XAGSHORT  | 232,116.2170       | 0.0000              | 0.0000   |
| HONEST.XAU       | 0.0150             | 0.0000              | 0.0000   |
| HONEST.XAUSHORT  | 40,255,892.1600    | 0.0000              | 0.0000   |
| HONEST.XLM       | 111.2562           | 0.0000              | 0.0000   |
| HONEST.XLMSHORT  | 208.0542           | 0.0000              | 0.0000   |
| HONEST.XMR       | 0.0015             | 0.0000              | 0.0000   |
| HONEST.XMRSHORT  | 919,395.7070       | 0.0000              | 0.0000   |
| HONEST.XRP       | 49.2232            | 0.0000              | 0.0000   |
| HONEST.XRP1      | 2.7897             | 0.0000              | 0.0000   |
| HONEST.XRPSHORT  | 1,434.8601         | 0.0000              | 0.0000   |

## 4. Collateral & Settlement (MPA bitasset state)

Current maintenance/initial collateralization is the live collateral-per-debt price (backing units per 1 MPA) the chain maintains; a low/dropping maintenance value indicates the market is closer to margin calls. Feed age is minutes since the last published oracle feed. `settling` is true when a forced-settlement is in progress.

| Asset            | backing    | maint coll (back/MPA) | init coll (back/MPA) | feed age (min) | margin-call fee | force-settle fee | black-swan  | settling |
| ---------------- | ---------- | --------------------- | -------------------- | -------------- | --------------- | ---------------- | ----------- | -------- |
| HONEST.ADA       | BTS        | 256.3551              | 256.3551             | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ADASHORT  | BTS        | 0.0076                | 0.0076               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ALGO      | BTS        | 112.1501              | 112.1501             | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ALGOSHORT | BTS        | 0.0174                | 0.0174               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ATOM      | BTS        | 1,773.4209            | 1,773.4209           | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ATOMSHORT | BTS        | 0.0011                | 0.0011               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.BTC       | BTS        | 83,259,193.0538       | 83,259,193.0538      | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.BTCSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.CNY       | BTS        | 189.7259              | 189.7259             | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.CNYSHORT  | BTS        | 0.0103                | 0.0103               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.DOT       | BTS        | 1,049.0659            | 1,049.0659           | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.DOTSHORT  | BTS        | 0.0019                | 0.0019               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.EOS       | BTS        | 83.2176               | 83.2176              | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.EOSSHORT  | BTS        | 0.0235                | 0.0235               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ETH       | BTS        | 2,457,145.3664        | 2,457,145.3664       | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.ETH1      | HONEST.BTC | 0.0413                | 0.0413               | 43             | —               | —                | —           | no       |
| HONEST.ETHSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.EUR       | BTS        | 1,479.6121            | 1,479.6121           | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.EURSHORT  | BTS        | 0.0013                | 0.0013               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.FIL       | BTS        | 918.2849              | 918.2849             | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.FILSHORT  | BTS        | 0.0021                | 0.0021               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.GBP       | BTS        | 1,727.0786            | 1,727.0786           | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.GBPSHORT  | BTS        | 0.0011                | 0.0011               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.JPY       | BTS        | 8.1131                | 8.1131               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.JPYSHORT  | BTS        | 0.2408                | 0.2408               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.KRW       | BTS        | 0.9094                | 0.9094               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.KRWSHORT  | BTS        | 2.1478                | 2.1478               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.LTC       | BTS        | 58,947.5099           | 58,947.5099          | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.LTCSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.RUB       | BTS        | 15.6335               | 15.6335              | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.RUBSHORT  | BTS        | 0.1250                | 0.1250               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.SOL       | BTS        | 97,600.4647           | 97,600.4647          | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.SOLSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.USD       | BTS        | 1,280.2273            | 1,280.2273           | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.USDSHORT  | BTS        | 0.0015                | 0.0015               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XAG       | BTS        | 81,358.4443           | 81,358.4443          | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XAGSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XAU       | BTS        | 5,559,195.9465        | 5,559,195.9465       | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XAUSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XLM       | BTS        | 211.4372              | 211.4372             | 43             | 0.05%           | 2.50%            | payback all | no       |
| HONEST.XLMSHORT  | BTS        | 0.0092                | 0.0092               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.XMR       | BTS        | 488,515.2848          | 488,515.2848         | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.XMRSHORT  | BTS        | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.XRP       | BTS        | 1,334.1669            | 1,334.1669           | 43             | 0.05%           | 1.50%            | payback all | no       |
| HONEST.XRP1      | HONEST.BTC | 0.0000                | 0.0000               | 43             | 0.05%           | 2.50%            | payback all | yes      |
| HONEST.XRPSHORT  | BTS        | 0.0015                | 0.0015               | 43             | 0.05%           | 2.50%            | payback all | yes      |

## 5. Options Extensions (`asset_update` extensions)

`reward_percent` and `whitelist_market_fee_sharing` live in the asset options extensions (same place as `taker_fee_percent`) and implement BSIP-0043 market-fee sharing: `reward_percent` is the share of the asset's market fee paid out to the buyer's registrar/referrer, and `whitelist_market_fee_sharing` (if non-empty) restricts which accounts are eligible to receive those rewards.

| Asset       | reward_percent | whitelist_market_fee_sharing |
| ----------- | -------------- | ---------------------------- |
| HONEST.BTC  | 0.000000%      | —                            |
| HONEST.CNY  | 0.000000%      | —                            |
| HONEST.ETH  | 0.000000%      | —                            |
| HONEST.ETH1 | 0.000000%      | —                            |
| HONEST.USD  | 0.000000%      | —                            |
| HONEST.XAG  | 0.000000%      | —                            |
| HONEST.XAU  | 0.000000%      | —                            |
| HONEST.XRP  | 0.000000%      | —                            |
| HONEST.XRP1 | 0.000000%      | —                            |

## 6. Issuer Market-Fee-Sharing Vestings

- `CRUDE.LVRG` (`1.3.5882`): 11383.21 (11383206124 satoshis)
- `XBTSX.TUSC` (`1.3.6149`): 191581.57 (1915815708 satoshis)
- `BTS` (`1.3.0`): 3952.85 (395285191 satoshis)
- `XBTSX.HIVE` (`1.3.6013`): 0.24 (240437 satoshis)
- `XBTSX.USDT` (`1.3.5589`): 0.04 (43692 satoshis)
- `XBTSX.EOS` (`1.3.5877`): 0.01 (12925 satoshis)
- `XBTSX.RUB` (`1.3.5887`): 0.16 (1618 satoshis)
- `XBTSX.WRAM` (`1.3.6574`): 2.06 (206 satoshis)
- `DEFI` (`1.3.5925`): 0.00 (38 satoshis)
- `GDEX.USDT` (`1.3.5286`): 0.00 (23 satoshis)
- `CNY` (`1.3.113`): 0.00 (6 satoshis)
- `XBTSX.BTC` (`1.3.4157`): 0.00 (2 satoshis)
- `XBTSX.ETH` (`1.3.4760`): 0.00 (2 satoshis)
- `GDEX.BTC` (`1.3.2241`): 0.00 (1 satoshis)
*(via wss://dex.iobanker.com/ws)*

---
Generated by `honest/honest_assets_report.py`. Read-only; does not modify the chain.
