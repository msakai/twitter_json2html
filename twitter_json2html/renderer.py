"""Render HTML output using Jinja2 templates."""

from __future__ import annotations

from datetime import timedelta, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup

from . import tweet as tweet_mod

JST = timezone(timedelta(hours=9))


def create_env(template_dir: Path) -> Environment:
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=False,
    )

    env.filters["render_tweet_text"] = _filter_render_tweet_text
    env.filters["render_media"] = _filter_render_media
    env.filters["tweet_url"] = _filter_tweet_url
    env.filters["profile_image_bigger"] = _filter_profile_image_bigger
    env.filters["format_number"] = _filter_format_number
    env.filters["format_datetime_jst"] = _filter_format_datetime_jst

    return env


def render_all(
    env: Environment,
    output_dir: Path,
    daily_groups: dict[str, list[dict]],
    monthly_groups: dict[str, list[dict]],
    total_tweets: int,
) -> None:
    """Render all HTML pages."""
    # Create output directories
    (output_dir / "daily").mkdir(parents=True, exist_ok=True)
    (output_dir / "monthly").mkdir(parents=True, exist_ok=True)

    # Render index
    index_tmpl = env.get_template("index.html")
    index_html = index_tmpl.render(
        daily_groups=daily_groups,
        monthly_groups=monthly_groups,
        total_tweets=total_tweets,
    )
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")

    # Render daily pages
    daily_tmpl = env.get_template("daily.html")
    for day, tweets in daily_groups.items():
        html = daily_tmpl.render(day=day, tweets=tweets)
        (output_dir / "daily" / f"{day}.html").write_text(
            html, encoding="utf-8"
        )

    # Render monthly pages
    monthly_tmpl = env.get_template("monthly.html")
    for month, tweets in monthly_groups.items():
        html = monthly_tmpl.render(month=month, tweets=tweets)
        (output_dir / "monthly" / f"{month}.html").write_text(
            html, encoding="utf-8"
        )


def _filter_render_tweet_text(tw: dict) -> Markup:
    """Jinja2 filter to render tweet text as HTML."""
    return Markup(tweet_mod.render_tweet_html(tw))


def _filter_render_media(tw: dict) -> Markup:
    """Jinja2 filter to render tweet media as HTML."""
    return Markup(tweet_mod.render_media_html(tw))


def _filter_tweet_url(tw: dict) -> str:
    """Jinja2 filter to get tweet URL."""
    return tweet_mod.get_tweet_url(tw)


def _filter_profile_image_bigger(url: str) -> str:
    """Jinja2 filter to get bigger profile image."""
    return tweet_mod.get_profile_image_url(url, "bigger")


def _filter_format_number(n: int | None) -> str:
    """Format number with commas."""
    if n is None:
        return "0"
    return f"{n:,}"


def _filter_format_datetime_jst(dt) -> str:
    """Format datetime in JST."""
    jst_dt = dt.astimezone(JST)
    return jst_dt.strftime("%Y-%m-%d %H:%M")
