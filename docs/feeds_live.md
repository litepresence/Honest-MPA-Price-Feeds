# HONEST-feeds-live

Each HONEST feed producer publishes a public JSON snapshot of its current feed
once per hourly cycle. A browser-side renderer can fetch every producer's
snapshot and draw the live source grids without any server or read-side
credentials.

## Repo setup (you, once)

1. Create `squidKid-deluxe/HONEST-feeds-live` as a **public** repository with a
   README. It has to be public: `raw.githubusercontent.com` and Pages on a free
   account do not serve private repos. The README gives GitHub a `main` branch
   before you enable Pages.
2. Settings > Pages > Source: "Deploy from a branch", branch `main`, folder
   `/ (root)`. Save. GitHub shows the site URL there.
3. For each producer, generate a fine-grained token: Settings > Developer
   settings > Personal access tokens > Fine-grained tokens.
   - Repository access: Only select repositories > `HONEST-feeds-live`
   - Permissions > Repository permissions > Contents: Read and write
   - Expiration: up to one year. Note the date: an expired token stops
     snapshots without any chain-side symptom. One token per producer, so each
     can be revoked alone.

## Producer setup (each machine)

The repo is hardcoded in `honest/publish_snapshot.py` as `FEED_REPO`, since
every producer writes to the same one. Only the token is per machine. In the
same shell you start the feed from:

```bash
cd Honest-MPA-Price-Feeds/honest
export FEED_TOKEN=<this machine's token>
python HONEST.py
```

The feed uploads `<account>.json` to the repo after it finishes publishing to
the chain. A snapshot reports the prices the producer computed; it does not
confirm that the chain accepted every edict. Without `FEED_TOKEN` it prints
`feed snapshot skipped: FEED_TOKEN must be set` and publishes to the chain as
usual. Upload messages go to the console: `REDIRECT_TO_LOG` is `False`, so
stdout is not sent to `pipe/log*.txt`.

## First check

One cycle is enough to prove the wiring, and `--snapshot-only` uploads the
snapshot without touching the blockchain, so no WIF is needed. `--oneshot`
runs a single pass:

```bash
export FEED_TOKEN=<this machine's token>
python HONEST.py --oneshot --snapshot-only
```

It asks for your BitShares account name, then prints
`snapshot upload OK` or `snapshot upload FAILED`. Then fetch the file from
another machine or a browser:

```bash
curl -s https://raw.githubusercontent.com/squidKid-deluxe/HONEST-feeds-live/main/<account>.json | head -c 200
```

A body starting with `{"schema": 1` means it works. On failure the console line
above says why (`GitHub returned 401/403/404`); the usual cause is a token
scoped to a different repo or missing `Contents: Read and write`.

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
