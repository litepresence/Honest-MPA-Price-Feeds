# Live Feed Publishing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Each producer's hourly feed cycle publishes its current feed snapshot as public JSON to the `HONEST-feeds-live` repo.

**Architecture:** A new `publish_snapshot` module wraps the existing `prices` dict in a small envelope and PUTs it to the GitHub Contents API as `<account>.json`. `HONEST.py` calls it after a successful chain publish, inside its own try/except so an upload can never affect the feed loop.

**Tech Stack:** Python 3.10, `requests` (already a dependency), pytest (tests only), GitHub Contents API.

**Spec:** `docs/superpowers/specs/2026-11-13-feeds-live-publishing-design.md`

## Global Constraints

- Python 3.10; `black --check` must pass on changed files.
- No new runtime dependencies: `requests` is already in `requirements.txt`.
- Payload is exactly `{"schema": 1, "account": <account>, "prices": <prices dict>}`; `prices` passes through untouched.
- Env vars: `FEED_REPO` (`owner/repo`) and `FEED_TOKEN` (fine-grained PAT).
- One upload attempt per cycle, `timeout=10`; functions return `bool` and never raise.
- Upload runs only when `--publish` is active, and only after `publish_feed` returns.
- The WIF must never appear in the payload, logs, or commit messages.
- Commit message for each snapshot: `feed: <account> <UTC ISO-8601>`.

## Review Focus

- **Env vars unset** on a producer machine: chain publishing continues, one warning is printed, no traceback.
- **First upload** (file absent): GET returns 404 and the PUT must omit `sha`; later uploads must include the current `sha` or GitHub rejects the write.
- **HTTP/network failure** (401, 403, 409, 429, 5xx, timeout, DNS): returns `False`, nothing reaches the feed loop, and the next hour retries.
- **Snapshot fidelity**: the payload must carry the exact `prices` object so the website can redraw the grid, and `account` must match the chain-publishing name.
- **Secret hygiene**: the token appears only in the `Authorization` header; no error message dumps headers, and no WIF is ever included.

---

### Task 1: `publish_snapshot` module

**Files:**
- Create: `honest/publish_snapshot.py`
- Create: `tests/conftest.py`
- Create: `tests/test_publish_snapshot.py`

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces:
  - `snapshot_payload(prices: dict, account: str) -> dict`
  - `upload_snapshot(payload: dict, repo: str, token: str, timeout: int = 10) -> bool`
  - `publish_snapshot(prices: dict, account: str) -> bool`

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py`:

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "honest"))
```

`tests/test_publish_snapshot.py`:

```python
import base64
import json

import pytest
import requests

import publish_snapshot


class FakeResponse:
    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body


def test_snapshot_payload_has_schema_account_and_prices():
    prices = {"time": {"unix": 1}, "feed": {"BTS:USD": 0.1}}
    assert publish_snapshot.snapshot_payload(prices, "alice") == {
        "schema": 1,
        "account": "alice",
        "prices": prices,
    }


def make_payload(account="alice"):
    return {"schema": 1, "account": account, "prices": {"feed": {}}}


def test_upload_snapshot_creates_file_without_sha(monkeypatch):
    calls = {}

    def fake_get(url, headers, timeout):
        return FakeResponse(404)

    def fake_put(url, headers, json, timeout):
        calls["put"] = (url, headers, json)
        return FakeResponse(201)

    monkeypatch.setattr(publish_snapshot.requests, "get", fake_get)
    monkeypatch.setattr(publish_snapshot.requests, "put", fake_put)

    payload = make_payload("alice")
    ok = publish_snapshot.upload_snapshot(payload, "org/HONEST-feeds-live", "tok")

    assert ok is True
    url, headers, body = calls["put"]
    assert url == (
        "https://api.github.com/repos/org/HONEST-feeds-live/contents/alice.json"
    )
    assert "sha" not in body
    assert body["message"].startswith("feed: alice ")
    assert json.loads(base64.b64decode(body["content"])) == payload
    assert headers["Authorization"] == "Bearer tok"


def test_upload_snapshot_updates_existing_file_with_sha(monkeypatch):
    body = {}

    monkeypatch.setattr(
        publish_snapshot.requests,
        "get",
        lambda url, headers, timeout: FakeResponse(200, {"sha": "abc123"}),
    )

    def fake_put(url, headers, json, timeout):
        body.update(json)
        return FakeResponse(200)

    monkeypatch.setattr(publish_snapshot.requests, "put", fake_put)

    ok = publish_snapshot.upload_snapshot(
        make_payload(), "org/HONEST-feeds-live", "tok"
    )

    assert ok is True
    assert body["sha"] == "abc123"


def test_upload_snapshot_returns_false_on_http_error(monkeypatch):
    monkeypatch.setattr(
        publish_snapshot.requests,
        "get",
        lambda url, headers, timeout: FakeResponse(200, {"sha": "abc123"}),
    )
    monkeypatch.setattr(
        publish_snapshot.requests,
        "put",
        lambda url, headers, json, timeout: FakeResponse(403),
    )

    assert publish_snapshot.upload_snapshot(make_payload(), "org/repo", "tok") is False


def test_upload_snapshot_returns_false_on_network_error(monkeypatch):
    def boom(url, headers, timeout):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(publish_snapshot.requests, "get", boom)

    assert publish_snapshot.upload_snapshot(make_payload(), "org/repo", "tok") is False


def test_publish_snapshot_skips_without_env(monkeypatch):
    monkeypatch.delenv("FEED_REPO", raising=False)
    monkeypatch.delenv("FEED_TOKEN", raising=False)
    monkeypatch.setattr(
        publish_snapshot,
        "upload_snapshot",
        lambda *a, **k: pytest.fail("upload must not run without env"),
    )

    assert publish_snapshot.publish_snapshot({}, "alice") is False


def test_publish_snapshot_never_raises(monkeypatch):
    monkeypatch.setenv("FEED_REPO", "org/repo")
    monkeypatch.setenv("FEED_TOKEN", "tok")

    def boom(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(publish_snapshot, "upload_snapshot", boom)

    assert publish_snapshot.publish_snapshot({}, "alice") is False


def test_payload_contains_no_wif():
    payload = publish_snapshot.snapshot_payload({"feed": {}}, "alice")
    assert "wif" not in json.dumps(payload).lower()
```

Note: `upload_snapshot` derives the filename from `payload["account"]`; keep
the signature above and do not add a separate account parameter.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_publish_snapshot.py -v`
Expected: `ModuleNotFoundError: No module named 'publish_snapshot'`.

- [ ] **Step 3: Implement `honest/publish_snapshot.py`**

Pinned values:
- File URL: `https://api.github.com/repos/{repo}/contents/{payload['account']}.json`
- GET headers: `Authorization: Bearer {token}`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version: 2022-11-28`
- GET 200 → take `sha` from the response JSON; GET 404 → `sha = None`; any other status → return `False`.
- PUT body: `{"message": f"feed: {account} {datetime.now(timezone.utc).isoformat(timespec='seconds')}", "content": base64(json.dumps(payload)).decode(), ...}` plus `"sha": sha` only when `sha` is not `None`.
- PUT success: 200 or 201. Any other status, exception, or missing env returns `False`.
- `publish_snapshot` reads `FEED_REPO`/`FEED_TOKEN` with `os.environ.get`; if either is empty it prints `feed snapshot skipped: FEED_REPO and FEED_TOKEN must be set` and returns `False` without any HTTP call.
- Every function is pure of I/O except `upload_snapshot`; `publish_snapshot` wraps the upload in `try/except Exception` and returns `False` on error.
- Module docstring: one paragraph stating it publishes the current feed snapshot to the `HONEST-feeds-live` repo and never raises.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_publish_snapshot.py -v`
Expected: 8 passed.

- [ ] **Step 5: Format check and commit**

```bash
black --check honest/publish_snapshot.py tests/
git add honest/publish_snapshot.py tests/
git commit -m "feat: publish feed snapshots to HONEST-feeds-live via Contents API"
```

---

### Task 2: Wire the snapshot upload into the feed loop

**Files:**
- Modify: `honest/HONEST.py:44` (imports) and `honest/HONEST.py:343-357` (the `if publish:` block)
- Test: `honest/HONEST.py` structural check (below; no unit test for the event loop)

**Interfaces:**
- Consumes: `publish_snapshot(prices: dict, account: str) -> bool` from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Add the import**

Add `from publish_snapshot import publish_snapshot` to the HONEST MODULES import block, after `from proxy_list import ProxyManager` and before `from utilities import (`.

- [ ] **Step 2: Add the guarded call**

Inside `if publish:`, immediately after `publish_feed(prices, name, wif)`, add:

```python
                    try:
                        publish_snapshot(prices, name)
                    except Exception as error:
                        logger(trace(error), "publish snapshot")
```

It must sit after `publish_feed` so the public snapshot never shows data the chain rejected, and in its own `try` so an upload fault cannot trigger the block's `continue`.

- [ ] **Step 3: Verify the structure mechanically**

```bash
cd honest && python - <<'EOF'
import ast

tree = ast.parse(open("HONEST.py").read())
calls = [
    n for n in ast.walk(tree)
    if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "publish_snapshot"
]
assert len(calls) == 1, f"expected one call, found {len(calls)}"
for node in ast.walk(tree):
    if isinstance(node, ast.Try) and any(c is calls[0] for c in ast.walk(node)):
        print("guarded by try at line", node.lineno)
        break
else:
    raise SystemExit("publish_snapshot is not inside its own try block")
EOF
grep -n "from publish_snapshot import publish_snapshot" HONEST.py
```

Expected: one call, a `try` guard line, and the import line number.

- [ ] **Step 4: Verify HONEST still imports**

Run: `cd honest && python -c "import HONEST"`
Expected: no output, exit 0.

- [ ] **Step 5: Commit**

```bash
git add honest/HONEST.py
git commit -m "feat: upload feed snapshot after each successful chain publish"
```

---

### Task 3: Rollout documentation

**Files:**
- Create: `docs/feeds_live.md`

**Interfaces:**
- Consumes: the env vars and URL patterns fixed in the design.
- Produces: operator instructions only.

- [ ] **Step 1: Write `docs/feeds_live.md`**

Contents (exact values):
- Create `HONEST-feeds-live` on GitHub, enable Pages (branch `main`, root).
- Add `producers.json` listing the four BitShares account names, e.g. `["producer1", "producer2", "producer3", "producer4"]`; the org maintains it.
- For each producer, create a fine-grained PAT scoped to that repo only, with `Contents: Read and write`; set `FEED_REPO=litepresence/HONEST-feeds-live` and `FEED_TOKEN=<pat>` on that machine.
- Snapshot URL for the site: `https://raw.githubusercontent.com/<owner>/HONEST-feeds-live/main/<account>.json` (immediate) or `https://<owner>.github.io/HONEST-feeds-live/<account>.json` (Pages, ~1 min lag).
- Payload shape: `{"schema": 1, "account": "...", "prices": {...}}`; `prices.time.unix` drives staleness; treat older than 7200 s as stale.
- Failure behavior: an upload failure only logs; publishing to chain is unaffected.

- [ ] **Step 2: Commit**

```bash
git add docs/feeds_live.md
git commit -m "docs: add HONEST-feeds-live rollout instructions"
```

---

## Self-Review

- **Spec coverage:** payload envelope (Task 1), single attempt + timeout + bool/no-raise (Task 1), env vars (Task 1), upload after successful publish and isolated from the loop (Task 2), repo/Pages/tokens/`producers.json`/staleness (Task 3).
- **Step scan:** each step is one action; test code is given in full, implementation pins names, URLs, headers, status codes, and the commit-message format without transcribing the module body.
- **Type consistency:** `snapshot_payload(prices, account)`, `upload_snapshot(payload, repo, token, timeout=10)`, `publish_snapshot(prices, account)` used with the same names and order everywhere.
- **Review Focus:** unset env (Task 1 test), 404 create vs 200 update (Task 1 tests), HTTP/network failure (Task 1 tests), payload fidelity (Task 1 test), WIF absence (Task 1 test), hook isolation (Task 2 structural check).
- **Proportion:** three tasks, one small module, one hook, one doc page.
