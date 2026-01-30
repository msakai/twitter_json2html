"""Tweet text processing: entity-aware HTML rendering."""

from __future__ import annotations

import html as html_module


def render_tweet_html(tweet: dict) -> str:
    """Convert tweet text to HTML with clickable entities.

    Handles display_text_range to trim leading @mentions (replies)
    and trailing media t.co URLs. Replaces URLs, hashtags, and
    mentions with appropriate links. Escapes non-entity text.
    Converts newlines to <br>.
    """
    text = tweet["text"]
    entities = tweet.get("entities", {})
    display_range = tweet.get("display_text_range")

    # Determine the visible text range
    # display_text_range: [start, end] — codepoint indices
    codepoints = list(text)
    if display_range:
        disp_start, disp_end = display_range
    else:
        disp_start, disp_end = 0, len(codepoints)

    # Collect all entity spans with their replacement HTML
    # Only include entities that overlap with the display range
    replacements: list[tuple[int, int, str]] = []

    for url in entities.get("urls", []):
        if url["end"] <= disp_start or url["start"] >= disp_end:
            continue
        display = html_module.escape(url.get("display_url") or url.get("expanded_url") or url["url"])
        expanded = html_module.escape(url.get("expanded_url") or url["url"])
        replacement = f'<a href="{expanded}" class="tweet-link" target="_blank" rel="noopener">{display}</a>'
        replacements.append((url["start"], url["end"], replacement))

    for tag in entities.get("hashtags", []):
        if tag["end"] <= disp_start or tag["start"] >= disp_end:
            continue
        tag_text = html_module.escape(tag["tag"])
        url = f"https://twitter.com/hashtag/{tag_text}"
        replacement = f'<a href="{url}" class="tweet-hashtag" target="_blank" rel="noopener">#{tag_text}</a>'
        replacements.append((tag["start"], tag["end"], replacement))

    for mention in entities.get("mentions", []):
        if mention["end"] <= disp_start or mention["start"] >= disp_end:
            continue
        username = html_module.escape(mention["username"])
        url = f"https://twitter.com/{username}"
        replacement = f'<a href="{url}" class="tweet-mention" target="_blank" rel="noopener">@{username}</a>'
        replacements.append((mention["start"], mention["end"], replacement))

    # Sort by start position descending to replace from end to start
    replacements.sort(key=lambda r: r[0], reverse=True)

    # Trim to display range first, then apply replacements
    # Work with the full codepoints array but only output the display range
    visible = codepoints[disp_start:disp_end]

    # Adjust replacement indices relative to disp_start
    for start, end, replacement in replacements:
        adj_start = start - disp_start
        adj_end = end - disp_start
        # Clamp to visible range
        if adj_start < 0:
            adj_start = 0
        if adj_end > len(visible):
            adj_end = len(visible)
        if adj_start < adj_end:
            visible[adj_start:adj_end] = [replacement]

    # Escape non-entity parts and join
    result_parts = []
    for part in visible:
        if part.startswith("<a "):
            result_parts.append(part)
        else:
            result_parts.append(html_module.escape(part))

    result = "".join(result_parts)
    result = result.replace("\n", "<br>")
    return result


def render_media_html(tweet: dict) -> str:
    """Render media attachments (photos, videos) as HTML."""
    media = tweet.get("media", [])
    if not media:
        return ""

    parts = []
    for m in media:
        mtype = m.get("type", "photo")
        if mtype == "photo":
            url = html_module.escape(m["url"])
            expanded = html_module.escape(m.get("expanded_url", m["url"]))
            parts.append(
                f'<a href="{expanded}" target="_blank" rel="noopener">'
                f'<img class="tweet-media-img" src="{url}" alt="" loading="lazy">'
                f'</a>'
            )
        elif mtype in ("video", "animated_gif"):
            video_url = m.get("video_url", "")
            poster = html_module.escape(m["url"])
            if video_url:
                video_url = html_module.escape(video_url)
                loop = " loop" if mtype == "animated_gif" else ""
                autoplay = " autoplay muted" if mtype == "animated_gif" else " controls"
                parts.append(
                    f'<video class="tweet-media-video" poster="{poster}"'
                    f'{autoplay}{loop} preload="metadata">'
                    f'<source src="{video_url}" type="video/mp4">'
                    f'</video>'
                )
            else:
                # Fallback to poster image
                parts.append(
                    f'<img class="tweet-media-img" src="{poster}" alt="" loading="lazy">'
                )

    if not parts:
        return ""

    return '<div class="tweet-media">' + "".join(parts) + '</div>'


def get_profile_image_url(url: str, size: str = "bigger") -> str:
    """Convert profile image URL size.

    Twitter uses suffixes like _normal, _bigger, _mini, _original.
    Default converts _normal to _bigger for better quality.
    """
    if not url:
        return ""
    return url.replace("_normal.", f"_{size}.")


def get_tweet_url(tweet: dict) -> str:
    """Generate the URL to view the tweet on X/Twitter."""
    screen_name = tweet.get("user", {}).get("screen_name", "")
    tweet_id = tweet.get("id", "")
    return f"https://twitter.com/{screen_name}/status/{tweet_id}"
