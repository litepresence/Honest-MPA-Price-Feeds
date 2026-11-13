# Live Feed Publishing — Design

**Date:** 2026-11-13
**Status:** approved

## Intent

Each producer's HONEST feed publishes a public JSON snapshot of its current
feed every hourly cycle to the dedicated `HONEST-feeds-live` GitHub repo, one
`<account>.json` per producer, so a browser-side renderer can fetch all four
and draw the live source grids. The render script stays local; the website
does the drawing.

## Goals

- Overwrite `<account>.json` once per publish cycle.
- Public read with permissive CORS, no read-side credentials.
- Payload contains the exact `prices` dict the grid renderer consumes
  (`time`, `cex`, `dex`, `forex`, `inverse`, `feed`).
- Upload failures never block, delay, or interrupt the chain publish.
- No git checkout needed on producer machines (GitHub Contents API).

## Non-goals

- No archive beyond the feeds repo's own commit history.
- No server or dashboard; rendering belongs to the website.
- No changes to `render_price_logs.py`.
- Producers do not coordinate with each other.

## Anti-goals

- A stale or partial snapshot without a visible timestamp is worse than none.
- Upload errors must not touch the feed loop's control flow.
- The WIF must never leave the producer machine.
- No shared write credentials beyond scoped per-producer tokens.

## Constraints

- Producers run independently, one machine each, Python 3.10.
- The repo, Pages, and four fine-grained tokens are created manually by the
  org before rollout.
- GitHub Pages and raw.githubusercontent.com serve
  `Access-Control-Allow-Origin: *` (verified 2026-11-13), so no CORS proxy is
  needed.

## Approaches considered

1. GitHub Pages on the main code repo — rejected: commit noise in the code
   repository.
2. Cloudflare R2 public bucket — rejected: extra account and credential
   distribution for marginal benefit over GitHub.
3. Per-producer self-hosting plus a registry — rejected: four independent
   points of failure and assumes each producer has hosting.

Chosen: a dedicated `HONEST-feeds-live` repo, one file per producer, committed
through the GitHub Contents API from the feed's publish branch.

## Decisions

- Payload: `{"schema": 1, "account": <account>, "prices": <prices dict>}`.
- Env vars `FEED_REPO` (`owner/repo`) and `FEED_TOKEN` (fine-grained PAT with
  contents read/write on that repo only).
- Single upload attempt per cycle with a 10 s timeout; the next cycle retries.
- Upload runs after `publish_feed` succeeds, inside its own try/except.
- `producers.json` in the feeds repo lists the four accounts; the org
  maintains it and producers never write it. (Superseded: the site discovers
  producers from the on-chain `feeds` list, so no manifest file is needed.)
- The website treats a snapshot older than two hours as stale (its own rule).

## Left to the builder

- Exact log wording, and whether to warn every cycle or once per process.
