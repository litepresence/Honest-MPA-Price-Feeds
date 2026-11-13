# HONEST-feeds-live

Each HONEST feed producer publishes a public JSON snapshot of its current feed
once per hourly cycle. A browser-side renderer can fetch every producer's
snapshot and draw the live source grids without any server or read-side
credentials.

## Repo setup (done once by the org)

1. Create the `HONEST-feeds-live` repository on GitHub and enable Pages
   (branch `main`, root directory).
2. Add `producers.json` at the repo root listing the four BitShares account
   names, for example:

   ```json
   ["producer1", "producer2", "producer3", "producer4"]
   ```

   The org maintains this file. Producers never write it, so there are no write
   races.
3. For each producer, create a fine-grained personal access token scoped to
   `HONEST-feeds-live` only, with `Contents: Read and write`.

## Producer setup (each machine)

Set two environment variables in the feed's environment:

```bash
export FEED_REPO=litepresence/HONEST-feeds-live
export FEED_TOKEN=<that producer's fine-grained token>
```

The feed then uploads `<account>.json` to the repo after every successful
chain publish. Without both variables it logs
`feed snapshot skipped: FEED_REPO and FEED_TOKEN must be set` and publishes to
the chain as usual.

## Snapshot URLs for the site

- Immediate, no build step:
  `https://raw.githubusercontent.com/<owner>/HONEST-feeds-live/main/<account>.json`
- GitHub Pages (about a minute behind, stable domain):
  `https://<owner>.github.io/HONEST-feeds-live/<account>.json`

Both serve `Access-Control-Allow-Origin: *`, so a browser-side renderer can
fetch them directly.

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

An upload failure is logged and otherwise ignored: chain publishing is
unaffected. The next hourly cycle retries. The site should treat a snapshot
whose `prices.time.unix` is more than 7200 seconds old as stale.
