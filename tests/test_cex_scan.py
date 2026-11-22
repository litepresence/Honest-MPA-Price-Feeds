import asyncio
import json

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
    assert (
        cex_scan.tier_reach({"BTC": ["a", "b", "c", "d", "e"], "USD": [], "USDT": []})
        == "BTC"
    )
    assert (
        cex_scan.tier_reach({"BTC": ["a"], "USD": ["b", "c", "d", "e"], "USDT": []})
        == "USD"
    )
    assert (
        cex_scan.tier_reach({"BTC": ["a"], "USD": ["b"], "USDT": ["c", "d", "e"]})
        == "USDT"
    )
    assert cex_scan.tier_reach({"BTC": ["a"], "USD": ["b"], "USDT": ["c"]}) == "MISSING"


def test_deviations_are_percentages_against_the_group_median():
    dev = cex_scan.deviations(RESULTS)
    assert round(dev["kraken"][0], 4) == round((1.0e-05 / 1.05e-05 - 1) * 100, 4)
    assert "dead" not in dev
    assert "dark" not in dev


def test_format_table_flags_thin_coins_blacklist_and_unreachable():
    unreachable = [name for name, row in RESULTS.items() if not row["ok"]]
    text = cex_scan.format_table(
        RESULTS, COINS, QUOTES, unreachable, blacklist=["gate"]
    )
    assert "ADA" in text and "EOS" in text
    assert "missing:" in text
    assert "dead" in text
    assert "blacklisted" in text


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


class ExplodingExchange:
    markets = {}

    async def load_markets(self):
        raise RuntimeError("boom")

    async def close(self):
        pass


def test_scan_records_errors_instead_of_zero_markets():
    cache = asyncio.run(
        cex_scan.scan(
            ["dead"], ["ADA"], ["BTC"], make_exchange=lambda name: ExplodingExchange()
        )
    )
    assert cache["exchanges"]["dead"]["ok"] is False
    assert cache["exchanges"]["dead"]["error"] == "RuntimeError"
    assert cache["exchanges"]["dead"]["prices"] == {}
    assert cache["exchanges"]["dead"]["volumes"] == {}


def test_scan_uses_the_alias_symbol_and_closes_the_exchange():
    made = {}

    def make_exchange(name):
        made[name] = FakeExchange("A/USDT", 0.7)
        return made[name]

    cache = asyncio.run(
        cex_scan.scan(["coinex"], ["EOS"], ["USDT"], make_exchange=make_exchange)
    )
    assert cache["exchanges"]["coinex"]["ok"] is True
    assert cache["exchanges"]["coinex"]["prices"] == {"EOS:USDT": 0.7}
    assert made["coinex"].requests == [["A/USDT"]]
    assert made["coinex"].closed is True


def test_scan_without_a_matching_market_makes_no_request():
    exp = FakeExchange("XRP/USDT", 1.0)

    cache = asyncio.run(
        cex_scan.scan(["gate"], ["ADA"], ["BTC"], make_exchange=lambda name: exp)
    )
    assert cache["exchanges"]["gate"]["ok"] is True
    assert cache["exchanges"]["gate"]["prices"] == {}
    assert exp.requests == []


def test_cache_round_trip(tmp_path):
    path = tmp_path / "cache.json"
    original = {
        "generated": "now",
        "coins": ["ADA"],
        "quotes": ["BTC"],
        "exchanges": {},
    }
    cex_scan.save_cache(path, original)
    assert cex_scan.load_cache(path) == original
    assert json.loads(path.read_text())["coins"] == ["ADA"]


def test_make_plot_writes_a_nonempty_png(tmp_path):
    outc = tmp_path / "plot.png"
    sources = cex_scan.live_sources(RESULTS, COINS, QUOTES)
    cex_scan.make_plot(RESULTS, sources, COINS, QUOTES, outc)
    assert outc.exists() and outc.stat().st_size > 1000


def test_main_from_json_renders_every_output(tmp_path):
    cache = tmp_path / "cache.json"
    cex_scan.save_cache(
        cache,
        {
            "generated": "now",
            "coins": COINS,
            "quotes": QUOTES,
            "exchanges": RESULTS,
        },
    )
    out_json = tmp_path / "out.json"
    out_png = tmp_path / "out.png"
    out_vol = tmp_path / "vol.png"
    out_md = tmp_path / "out.md"

    code = cex_scan.main(
        [
            "--from-json",
            str(cache),
            "--json",
            str(out_json),
            "--png",
            str(out_png),
            "--volume-png",
            str(out_vol),
            "--md",
            str(out_md),
        ]
    )

    assert code == 0
    assert out_json.exists() and out_png.exists() and out_md.exists()
    assert out_vol.exists()
    text = out_md.read_text()
    assert "ADA" in text and "missing:" in text


def test_from_json_does_not_overwrite_the_default_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cex_scan, "HERE", tmp_path)
    old = tmp_path / "old.json"
    cex_scan.save_cache(
        old,
        {"generated": "now", "coins": COINS, "quotes": QUOTES, "exchanges": RESULTS},
    )
    before = old.read_bytes()

    code = cex_scan.main(
        [
            "--from-json",
            str(old),
            "--png",
            str(tmp_path / "out.png"),
            "--md",
            str(tmp_path / "out.md"),
        ]
    )

    assert code == 0
    assert old.read_bytes() == before
    assert not (tmp_path / "cex_sources.json").exists()


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


def test_coin_volumes_sums_quotes_per_exchange():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    assert volumes["ADA"] == {"gate": 60.0, "kraken": 40.0}
    assert "BTS" not in volumes


def test_volume_shares_are_percentages_of_the_coin_total():
    volumes = cex_scan.coin_volumes(VOLUME_RESULTS)
    shares = cex_scan.shares_by_coin(volumes)
    assert shares["ADA"] == {"gate": 60.0, "kraken": 40.0}


def test_format_table_is_fixed_width():
    text = cex_scan.format_table(RESULTS, COINS, QUOTES, ["dead"], blacklist=["gate"])
    # Each fenced block must have uniform line lengths
    blocks = text.split("```")[1::2]
    assert len(blocks) >= 1
    for block in blocks:
        lines = [l for l in block.strip().splitlines() if l.strip()]
        lengths = {len(l) for l in lines}
        assert len(lengths) == 1, f"non-uniform lengths: {sorted(lengths)}"
    # Header of first table starts with "exchange"
    first = blocks[0].strip().splitlines()[0]
    assert first.startswith("exchange")
    assert "missing:" in text


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


def test_make_volume_plot_writes_a_nonempty_png(tmp_path):
    out = tmp_path / "volume.png"
    cex_scan.make_volume_plot(VOLUME_RESULTS, COINS, out)
    assert out.exists() and out.stat().st_size > 1000
