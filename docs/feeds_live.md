# HONEST-feeds-live

Each HONEST feed producer publishes a public JSON snapshot of its current feed
once per hourly cycle. A browser-side renderer can fetch every producer's
snapshot and draw the live source grids without any server or read-side
credentials.

## Repo setup (done once by the org)

1. Create the `HONEST-feeds-live` repository on GitHub and enable Pages
   (branch `main`, root directory).
2. For each producer, create a fine-grained personal access token scoped to
   `HONEST-feeds-live` only, with `Contents: Read and write`.

## Producer setup (each machine)

Set two environment variables in the feed's environment:

```bash
export FEED_REPO=squidKid-deluxe/HONEST-feeds-live
export FEED_TOKEN=<that producer's fine-grained token>
```

The feed uploads `<account>.json` to the repo after it finishes publishing to
the chain. A snapshot reports the prices the producer computed; it does not
confirm that the chain accepted every edict. Without both variables it prints
`feed snapshot skipped: FEED_REPO and FEED_TOKEN must be set` and publishes to
the chain as usual.

## Snapshot URLs for the site

- Immediate, no build step:
  `https://raw.githubusercontent.com/squidKid-deluxe/HONEST-feeds-live/main/<account>.json`
- GitHub Pages (about a minute behind, stable domain):
  `https://squidKid-deluxe.github.io/HONEST-feeds-live/<account>.json`

Both serve `Access-Control-Allow-Origin: *`, so a browser-side renderer can
fetch them directly.

## Which accounts to fetch

No manifest. Read the current producers from the blockchain, which is
authoritative and needs no maintenance. Each HONEST asset's bitasset object
carries a `feeds` list whose entries start with a producer account id, and
`get_objects` turns those `1.2.x` ids into account names. `pricefeed_stats.py`
in this repo already does both steps: it reads `feeds` from each bitasset
object and resolves the producer ids to names.

Fetch `<account>.json` for each producer found that way, and skip accounts
whose file is missing (404), since an account can publish settlement prices
without publishing snapshots.

## Payload

```json
{
  "schema": 1,
  "account": "<BitShares account>",
  "prices": {
    "time": {"unix": 0, "local": "", "utc": "", "runtime": 0, "updates": 0},
    "cex": {},
    "dex": {},
    "forex": {},
    "inverse": {},
    "feed": {}
  }
}
```

The `prices` object is exactly what `render_price_logs.py` consumes, so a
renderer can reproduce the CEX, DEX, FOREX, final feed, and BTS:BTC source
tables for each producer.

## Failure behavior

An upload failure prints a message and is otherwise ignored: chain publishing
is unaffected. The next hourly cycle retries. The site should treat a snapshot
whose `prices.time.unix` is more than 7200 seconds old as stale.
