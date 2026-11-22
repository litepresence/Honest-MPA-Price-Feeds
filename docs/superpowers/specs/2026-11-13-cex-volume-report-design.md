# CEX volume report Design

Date: 2026-11-13
Status: draft

## Intent

The coverage scan answers "how many sources". It does not answer "which sources carry the trade", so a coin can look well covered while nearly all of its volume sits on one exchange, or on exchanges the feed would never pick. Add 24 h volume to the scan, to the markdown report, and to a second figure.

## Goals

- For each coin, list every exchange with a live price, sorted by that coin's 24 h volume on that exchange.
- A second figure, `tooling/cex_volume.png`, with the same box-and-whisker layout as the accuracy figure; the x axis is the exchange's share of each coin's volume, so higher is better.
- Every table in `tooling/cex_sources.md` readable at a fixed width: padded cells inside a fenced block.

## Non-goals

- No change to `honest/` or to feed behavior.
- No dollar conversion of volume. Shares are unit-free.
- No volume axis added to the coverage bars.

## Constraints and findings

- ccxt returns `baseVolume` (coin units) and `quoteVolume` (quote units) in the ticker the scan already fetches, so volume costs no extra requests.
- `baseVolume` is comparable across a coin's BTC/USD/USDT markets; quote volume is not, because a BTC-denominated figure is roughly 60,000 times a USD figure for the same trade. Verified on kraken: BTC/USD returned `baseVolume` 6073 BTC against `quoteVolume` 422.9M USD.
- The existing cache has no volume, so the report needs one fresh scan (about 30 s).
- Caches written before this change stay loadable. Missing volume renders as an empty cell, never as zero.

## Approaches

1. **Share of the coin's volume (picked).** Inside each coin, divide an exchange's volume by the total over the exchanges that list it, pooled per exchange. Unit-free, comparable across coins, reads as "this exchange carries this much of the coins it lists".
2. **Log10 dollar volume.** Rejected: a single BTC market dwarfs BTS by six orders, so boxes run long and the axis needs a currency conversion the scan does not otherwise do.
3. **Log ratio against the coin's median exchange.** Rejected: symmetric, but "higher is better" stops being obvious.

Separate figure rather than a third panel: the coverage figure already carries two panels, and squeezing in a third costs legibility on both.

## Design

**Cache.** Every exchange row gains `"volumes": {"ADA:BTC": 123.4}`, keyed by the same honest pair as `prices`, in base-coin units. A value comes from `baseVolume`; when that is missing or zero, from `quoteVolume / last`; otherwise the pair is skipped.

**Per coin and exchange.** Volume is summed across the quote markets where that exchange is live. Shares are computed per coin over exchanges with a positive volume, as a percentage of that coin's total.

**Markdown.** The summary table keeps its columns and gains padding. After it, one section per coin (`### ADA`) holds a fenced, fixed-width table sorted by volume descending:

```
exchange        volume        share
gate            1234567.89    41.2%
kraken          987654.32     33.0%
```

A coin with no reported volume prints "no reported 24 h volume" instead of an empty table.

**Plot.** `make_volume_plot(results, coins, path)` draws one horizontal box per exchange with at least three coin shares, sorted by median share ascending so the largest sits at the top. X axis: `% of the coin's 24 h volume`. Title names the exchange count and the threshold, matching the accuracy figure.

**CLI.** `--volume-png` defaults to `tooling/cex_volume.png`; `--from-json` renders it from the cache like the others.

**Tests.** Base and fallback volume extraction; zero and missing values; per-coin sums and shares; markdown sections sorted, padded, fenced; volume figure written non-empty; CLI writes all four outputs; a cache without `volumes` renders empty cells.

## Open

None.
