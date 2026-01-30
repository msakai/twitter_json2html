"""Normalize Twitter API v1.1 and v2 JSON to a common internal format."""

from __future__ import annotations

import re
from datetime import datetime, timezone


def detect_format(data: dict) -> str:
    """Detect whether JSON data is v1.1 or v2 format.

    Returns 'v1' or 'v2'.
    """
    if "user" in data and isinstance(data["user"], dict):
        return "v1"
    if "data" in data:
        return "v2"
    if "author_id" in data and "user" not in data:
        return "v2"
    # Default to v1 if id_str exists
    if "id_str" in data:
        return "v1"
    raise ValueError("Cannot detect Twitter API format")


def normalize(data: dict) -> list[dict]:
    """Auto-detect format and normalize to common form.

    Returns a list of normalized tweets.
    """
    fmt = detect_format(data)
    if fmt == "v1":
        return [normalize_v1(data)]
    else:
        return normalize_v2(data)


def normalize_v1(data: dict) -> dict:
    """Normalize a v1.1 tweet object."""
    user = data.get("user", {})

    # Parse v1.1 date: "Fri Jul 02 13:51:55 +0000 2021"
    created_at = datetime.strptime(
        data["created_at"], "%a %b %d %H:%M:%S %z %Y"
    )

    # Parse source HTML: '<a href="...">Twitter Web App</a>' -> 'Twitter Web App'
    source_raw = data.get("source", "")
    source = _parse_source_html(source_raw)

    # Prefer full_text (extended tweet mode) over text
    text = data.get("full_text", data.get("text", ""))

    # display_text_range: [start, end] indicating visible portion of text
    # Excludes leading @mentions in replies and trailing media URLs
    display_range = data.get("display_text_range")

    entities = _normalize_v1_entities(data.get("entities", {}))

    # Collect media from entities and extended_entities
    media = _extract_v1_media(data)

    quoted_tweet = None
    if data.get("quoted_status"):
        quoted_tweet = normalize_v1(data["quoted_status"])

    return {
        "id": data.get("id_str", str(data.get("id", ""))),
        "text": text,
        "display_text_range": display_range,
        "created_at": created_at,
        "user": {
            "name": user.get("name", ""),
            "screen_name": user.get("screen_name", ""),
            "profile_image_url": user.get(
                "profile_image_url_https",
                user.get("profile_image_url", ""),
            ),
            "verified": user.get("verified", False),
        },
        "entities": entities,
        "media": media,
        "metrics": {
            "retweet_count": data.get("retweet_count", 0),
            "like_count": data.get("favorite_count", 0),
            "reply_count": None,
            "quote_count": None,
        },
        "in_reply_to_user": data.get("in_reply_to_screen_name"),
        "in_reply_to_tweet_id": data.get("in_reply_to_status_id_str"),
        "quoted_tweet": quoted_tweet,
        "source": source,
        "lang": data.get("lang"),
    }


def normalize_v2(data: dict) -> list[dict]:
    """Normalize v2 API response (single tweet or multiple)."""
    includes = data.get("includes", {})
    users_map = {}
    for u in includes.get("users", []):
        users_map[u["id"]] = u
    tweets_map = {}
    for t in includes.get("tweets", []):
        tweets_map[t["id"]] = t

    tweet_data = data.get("data", data)
    if isinstance(tweet_data, dict):
        tweet_data = [tweet_data]

    results = []
    for tw in tweet_data:
        results.append(_normalize_v2_tweet(tw, users_map, tweets_map))
    return results


def _normalize_v2_tweet(
    tw: dict, users_map: dict, tweets_map: dict
) -> dict:
    """Normalize a single v2 tweet object."""
    # Resolve user
    author_id = tw.get("author_id", "")
    user_data = users_map.get(author_id, {})

    # Parse ISO 8601 date
    created_str = tw.get("created_at", "")
    if created_str:
        created_at = datetime.fromisoformat(
            created_str.replace("Z", "+00:00")
        )
    else:
        created_at = datetime.now(timezone.utc)

    entities = _normalize_v2_entities(tw.get("entities", {}))

    metrics = tw.get("public_metrics", {})

    # Resolve quoted tweet
    quoted_tweet = None
    reply_to_id = None
    for ref in tw.get("referenced_tweets", []):
        if ref["type"] == "quoted" and ref["id"] in tweets_map:
            quoted_tweet = _normalize_v2_tweet(
                tweets_map[ref["id"]], users_map, {}
            )
        if ref["type"] == "replied_to":
            reply_to_id = ref["id"]

    return {
        "id": tw.get("id", ""),
        "text": tw.get("text", ""),
        "display_text_range": None,
        "created_at": created_at,
        "user": {
            "name": user_data.get("name", ""),
            "screen_name": user_data.get("username", ""),
            "profile_image_url": user_data.get("profile_image_url", ""),
            "verified": user_data.get("verified", False),
        },
        "entities": entities,
        "media": [],
        "metrics": {
            "retweet_count": metrics.get("retweet_count", 0),
            "like_count": metrics.get("like_count", 0),
            "reply_count": metrics.get("reply_count"),
            "quote_count": metrics.get("quote_count"),
        },
        "in_reply_to_user": None,  # v2 needs additional resolution
        "in_reply_to_tweet_id": reply_to_id,
        "quoted_tweet": quoted_tweet,
        "source": tw.get("source"),
        "lang": tw.get("lang"),
    }


def _normalize_v1_entities(entities: dict) -> dict:
    """Normalize v1.1 entities to common format."""
    urls = []
    for u in entities.get("urls", []):
        indices = u.get("indices", [0, 0])
        urls.append({
            "start": indices[0],
            "end": indices[1],
            "url": u.get("url", ""),
            "expanded_url": u.get("expanded_url", ""),
            "display_url": u.get("display_url", ""),
        })

    hashtags = []
    for h in entities.get("hashtags", []):
        indices = h.get("indices", [0, 0])
        hashtags.append({
            "start": indices[0],
            "end": indices[1],
            "tag": h.get("text", ""),
        })

    mentions = []
    for m in entities.get("user_mentions", []):
        indices = m.get("indices", [0, 0])
        mentions.append({
            "start": indices[0],
            "end": indices[1],
            "username": m.get("screen_name", ""),
        })

    return {
        "urls": urls,
        "hashtags": hashtags,
        "mentions": mentions,
    }


def _normalize_v2_entities(entities: dict) -> dict:
    """Normalize v2 entities to common format."""
    urls = []
    for u in entities.get("urls", []):
        urls.append({
            "start": u.get("start", 0),
            "end": u.get("end", 0),
            "url": u.get("url", ""),
            "expanded_url": u.get("expanded_url", ""),
            "display_url": u.get("display_url", ""),
        })

    hashtags = []
    for h in entities.get("hashtags", []):
        hashtags.append({
            "start": h.get("start", 0),
            "end": h.get("end", 0),
            "tag": h.get("tag", ""),
        })

    mentions = []
    for m in entities.get("mentions", []):
        mentions.append({
            "start": m.get("start", 0),
            "end": m.get("end", 0),
            "username": m.get("username", ""),
        })

    return {
        "urls": urls,
        "hashtags": hashtags,
        "mentions": mentions,
    }


def _extract_v1_media(data: dict) -> list[dict]:
    """Extract media items from v1.1 tweet.

    Uses extended_entities.media (preferred, has all media) or
    falls back to entities.media.
    """
    ext_ent = data.get("extended_entities", {})
    ent = data.get("entities", {})
    raw_media = ext_ent.get("media", ent.get("media", []))

    media = []
    seen_ids = set()
    for m in raw_media:
        mid = m.get("id_str", m.get("id", ""))
        if mid in seen_ids:
            continue
        seen_ids.add(mid)

        media_type = m.get("type", "photo")
        item = {
            "type": media_type,
            "url": m.get("media_url_https", m.get("media_url", "")),
            "display_url": m.get("display_url", ""),
            "expanded_url": m.get("expanded_url", ""),
        }
        # For video/animated_gif, extract video URL
        if media_type in ("video", "animated_gif"):
            variants = m.get("video_info", {}).get("variants", [])
            # Pick highest bitrate mp4
            mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
            if mp4s:
                best = max(mp4s, key=lambda v: v.get("bitrate", 0))
                item["video_url"] = best["url"]

        media.append(item)

    return media


def _parse_source_html(source: str) -> str | None:
    """Extract app name from v1.1 source HTML string."""
    if not source:
        return None
    match = re.search(r">(.+?)</a>", source)
    return match.group(1) if match else source
