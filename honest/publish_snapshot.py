"""
Publish the current HONEST feed snapshot to the HONEST-feeds-live repo.

Each producer uploads its own ``<account>.json`` through the GitHub Contents API
so a browser-side renderer can fetch all producers' current source tables.
Every function returns False on failure; nothing here raises.
"""

import base64
import json
import os
from datetime import datetime, timezone

import requests

API_URL = "https://api.github.com/repos/{repo}/contents/{account}.json"
FEED_REPO = "squidKid-deluxe/HONEST-feeds-live"


def snapshot_payload(prices, account):
    return {"schema": 1, "account": account, "prices": prices}


def upload_snapshot(payload, repo, token, timeout=10):
    account = payload["account"]
    url = API_URL.format(repo=repo, account=account)
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        existing = requests.get(url, headers=headers, timeout=timeout)
        if existing.status_code == 404:
            sha = None
        elif existing.status_code == 200:
            sha = existing.json()["sha"]
        else:
            print(f"feed snapshot skipped: GitHub returned {existing.status_code}")
            return False
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        body = {
            "message": f"feed: {account} {stamp}",
            "content": base64.b64encode(json.dumps(payload).encode()).decode(),
        }
        if sha is not None:
            body["sha"] = sha
        response = requests.put(url, headers=headers, json=body, timeout=timeout)
        if response.status_code in (200, 201):
            return True
        print(f"feed snapshot upload failed: GitHub returned {response.status_code}")
        return False
    except Exception as error:
        print(f"feed snapshot upload failed: {type(error).__name__}: {error}")
        return False


def publish_snapshot(prices, account):
    token = os.environ.get("FEED_TOKEN")
    if not token:
        print("feed snapshot skipped: FEED_TOKEN must be set")
        return False
    try:
        return upload_snapshot(snapshot_payload(prices, account), FEED_REPO, token)
    except Exception as error:
        print(f"feed snapshot upload failed: {type(error).__name__}: {error}")
        return False
