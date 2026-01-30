"""Load JSON files from data directory and group tweets by date."""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import timezone, timedelta
from pathlib import Path

from . import normalizer

JST = timezone(timedelta(hours=9))


def load_all(data_dir: Path) -> list[dict]:
    """Load all JSON files from data_dir and return normalized tweets."""
    tweets = []
    for json_path in sorted(data_dir.glob("*.json")):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        try:
            normalized = normalizer.normalize(data)
            tweets.extend(normalized)
        except (ValueError, KeyError) as e:
            print(f"Warning: skipping {json_path.name}: {e}")
    return tweets


def sort_tweets(tweets: list[dict]) -> list[dict]:
    """Sort tweets by created_at ascending."""
    return sorted(tweets, key=lambda t: t["created_at"])


def group_by_day(tweets: list[dict]) -> dict[str, list[dict]]:
    """Group tweets by JST date (YYYY-MM-DD)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for tweet in tweets:
        jst_dt = tweet["created_at"].astimezone(JST)
        day_key = jst_dt.strftime("%Y-%m-%d")
        groups[day_key].append(tweet)
    return dict(sorted(groups.items()))


def group_by_month(tweets: list[dict]) -> dict[str, list[dict]]:
    """Group tweets by JST month (YYYY-MM)."""
    groups: dict[str, list[dict]] = defaultdict(list)
    for tweet in tweets:
        jst_dt = tweet["created_at"].astimezone(JST)
        month_key = jst_dt.strftime("%Y-%m")
        groups[month_key].append(tweet)
    return dict(sorted(groups.items()))
