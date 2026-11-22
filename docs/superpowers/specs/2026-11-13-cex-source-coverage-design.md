# CEX source coverage and accuracy scan — design

**Date:** 2026-11-13
**Status:** awaiting approval

## Intent

HONEST needs five independent CEX sources per coin. The feed's source table
(`honest/exchanges.py`) has thin spots (BTS:USDT has 3, EOS:BTC 5, EOS:USDT 6,
XMR:BTC 6) and some configured exchanges are listed but dead. Build a tooling
script that measures, across every exchange ccxt ships, how many live prices
each needed coin has against BTC, USD, and USDT, and plots per-exchange price
deviation so we can see which sources agree with the pack.

## Goals

- One row per needed coin: live source counts for BTC, USD, USDT, and the tier
  at which the coin reaches 5.
- Distinguish "no market" from "exchange unreachable": a timeout is not a
  delisting.
- Mark which currently configured pairs are broken.
- Per-exchange deviation distribution as a matplotlib figure.
- Cache raw results so the plot can be redrawn without re-hitting exchanges.

## Non-goals

- Editing `exchanges.py`, or choosing the replacement sources.
- Fiat and metals: those come from the forex feed, not CEX.
- Scheduling, monitoring, or running this from the feed.
- Proving an exchange is correct. Deviation measures agreement with the
  cross-exchange median, not truth.

## Anti-goals

- Reporting an unreachable exchange as having zero markets.
- Counting a listed-but-dark pair as a live source.
- Pooling BTC, USD, and USDT prices into one comparison; those are different
  units and must be grouped separately.

## Constraints

- Python 3.10, ccxt 4.5.59 (105 exchanges). `ccxt.async_support`, aiohttp, and
  matplotlib 3.10.9 are present in this environment.
- Rate limits are per exchange, so exchanges run concurrently and each one is
  throttled by its own ccxt instance. One global cap keeps the machine sane.
- Some exchanges are geo-blocked or defunct; failures are expected data.

## Approaches considered

1. Markets-list only: fast, but a market listing is exactly what looks healthy
   while the feed reports failures.
2. Markets plus live probe of the configured exchanges only: cheap, answers
   "which current source is broken" but not "where do replacements come from".
3. Live ticker per coin per exchange across all of ccxt, with an accuracy plot:
   chosen. It answers both questions in one pass and the plot was requested.

## Decisions

- Coin universe is parsed from `honest/exchanges.py` (14 bases: ADA, ALGO,
  ATOM, BTC, BTS, DOT, EOS, ETH, FIL, LTC, SOL, XLM, XMR, XRP), read at runtime
  rather than hardcoded, so the scan follows the feed.
- A source is an exchange returning a non-null `last` for `COIN/QUOTE` where
  QUOTE is BTC, USD, or USDT. The three counts stay separate and are reported
  in that preference order.
- Symbols are built with `utilities.correct_pair`, the same EOS-to-A mapping the
  feed uses, so counts match what the feed can actually request.
- `binance` and `bybit` are in `exchanges.py`'s BLACKLIST: they are scanned and
  reported, but excluded from viable counts and flagged as blacklisted.
- Concurrency: one async task per exchange, global semaphore of 20, 20 s
  request timeout, 90 s deadline per exchange. A failure records the exception
  class against that exchange, never zero markets.
- Deviation is computed inside a (coin, quote) group with at least two live
  prices: each price against that group's median, as a percentage. The per-
  exchange distributions pool those deviations across groups, since percentages
  are unitless, and only exchanges with at least 3 observations are plotted.
- Outputs: markdown table on stdout, `tooling/cex_sources.json` cache,
  `tooling/cex_sources.png` figure, and `--from-json` to redraw from cache.
- `matplotlib` is added to `requirements.txt`: `render_price_logs.py` already
  imports it and the file is missing it.
- Figure: two panels. Left, stacked horizontal bars per coin with BTC, USD, and
  USDT live counts and a line at 5. Right, box plot of per-exchange deviation,
  sorted by median absolute deviation.

## Left to the builder

- Exact CLI flags, table column widths, cache JSON schema.
- Whether to label the blacklisted exchanges inside the plot or only in the
  table.
