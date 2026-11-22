# CEX volume report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture 24 h volume per market in the CEX scan, render per-coin exchange lists sorted by volume in fixed-width markdown, and add a box-and-whisker figure of each exchange's share of every coin's volume.

**Architecture:** Volume rides along in the ticker response the scan already fetches, in base-coin units, and lands in the cache next to `prices`. Pure functions turn that into per-coin exchange volumes and shares; the markdown and a second figure render from the cache, so neither needs the network.

**Tech Stack:** Python 3.10, ccxt 4.5.59, asyncio, matplotlib 3.10, pytest.

**Spec:** `docs/superpowers/specs/2026-11-13-cex-volume-report-design.md`

## Global Constraints

- Python 3.10; `black --check` must pass on changed files.
- Volume is stored in base-coin units: `baseVolume` when positive, else `quoteVolume / last`, else the pair is skipped.
- A cache written before this change (no `volumes` key) must still render: missing volume is empty, never zero.
- Shares are computed per coin over exchanges with a positive volume; no coin with a zero total is divided by.
- Blacklisted exchanges (`binance`, `bybit`) are excluded from the markdown listings, matching the coverage counts; the volume figure includes all exchanges, matching the accuracy figure.
- Every table in `tooling/cex_sources.md` is a fenced, padded, fixed-width block.
- No changes to `honest/` behavior.

## Review Focus

- **quoteVolume-only exchange:** an exchange that reports `quoteVolume` but no `baseVolume` must still contribute volume, derived as `quoteVolume / last`, or its coin share silently reads zero. Tested in Task 1.
- **String volume:** ccxt sometimes hands back `baseVolume` or `last` as a string; a bare comparison or division must not lose the whole exchange. Tested in Task 1.
- **Old cache:** a cache with no `volumes` key must render the markdown and figure without an exception. Tested in Task 2 (markdown) and Task 3 (CLI from a cache fixture).
- **Zero-total coin:** a coin whose exchanges all report zero volume must not divide by zero and must say "no reported 24 h volume". Tested in Task 2.
- **Multi-quote coin:** a coin live under BTC and USD on one exchange is summed once per exchange, not counted as two entries. Tested in Task 2.

---

### Task 1: Capture volume in the scan

**Files:**
- Modify: `tooling/cex_scan.py` (`volumes_from_tickers`, `_scan_one`, success/failure record)
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: `prices_from_tickers` shape, `chosen` mapping (`{"ADA:BTC": "ADA/BTC"}`).
- Produces:
  - `volumes_from_tickers(tickers: dict, chosen: dict) -> dict[str, float]` keyed by honest pair, base-coin units.
  - Every cache exchange row gains `"volumes": dict[str, float]`, `{}` on failure.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_cex_scan.py`:

```python
def test_volumes_from_tickers_uses_base_volume():
    tickers = {
        "ADA/BTC": {"last": 1.0e-05, "baseVolume": 10.0, "quoteVolume": 0.0001},
        "ADA/USD": {"last": 0.40, "baseVolume": 0, "quoteVolume": 500.0},
        "ADA/USDT": {"last": 0, "baseVolume": 0, "quoteVolume": 100.0},
    }
    chosen = {"ADA:BTC": "ADA/BTC", "ADA:USD": "ADA/USD", "ADA:USDT": "ADA/USDT"}
    assert cex_scan.volumes_from_tickers(tickers, chosen) == {
        "ADA:BTC": 10.0,
        "ADA:USD": 1250.0,
    }


def test_volumes_from_tickers_coerces_strings():
    tickers = {
        "ADA/BTC": {"last": "5", "baseVolume": "10.5"},
        "ADA/USD": {"last": "2", "baseVolume": None, "quoteVolume": "50"},
        "ADA/USDT": {"last": None, "baseVolume": None, "quoteVolume": "9"},
    }
    chosen = {"ADA:BTC": "ADA/BTC", "ADA:USD": "ADA/USD", "ADA:USDT": "ADA/USDT"}
    assert cex_scan.volumes_from_tickers(tickers, chosen) == {
        "ADA:BTC": 10.5,
        "ADA:USD": 25.0,
    }


def test_scan_records_volumes():
    made = {}

    def make_exchange(name):
        made[name] = FakeExchange("A/USDT", 0.7, volume=42.0)
        return made[name]

    cache = asyncio.run(
        cex_scan.scan(["coinex"], ["EOS"], ["USDT"], make_exchange=make_exchange)
    )
    assert cache["exchanges"]["coinex"]["volumes"] == {"EOS:USDT": 42.0}
```

Extend the existing `FakeExchange` so it can report volume:

```python
class FakeExchange:
    def __init__(self, symbol, last, volume=None):
        self.markets = {symbol: {"symbol": symbol}}
        self._symbol = symbol
        self._last = last
        self._volume = volume
        self.closed = False
        self.requests = []

    async def load_markets(self):
        return self.markets

    async def fetch_tickers(self, symbols=None):
        self.requests.append(list(symbols))
        return {
            symbol: {"last": self._last, "baseVolume": self._volume}
            for symbol in symbols
        }

    async def close(self):
        self.closed = True
```

Add to `test_scan_records_errors_instead_of_zero_markets`:

```python
    assert cache["exchanges"]["dead"]["volumes"] == {}
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -q`
Expected: FAIL with `AttributeError: module 'cex_scan' has no attribute 'volumes_from_tickers'`, plus a `KeyError: 'volumes'`.

- [ ] **Step 3: Implement `volumes_from_tickers` and wire it into `_scan_one`**

Values:
- `float()` every candidate inside a `try/except (TypeError, ValueError): continue`, so a string or `None` is coerced or skipped, never raised.
- A value is kept when positive: `baseVolume` first, else `quoteVolume / last` when both are positive.
- `_scan_one`'s success record adds `"volumes": volumes_from_tickers(tickers, chosen)`; its empty-market shortcut and its failure record add `"volumes": {}`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_cex_scan.py -q`
Expected: 26 passed (23 existing plus 3 new).

- [ ] **Step 5: Commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tests/test_cex_scan.py
git commit -m "feat: capture 24h base volume per market in the CEX scan"
```

---

### Task 2: Per-coin volumes, shares, and fixed-width markdown

**Files:**
- Modify: `tooling/cex_scan.py` (`coin_volumes`, `shares_by_coin`, `_fixed_table`, `format_table`, `format_volume_sections`)
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: cache exchange rows with `volumes`.
- Produces:
  - `coin_volumes(results: dict) -> dict[str, dict[str, float]]` — coin -> exchange -> summed base volume, positive only.
  - `shares_by_coin(volumes: dict) -> dict[str, dict[str, float]]` — coin -> exchange -> percent of the coin's total.
  - `format_table(sources, coins, quotes, unreachable, blacklist) -> str` — now a fenced fixed-width block.
  - `format_volume_sections(volumes, shares, coins, blacklist) -> str` — one `### COIN` section per coin.

Fixture to add at module level:

```python
VOLUME_RESULTS = {
    "kraken": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"ADA:BTC": 1.0e-05, "ADA:USD": 0.40},
        "volumes": {"ADA:BTC": 10.0, "ADA:USD": 30.0},
    },
    "gate": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"ADA:USDT": 0.41},
        "volumes": {"ADA:USDT": 60.0},
    },
    "flat": {
        "ok": True,
        "error": None,
        "seconds": 1.0,
        "prices": {"BTS:USDT": 0.001},
        "volumes": {"BTS:USDT": 0.0},
    },
}
```

- [ ] **Step 1: Write the failing tests**

```python
def test_coin_volumes_sums_quotes_per_exchange():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    assert volumes["ADA"] == {"gate": 60.0, "kraken": 40.0}
    assert "BTS" not in volumes


def test_volume_shares_are_percentages_of_the_coin_total():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    shares = cex_scan.shares_by_coin(volumes)
    assert shares["ADA"] == {"gate": 60.0, "kraken": 40.0}


def test_format_table_is_fixed_width():
    sources = cex_scan.live_sources(RESULTS, COINS, QUOTES)
    text = cex_scan.format_table(sources, COINS, QUOTES, ["dead"], blacklist=["gate"])
    assert text.startswith("```")
    block = text.split("```")[1].strip("\n")
    lines = block.splitlines()
    assert len({len(line) for line in lines}) == 1
    assert any(line.startswith("ADA") for line in lines)
    assert "MISSING" in block


def test_format_volume_sections_lists_exchanges_by_volume():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    shares = cex_scan.shares_by_coin(volumes)
    text = cex_scan.format_volume_sections(volumes, shares, COINS, blacklist=[])
    ada = text.split("### ADA", 1)[1]
    assert ada.index("gate") < ada.index("kraken")
    assert "60.0%" in ada and "40.0%" in ada


def test_format_volume_sections_handles_missing_volume():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    shares = cex_scan.shares_by_coin(volumes)
    text = cex_scan.format_volume_sections(volumes, shares, COINS, blacklist=[])
    bts = text.split("### BTS", 1)[1]
    assert "no reported 24 h volume" in bts
    assert cex_scan.coin_volumes(RESULTS) == {}  # cache written before volumes existed
```

Also update the existing `test_format_table_flags_thin_coins_blacklist_and_unreachable`: replace `assert "| ADA" in text and "| EOS" in text and "| BTS" in text` with `assert "ADA" in text and "EOS" in text and "BTS" in text`, since the table is no longer pipe-delimited.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -q`
Expected: FAIL with `AttributeError` on `coin_volumes`, and the fixed-width assertion fails.

- [ ] **Step 3: Implement the four functions**

Values:
- `coin_volumes` skips rows with `ok` false, skips non-positive values, splits the pair on `:`, and sums.
- `shares_by_coin` skips a coin whose total is zero, otherwise `volume / total * 100`.
- `_fixed_table(header: list[str], rows: list[list[str]]) -> str` computes each column's width as the longest cell, joins cells with two spaces, ljusts every cell, wraps the result in triple backticks.
- `format_table` builds its header/rows as strings and returns `_fixed_table` output plus the existing `blacklisted:`, `unreachable:`, `missing:` lines after a blank line.
- `format_volume_sections` emits, per coin, `### COIN`, a blank line, then `_fixed_table(["exchange", "volume", "share"], rows)` with rows sorted by volume descending then name, blacklisted names removed, volume `f"{v:,.2f}"`, share `f"{s:.1f}%"`. A coin with no rows prints `no reported 24 h volume` instead of a table.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: 31 passed.

- [ ] **Step 5: Commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tests/test_cex_scan.py tooling/cex_sources.md
git commit -m "feat: render per-coin exchange volume and fixed-width markdown tables"
```

---

### Task 3: Volume figure, CLI flag, and the real scan

**Files:**
- Modify: `tooling/cex_scan.py` (`make_volume_plot`, `main`)
- Create (generated, committed): `tooling/cex_volume.png`
- Regenerate (committed): `tooling/cex_sources.md`, `tooling/cex_sources.png`
- Test: `tests/test_cex_scan.py`

**Interfaces:**
- Consumes: `coin_volumes`, `shares_by_coin`, `make_plot`.
- Produces:
  - `make_volume_plot(results: dict, coins: list[str], path) -> None`
  - `main` gains `--volume-png`, default `tooling/cex_volume.png`.

- [ ] **Step 1: Write the failing tests**

```python
def test_make_volume_plot_writes_a_nonempty_png(tmp_path):
    out = tmp_path / "volume.png"
    cex_scan.make_volume_plot(VOLUME_RESULTS, COINS, out)
    assert out.exists() and out.stat().st_size > 1000
```

Extend `test_main_from_json_renders_every_output` with `out_vol = tmp_path / "vol.png"`, a `"--volume-png", str(out_vol)` pair, and `assert out_vol.exists()`.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_cex_scan.py -q`
Expected: FAIL with `AttributeError: module 'cex_scan' has no attribute 'make_volume_plot'`, and `main` rejects `--volume-png`.

- [ ] **Step 3: Implement the figure and the flag**

Values:
- `make_volume_plot` pools `shares_by_coin(coin_volumes(results))` into exchange -> list of shares, keeps exchanges with at least three coin shares, sorts by median share ascending so the largest sits at the top, draws `boxplot(..., orientation="horizontal", tick_labels=names, showfliers=True)`, x label `% of the coin's 24 h volume`, x limits from the 1st and 99th percentile with a 10% pad, and a title naming the count and the number of points outside the axis. With fewer than two qualifying exchanges, turn the axis off and say so in the title, exactly like the accuracy figure.
- `main` writes `make_volume_plot(cache["exchanges"], coins, args.volume_png)` on both the scan and the `--from-json` paths.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest -q`
Expected: 32 passed.

- [ ] **Step 5: Run the real scan and inspect every output**

Run: `time python tooling/cex_scan.py`
Then read `tooling/cex_sources.md` and view `tooling/cex_sources.png` and `tooling/cex_volume.png`.
Expected: the md has a volume section per coin sorted descending, with volumes present; the volume figure has one box per exchange with 3+ coin shares, largest at the top; the accuracy figure is unchanged in shape.

- [ ] **Step 6: Commit**

```bash
black --check tooling/cex_scan.py tests/
git add tooling/cex_scan.py tooling/cex_sources.md tooling/cex_sources.png tooling/cex_volume.png tests/test_cex_scan.py
git commit -m "feat: add the volume share figure and its CLI flag, regenerate the report"
```

---

## Self-Review

- **Spec coverage:** volume capture with the quote fallback (Task 1), string coercion (Task 1), per-coin sums and shares (Task 2), fixed-width fenced tables (Task 2), sorted per-coin listings (Task 2), second box figure with higher=better shares (Task 3), CLI and `--from-json` (Task 3), old-cache back-compat (Task 2 missing-volume test, Task 3 CLI test).
- **Step scan:** each step is one action; test steps carry the assertions; code steps carry signatures and pinned values.
- **Type consistency:** `volumes` is keyed by honest pair everywhere; `coin_volumes` and `shares_by_coin` take and return the nested coin -> exchange dict; `make_volume_plot` consumes `results` and `coins` like `make_plot`.
- **Review Focus:** five lines, each with its owning test in Task 1 or Task 2.
- **Proportion:** three tasks, one module and one test file; the plan is mostly test code the executor needs verbatim.
