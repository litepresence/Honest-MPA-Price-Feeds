import base64
import json

import publish_snapshot
import pytest
import requests


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


def test_publish_snapshot_skips_without_token(monkeypatch):
    monkeypatch.delenv("FEED_TOKEN", raising=False)
    monkeypatch.setattr(
        publish_snapshot,
        "upload_snapshot",
        lambda *a, **k: pytest.fail("upload must not run without a token"),
    )

    assert publish_snapshot.publish_snapshot({}, "alice") is False


def test_publish_snapshot_uses_hardcoded_repo(monkeypatch):
    monkeypatch.setenv("FEED_TOKEN", "tok")
    monkeypatch.delenv("FEED_REPO", raising=False)
    seen = {}

    def fake_upload(payload, repo, token, timeout=10):
        seen.update(payload=payload, repo=repo, token=token)
        return True

    monkeypatch.setattr(publish_snapshot, "upload_snapshot", fake_upload)

    assert publish_snapshot.publish_snapshot({"feed": {}}, "alice") is True
    assert seen["repo"] == publish_snapshot.FEED_REPO
    assert seen["repo"] == "squidKid-deluxe/HONEST-feeds-live"
    assert seen["token"] == "tok"
    assert seen["payload"]["account"] == "alice"


def test_publish_snapshot_never_raises(monkeypatch):
    monkeypatch.setenv("FEED_TOKEN", "tok")

    def boom(*args, **kwargs):
        raise RuntimeError("unexpected")

    monkeypatch.setattr(publish_snapshot, "upload_snapshot", boom)

    assert publish_snapshot.publish_snapshot({}, "alice") is False


def test_payload_contains_no_wif():
    payload = publish_snapshot.snapshot_payload({"feed": {}}, "alice")
    assert "wif" not in json.dumps(payload).lower()
