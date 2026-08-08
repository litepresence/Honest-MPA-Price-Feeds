# HONEST Market Pegged Assets — Fees & Claimable Revenue

Generated 2026-08-08T19:14:52Z UTC from live blockchain data (head block 113300464 via wss://dex.iobanker.com/ws).

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
| HONEST.BTC       | 0.0003                         | 16113.71     | 2867.13                  | yes            |
| HONEST.BTCSHORT  | 4475612.0200                   | 0.08         | 0.00                     | yes            |
| HONEST.CNY       | 0.0000                         | 0.00         | 543.40                   | yes            |
| HONEST.CNYSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.DOT       | 0.0000                         | 0.00         | 0.03                     | yes            |
| HONEST.DOTSHORT  | 0.0000                         | 0.00         | 0.02                     | yes            |
| HONEST.EOS       | 0.0000                         | 0.00         | 1672.23                  | yes            |
| HONEST.EOSSHORT  | 0.0000                         | 0.00         | 4.18                     | yes            |
| HONEST.ETH       | 0.0000                         | 70.17        | 1387.75                  | yes            |
| HONEST.ETH1      | 0.0586                         | 102823.58    | 0.27                     | via HONEST.ETH |
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
| HONEST.USD       | 16.1262                        | 14732.74     | 8759.79                  | yes            |
| HONEST.USDSHORT  | 401.2705                       | 0.44         | 0.00                     | yes            |
| HONEST.XAG       | 0.0001                         | 4.07         | 1.55                     | yes            |
| HONEST.XAGSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.XAU       | 0.0001                         | 406.95       | 6115.57                  | yes            |
| HONEST.XAUSHORT  | 0.0000                         | 0.00         | 0.00                     | yes            |
| HONEST.XLM       | 0.0000                         | 0.00         | 3.33                     | yes            |
| HONEST.XLMSHORT  | 0.0000                         | 0.00         | 0.01                     | yes            |
| HONEST.XMR       | 0.0000                         | 0.00         | 0.67                     | yes            |
| HONEST.XMRSHORT  | 0.0000                         | 0.00         | 0.04                     | yes            |
| HONEST.XRP       | 1.7602                         | 1676.43      | 3.80                     | yes            |
| HONEST.XRP1      | 0.0454                         | 43.26        | 0.00                     | via HONEST.XRP |
| HONEST.XRPSHORT  | 0.0000                         | 0.00         | 0.01                     | yes            |

### Totals

- **accumulated fees (BTS value, approx):** 135,871.41 BTS
- **accumulated collateral fees:** 21,423.64 BTS
- **combined claimable (approx):** 157,295.05 BTS

## 3. Issuer Market-Fee-Sharing Vestings

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
Generated by `honest/fee_report.py`. Read-only; does not modify the chain.
