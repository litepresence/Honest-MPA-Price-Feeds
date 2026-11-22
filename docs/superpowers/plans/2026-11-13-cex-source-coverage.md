# CEX source coverage scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A tooling script that measures, for every coin HONEST needs, how many ccxt exchanges return a live price in BTC, USD, and USDT, and plots per-exchange deviation from the cross-exchange median.

**Architecture:** One script, `tooling/cex_scan.py`, split into pure metric functions, an async fan-out over ccxt exchanges, and a rendering layer. Exchanges run concurrently, one task each, throttled by their own ccxt instance under a global semaphore. Results land in a JSON cache; the table and plot render from that cache, so plotting never needs the network again.

**Tech Stack:** Python 3.10, ccxt 4.5.59 (`ccxt.async_support`), asyncio, matplotlib 3.10.9, pytest.

**Spec:** `docs/superpowers/specs/2026-11-13-cex-source-coverage-design.md`

## Global Constraints

- Python 3.10; `black --check` must pass on changed files.
- Coin universe comes from `honest/exchanges.py` at runtime: 14 bases (ADA, ALGO, ATOM, BTC, BTS, DOT, EOS, ETH, FIL, LTC, SOL, XLM, XMR, XRP).
- Quotes are exactly `BTC`, `USD`, `USDT`, reported separately and in that preference order.
- A source is an exchange whose ticker `last` is present and greater than zero. A missing market, a `None`, and a `0` are all "not a source".
- An exchange that raises is recorded with its exception class name in `error`; it never reports zero markets.
- Symbols are requested through `utilities.correct_pair` first, with the literal `COIN/QUOTE` as fallback.
- `binance` and `bybit` are scanned, reported, and excluded from viable counts (they are `BLACKLIST` in `honest/exchanges.py`).
- Async: one task per exchange, semaphore of 20, 20 s request timeout, 90 s deadline per exchange.
- Deviation is computed inside a (coin, quote) group with at least two live prices, as `(price / median - 1) * 100`, and pooled per exchange afterward.
- Outputs: `tooling/cex_sources.json` (cache, gitignored), `tooling/cex_sources.md` and `tooling/cex_sources.png` (committed report).
- `matplotlib` is added to `requirements.txt`.
- No changes to `honest/` behavior; `tooling/` may import `honest/exchanges.py` and `honest/utilities.py`.

## Review Focus

- **Unreachable exchange:** a timeout, DNS failure, or Cloudflare block must appear as `{"ok": false, "error": "..."}` with its name in the table's unreachable list, never as a coin with zero sources. Tested in Task 2.
- **Dark market:** a listed symbol whose ticker `last` is `None` or `0` is not a source. Tested in Task 1.
- **EOS alias:** on coinex, hitbtc, kucoin, mexc, and upbit the feed requests `A` for EOS. Counting must use the same candidates or EOS is undercounted by five. Tested in Task 1.
- **Blacklisted exchanges:** present in the scan, absent from viable counts, and named as blacklisted. Tested in Task 1.
- **Partial run:** some exchanges always fail. The cache and report must still be written from the rest. Tested in Task 3.

---

### Task 1: Pure metrics — universe, counts, tiers, deviations, table

**Files:**
- Create: `tooling/cex_scan.py`
- Modify: `tests/conftest.py`
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: `honest/exchanges.py` (`EXCHANGES`, `BLACKLIST`), `honest/utilities.py` (`correct_pair`).
- Produces:
  - `coins_from_exchanges(exchanges: dict) -> list[str]`
  - `candidate_symbols(exchange: str, coin: str, quote: str) -> list[str]`
  - `prices_from_tickers(tickers: dict, chosen: dict) -> dict[str, float]`
  - `live_sources(results: dict, coins: list[str], quotes: list[str]) -> dict[str, dict[str, list[str]]]`
  - `tier_reach(sources: dict[str, list[str]], quotes: list[str] = QUOTES, target: int = 5) -> str`
  - `deviations(results: dict) -> dict[str, list[float]]`
  - `format_table(sources: dict, coins: list[str], quotes: list[str], unreachable: list[str], blacklist: list[str]) -> str`

The cache shape every function here takes:

```python
{
  "generated": "2026-11-13T00:00:00+00:00",
  "coins": ["ADA", "BTC"],
  "quotes": ["BTC", "USD", "USDT"],
  "exchanges": {
    "kraken": {"ok": True,  "error": None, "seconds": 2.1,
               "prices": {"ADA:BTC": 1.05e-05, "BTC:USD": 60000.0}},
    "dead":   {"ok": False, "error": "NetworkError", "seconds": 20.0,
               "prices": {}},
  },
}
```

- [ ] **Step 1: Put `tooling/` on the test path**

Replace `tests/conftest.py` with:

```python
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(ROOT / "honest"))
sys.path.insert(0, str(ROOT / "tooling"))
```

- [ ] **Step 2: Write the failing tests**

`tests/test_cex_scan.py`:

```python
import cex_scan

COINS = ["ADA", "EOS", "BTS"]
QUOTES = ["BTC", "USD", "USDT"]

RESULTS = {
    "kraken": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"ADA:BTC": 1.0e-05, "ADA:USD": 0.40, "BTC:USD": 60000.0},
    },
    "gate": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"ADA:BTC": 1.1e-05, "ADA:USDT": 0.41, "BTC:USDT": 61000.0},
    },
    "coinex": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"EOS:USDT": 0.70},
    },
    "dark": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"BTS:USDT": None},
    },
    "dead": {
        "ok": False,
        "error": "NetworkError",
        "seconds": 20.0,
        "prices": {},
    },
}


def test_coins_from_exchanges_dedupes_and_sorts():
    exchanges = {
        "ADA:BTC": ["kraken"],
        "ADA:USDT": ["gate"],
        "BTC:USD": ["kraken"],
        "BTS:USDT": ["gate"],
    }
    assert cex_scan.coins_from_exchanges(exchanges) == ["ADA", "BTC", "BTS"]


def test_candidate_symbols_prefers_the_feed_alias_then_the_literal():
    assert cex_scan.candidate_symbols("kucoin", "EOS", "USDT") == [
        "A/USDT",
        "EOS/USDT",
    ]
    assert cex_scan.candidate_symbols("kraken", "ADA", "BTC") == ["ADA/BTC"]


def test_prices_from_tickers_drops_none_and_zero():
    tickers = {
        "ADA/BTC": {"last": 1.0e-05},
        "ADA/USD": {"last": None},
        "ADA/USDT": {"last": 0},
    }
    chosen = {"ADA:BTC": "ADA/BTC", "ADA:USD": "ADA/USD", "ADA:USDT": "ADA/USDT"}
    assert cex_scan.prices_from_tickers(tickers, chosen) == {"ADA:BTC": 1.0e-05}


def test_live_sources_counts_quotes_separately():
    sources = cex_scan.live_sources(RESULTS, COINS, QUOTES)
    assert sources["ADA"] == {
        "BTC": ["gate", "kraken"],
        "USD": ["kraken"],
        "USDT": ["gate"],
    }
    assert sources["EOS"] == {"BTC": [], "USD": [], "USDT": ["coinex"]}
    assert sources["BTS"] == {"BTC": [], "USD": [], "USDT": []}


def test_tier_reach_walks_the_preference_order():
    assert cex_scan.tier_reach({"BTC": ["a", "b", "c", "d", "e"], "USD": [], "USDT": []}) == "BTC"
    assert cex_scan.tier_reach({"BTC": ["a"], "USD": ["b", "c", "d", "e"], "USDT": []}) == "USD"
    assert cex_scan.tier_reach({"BTC": ["a"], "USD": ["b"], "USDT": ["c", "d", "e"]}) == "USDT"
    assert cex_scan.tier_reach({"BTC": ["a"], "USD": ["b"], "USDT": ["c"]}) == "MISSING"


def test_deviations_are_percentages_against_the_group_median():
    dev = cex_scan.deviations(RESULTS)
    assert round(dev["kraken"][0], 4) == round((1.0e-05 / 1.05e-05 - 1) * 100, 4)
    assert "dead" not in dev
    assert "dark" not in dev


def test_format_table_flags_thin_coins_blacklist_and_unreachable():
    sources = cex_scan.live_sources(RESULTS, COINS, QUOTES)
    unreachable = [name for name, row in RESULTS.items() if not row["ok"]]
    text = cex_scan.format_table(
        sources, COINS, QUOTES, unreachable, blacklist=["gate"]
    )
    assert "| ADA" in text and "| EOS" in text and "| BTS" in text
    assert "MISSING" in text
    assert "dead" in text
    assert "blacklisted" in text
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -v`
Expected: collection error, `ModuleNotFoundError: No module named 'cex_scan'`.

- [ ] **Step 4: Implement the pure half of `tooling/cex_scan.py`**

Module docstring: one paragraph saying it measures live CEX source coverage for HONEST coins against BTC, USD, USDT and never modifies the feed.

Pinned values:
- `QUOTES = ["BTC", "USD", "USDT"]` and `TARGET_SOURCES = 5` at module level.
- `coins_from_exchanges` returns `sorted({pair.split(":")[0] for pair in exchanges})`, so BTC and BTS are included like any other base.
- `candidate_symbols` returns `correct_pair(exchange, f"{coin}/{quote}")` first, then `f"{coin}/{quote}"` when different, deduped in that order.
- `prices_from_tickers(tickers, chosen)` keeps only `last` values that are not `None` and `> 0`, keyed by the honest pair.
- `live_sources` iterates `results`, skips exchanges with `ok` false, and returns every coin and every quote present, sorted, including empty lists.
- `tier_reach` accumulates counts in the order of `quotes` (defaulting to `QUOTES`) and returns the first quote whose running total reaches `target`, else `"MISSING"`.
- `deviations` groups live prices by `(coin, quote)` across exchanges, keeps groups with at least two prices, computes the median, and appends `(price / median - 1) * 100` to the exchange's list. It returns only exchanges with at least one deviation.
- `format_table` emits a markdown table with columns `coin`, one column per quote, `reach`, `tier`, and a `missing` line listing coins whose reach is `MISSING`, a `blacklisted` line, and an `unreachable` line. When a line's list is empty, print the header with `none`.

- [ ] **Step 5: Run the tests to verify they pass**

Run: `python -m pytest tests/test_cex_scan.py -v`
Expected: 7 passed.

- [ ] **Step 6: Format check and commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tests/conftest.py tests/test_cex_scan.py
git commit -m "feat: compute per-coin CEX source counts, tiers, and deviations"
```

---

### Task 2: Async scan across ccxt

**Files:**
- Modify: `tooling/cex_scan.py`
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: `coins_from_exchanges`, `candidate_symbols`, `prices_from_tickers` from Task 1.
- Produces:
  - `async def scan(exchange_names: list[str], coins: list[str], quotes: list[str], concurrency: int = 20, request_timeout: int = 20, exchange_deadline: int = 90, make_exchange=None) -> dict`
  - `save_cache(path, cache: dict) -> None`
  - `load_cache(path) -> dict`

`scan` returns the cache shape from Task 1 with `generated`, `coins`, `quotes`, and `exchanges`; `make_exchange` is a callable taking a name and returning a ccxt exchange object, present so tests can inject a fake.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cex_scan.py`:

```python
import asyncio
import json

import pytest


class FakeExchange:
    def __init__(self, symbol, last):
        self.markets = {symbol: {"symbol": symbol}}
        self._symbol = symbol
        self._last = last
        self.closed = False
        self.requests = []

    async def load_markets(self):
        return self.markets

    async def fetch_tickers(self, symbols=None):
        self.requests.append(list(symbols))
        return {symbol: {"last": self._last} for symbol in symbols}

    async def close(self):
        self.closed = True


class ExplodingExchange:
    markets = {}

    async def load_markets(self):
        raise RuntimeError("boom")

    async def close(self):
        pass


def test_scan_records_errors_instead_of_zero_markets():
    def make_exchange(name):
        return ExplodingExchange()

    cache = asyncio.run(
        cex_scan.scan(["dead"], ["ADA"], ["BTC"], make_exchange=make_exchange)
    )
    assert cache["exchanges"]["dead"]["ok"] is False
    assert cache["exchanges"]["dead"]["error"] == "RuntimeError"
    assert cache["exchanges"]["dead"]["prices"] == {}


def test_scan_uses_the_alias_symbol_and_closes_the_exchange():
    made = {}

    def make_exchange(name):
        made[name] = FakeExchange("A/USDT", 0.7)
        return made[name]

    cache = asyncio.run(
        cex_scan.scan(
            ["coinex"], ["EOS"], ["USDT"], make_exchange=make_exchange
        )
    )
    assert cache["exchanges"]["coinex"]["ok"] is True
    assert cache["exchanges"]["coinex"]["prices"] == {"EOS:USDT": 0.7}
    assert made["coinex"].requests == [["A/USDT"]]
    assert made["coinex"].closed is True


def test_scan_without_a_matching_market_makes_no_request():
    exp = FakeExchange("XRP/USDT", 1.0)

    cache = asyncio.run(
        cex_scan.scan(
            ["gate"], ["ADA"], ["BTC"], make_exchange=lambda name: exp
        )
    )
    assert cache["exchanges"]["gate"]["ok"] is True
    assert cache["exchanges"]["gate"]["prices"] == {}
    assert exp.requests == []


def test_cache_round_trip(tmp_path):
    path = tmp_path / "cache.json"
    original = {"generated": "now", "coins": ["ADA"], "quotes": ["BTC"], "exchanges": {}}
    cex_scan.save_cache(path, original)
    assert cex_scan.load_cache(path) == original
    assert json.loads(path.read_text())["coins"] == ["ADA"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -v`
Expected: FAIL with `AttributeError: module 'cex_scan' has no attribute 'scan'`.

- [ ] **Step 3: Implement the scanner**

Pinned values:
- Import `ccxt.async_support as ccxt_async` inside the module; `make_exchange` defaults to `lambda name: getattr(ccxt_async, name)({"enableRateLimit": True, "timeout": 20000})`.
- One `asyncio.Semaphore(concurrency)` around each exchange coroutine; each coroutine is wrapped in `asyncio.wait_for(..., exchange_deadline)`.
- Per exchange: `await load_markets()`, choose the first `candidate_symbols(...)` present in `exchange.markets` for each coin and quote, build `chosen = {"ADA:BTC": "ADA/BTC", ...}`, and return early without a request when `chosen` is empty.
- Request with `await exchange.fetch_tickers(list(chosen.values()))`, wrapped in `asyncio.wait_for(..., request_timeout)`; on `ccxt_async.NotSupported` or a multi-symbol error, fall back to one `fetch_ticker` per symbol.
- `prices` is `prices_from_tickers(tickers, chosen)`.
- Success records `{"ok": True, "error": None, "seconds": <float>, "prices": ...}`; any exception records `{"ok": False, "error": type(error).__name__, "seconds": <float>, "prices": {}}`.
- `close()` runs in a `finally` for every exchange, including failures.
- `save_cache` writes indented JSON; `load_cache` reads it back.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_cex_scan.py -v`
Expected: 11 passed.

- [ ] **Step 5: Smoke-test the scanner against two live exchanges**

Run:

```bash
cd /workspace && python -c "
import asyncio, cex_scan
c = asyncio.run(cex_scan.scan(['kraken', 'gate'], ['ADA', 'BTC'], ['BTC', 'USD', 'USDT']))
for name, row in c['exchanges'].items():
    print(name, row['ok'], row['error'], len(row['prices']), row['seconds'])
"
```

Expected: both `ok` true, `error` None, and non-zero price counts. A failure here is a real network or symbol problem, not a test problem.

- [ ] **Step 6: Format check and commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tests/test_cex_scan.py
git commit -m "feat: scan ccxt exchanges concurrently and cache the results"
```

---

### Task 3: Plot, CLI, cache files, and the real run

**Files:**
- Modify: `tooling/cex_scan.py`
- Modify: `requirements.txt`
- Create: `tooling/.gitignore`
- Create (generated, committed): `tooling/cex_sources.md`, `tooling/cex_sources.png`
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: everything from Tasks 1 and 2.
- Produces:
  - `make_plot(results: dict, sources: dict, coins: list[str], quotes: list[str], path) -> None`
  - `main(argv=None) -> int`

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cex_scan.py`:

```python
def test_make_plot_writes_a_nonempty_png(tmp_path):
    outc = tmp_path / "plot.png"
    sources = cex_scan.live_sources(RESULTS, COINS, QUOTES)
    cex_scan.make_plot(RESULTS, sources, COINS, QUOTES, outc)
    assert outc.exists() and outc.stat().st_size > 1000


def test_main_from_json_renders_every_output(tmp_path):
    cache = tmp_path / "cache.json"
    cex_scan.save_cache(cache, {
        "generated": "now",
        "coins": COINS,
        "quotes": QUOTES,
        "exchanges": RESULTS,
    })
    out_json = tmp_path / "out.json"
    out_png = tmp_path / "out.png"
    out_md = tmp_path / "out.md"

    code = cex_scan.main(
        [
            "--from-json", str(cache),
            "--json", str(out_json),
            "--png", str(out_png),
            "--md", str(out_md),
        ]
    )

    assert code == 0
    assert out_json.exists() and out_png.exists() and out_md.exists()
    text = out_md.read_text()
    assert "| ADA" in text and "MISSING" in text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -v`
Expected: FAIL with `AttributeError: module 'cex_scan' has no attribute 'make_plot'`.

- [ ] **Step 3: Implement the plot and CLI**

Pinned values:
- `matplotlib.use("Agg")` before `pyplot` import, so the script never needs a display.
- Figure: 2 panels side by side, `figsize=(16, 0.3 * len(coins) + 4)`.
- Left panel: horizontal stacked bars per coin, `BTC` bottom, then `USD`, then `USDT`, counts from `sources`; a vertical dashed line at `TARGET_SOURCES` labeled `5 sources`.
- Right panel: horizontal box plot, one row per exchange with at least 3 deviations, sorted by median absolute deviation so the most consistent is at one end; x axis `% deviation from the (coin, quote) median`; title names the number of exchanges plotted and the threshold.
- Skip the right panel with a note in the title when fewer than two exchanges qualify.
- CLI flags: `--exchanges A,B`, `--quotes BTC,USD,USDT`, `--from-json PATH`, `--json PATH` (default `tooling/cex_sources.json`), `--png PATH` (default `tooling/cex_sources.png`), `--md PATH` (default `tooling/cex_sources.md`), `--top N` (default 0 = all exchanges).
- Default flow: scan every `ccxt.exchanges` name when `--exchanges` is absent; write the cache; render table to stdout and the markdown file; render the plot; return 0.
- `--from-json`: load the cache, skip the network, render the same three outputs.
- Read `BLACKLIST` from `honest/exchanges.py` for the table and exclude those names from viable counts.
- `requirements.txt`: add `matplotlib` after `numpy`.
- `tooling/.gitignore`: `cex_sources.json`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: 22 passed (the 9 existing tests, the 11 scan tests, and the 2 added here).

- [ ] **Step 5: Run the real scan**

Run:

```bash
cd /workspace && time python tooling/cex_scan.py
```

Expected: a table with all 14 coins, a `missing` line, the unreachable list, and both files written. Save the console output; quote the table in the final report to the human.

- [ ] **Step 6: Inspect the outputs before committing**

Read `tooling/cex_sources.md` and view `tooling/cex_sources.png`. Check that: every coin has a row; the blacklisted names appear only in the blacklist line; unreachable exchanges are named rather than counted; the box plot labels readable and sorted. Fix the rendering if any of those fail, then re-run `--from-json`.

- [ ] **Step 7: Format check and commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tooling/.gitignore tooling/cex_sources.md tooling/cex_sources.png requirements.txt tests/test_cex_scan.py
git commit -m "feat: render CEX coverage table and deviation plot, add the scan CLI"
```

---

## Self-Review

- **Spec coverage:** coin universe from `exchanges.py` (Task 1), three separate quote counts and tier order (Task 1), unreachable-is-not-zero (Task 2), alias-aware symbols (Tasks 1-2), blacklist handling (Tasks 1 and 3), async fan-out with the pinned limits (Task 2), deviation inside (coin, quote) groups (Task 1), two-panel figure (Task 3), JSON cache plus `--from-json` (Tasks 2-3), `matplotlib` in `requirements.txt` (Task 3).
- **Step scan:** each step carries one action; test steps contain the assertions, code steps carry signatures and pinned values, and no step transcribes a body whose shape the tests already fix.
- **Type consistency:** `scan` returns exactly the cache shape that Task 1's functions consume; `live_sources`, `tier_reach`, `deviations`, and `format_table` are called with the same argument order everywhere; `make_plot` consumes `results` and `sources` in the same order as `main` builds them.
- **Review Focus:** unreachable exchange (Task 2 test), dark market (Task 1 test), EOS alias (Task 1 test and Task 2 request assertion), blacklist (Task 1 test), partial run (Task 3 test writes outputs from a cache containing a failed exchange).
- **Proportion:** three tasks, one script plus one test file. Most of the plan's length is test code the executor needs verbatim, not transcribed implementation.
