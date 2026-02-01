# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Run the converter
uv run python -m twitter_json2html.main [data_dir] [-o output_dir]

# Defaults: data_dir=./data, output_dir=./output
```

No test suite, linter, or formatter is configured.

## Architecture

Pipeline: `main.py` → `loader.py` → `normalizer.py` → `renderer.py` (with `tweet.py` used at render time).

1. **main.py** — CLI entry point (`argparse`). Resolves paths, orchestrates load→group→render.
2. **loader.py** — Reads all `*.json` and `*.xml` from data dir, normalizes each, deduplicates by tweet ID (JSON priority over XML), sorts by `created_at`, groups into daily/monthly dicts keyed by JST date strings.
3. **normalizer.py** — Detects Twitter API format (v1.0 XML, v1.1 JSON, v2 JSON) and converts to a common dict structure. XML uses `normalize_xml()` (parses `<status>` elements); JSON uses `normalize()` with auto-detection. v1.1 extended tweets use `full_text` instead of `text`; `display_text_range` controls visible portion. Media extracted from `extended_entities.media` (preferred) or `entities.media`. Quoted tweets are normalized recursively. Old tweets without entity metadata get URL/mention/hashtag auto-detection from plain text via `_auto_detect_entities()`.
4. **tweet.py** — Entity-aware text→HTML conversion. Replaces URL/hashtag/mention entities with links, respecting `display_text_range` to trim leading @mentions and trailing media URLs. Also renders media (photos as `<img>`, videos as `<video>`). All non-entity text is HTML-escaped.
5. **renderer.py** — Creates Jinja2 env with custom filters (`render_tweet_text`, `render_media`, `tweet_url`, `profile_image_bigger`, `format_number`, `format_datetime_jst`), then renders index + daily + monthly pages.

Templates live in `templates/`. `base.html` embeds all CSS inline. `macros.html` defines `render_tweet_card` which recurses for quoted tweets. `daily.html`, `monthly.html`, and `index.html` extend `base.html`.

## Key Design Decisions

- All datetimes stored as UTC `datetime` objects; grouped and displayed in JST (UTC+9).
- Entity indices are codepoint-based (matching Twitter's indexing), processed via `list(text)`.
- CSS is fully embedded in each HTML page — no external assets.
- Only dependency is Jinja2/MarkupSafe.
