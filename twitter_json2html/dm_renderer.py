"""Render DM HTML output using Jinja2 templates."""

from __future__ import annotations

from datetime import timedelta, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from . import tweet as tweet_mod

JST = timezone(timedelta(hours=9))


def create_env(template_dir: Path) -> Environment:
    """Create Jinja2 environment with DM-specific filters."""
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
    )

    env.filters["render_dm_text"] = _filter_render_dm_text
    env.filters["profile_image_bigger"] = _filter_profile_image_bigger
    env.filters["format_datetime_jst"] = _filter_format_datetime_jst

    return env


def render_all(
    env: Environment,
    output_dir: Path,
    conversations: dict[str, list[dict]],
    owner: dict,
    total: int,
) -> None:
    """Render all DM HTML pages."""
    (output_dir / "conversations").mkdir(parents=True, exist_ok=True)

    # Build conversation summary for index
    conv_summary = []
    for screen_name, dms in conversations.items():
        # Find the partner user info
        if screen_name == "_self":
            partner = owner.copy()
            partner["screen_name"] = "_self"
            display_name = f'{owner["name"]} (self)'
            display_screen_name = owner["screen_name"]
        else:
            # Find partner from messages
            partner = _find_partner(dms, owner["id"])
            display_name = partner["name"]
            display_screen_name = partner["screen_name"]

        conv_summary.append({
            "screen_name": screen_name,
            "display_name": display_name,
            "display_screen_name": display_screen_name,
            "profile_image_url": partner["profile_image_url"],
            "message_count": len(dms),
            "last_message_at": dms[-1]["created_at"],
        })

    # Render index
    index_tmpl = env.get_template("dm_index.html")
    index_html = index_tmpl.render(
        conversations=conv_summary,
        total=total,
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Render each conversation page
    conv_tmpl = env.get_template("dm_conversation.html")
    for screen_name, dms in conversations.items():
        if screen_name == "_self":
            partner_name = f'{owner["name"]} (self)'
            partner_screen_name = owner["screen_name"]
        else:
            partner = _find_partner(dms, owner["id"])
            partner_name = partner["name"]
            partner_screen_name = partner["screen_name"]

        html = conv_tmpl.render(
            screen_name=screen_name,
            partner_name=partner_name,
            partner_screen_name=partner_screen_name,
            messages=dms,
            owner=owner,
        )
        (output_dir / "conversations" / f"{screen_name}.html").write_text(
            html, encoding="utf-8"
        )


def _find_partner(dms: list[dict], owner_id: str) -> dict:
    """Find the conversation partner's user info from message list."""
    for dm in dms:
        if dm["sender"]["id"] != owner_id:
            return dm["sender"]
        if dm["recipient"]["id"] != owner_id:
            return dm["recipient"]
    # Fallback: self-conversation
    return dms[0]["sender"]


def _filter_render_dm_text(dm: dict) -> Markup:
    """Jinja2 filter to render DM text as HTML.

    Adapts the DM dict to look like a tweet for render_tweet_html().
    """
    tweet_like = {
        "text": dm["text"],
        "entities": dm.get("entities", {}),
        "display_text_range": None,
    }
    return Markup(tweet_mod.render_tweet_html(tweet_like))


def _filter_profile_image_bigger(url: str) -> str:
    """Jinja2 filter to get bigger profile image."""
    return tweet_mod.get_profile_image_url(url, "bigger")


def _filter_format_datetime_jst(dt) -> str:
    """Format datetime in JST."""
    jst_dt = dt.astimezone(JST)
    return jst_dt.strftime("%Y-%m-%d %H:%M")
