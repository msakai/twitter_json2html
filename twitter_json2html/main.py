"""Entry point for twitter_json2html."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import loader, renderer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Twitter API JSON files to HTML pages.",
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data",
        help="directory containing JSON files (default: ./data)",
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="output directory (default: ./output)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    output_dir = Path(args.output).resolve()

    if not data_dir.exists():
        parser.error(f"data directory not found: {data_dir}")
        return

    print(f"Loading tweets from {data_dir}...")
    tweets = loader.load_all(data_dir)
    tweets = loader.sort_tweets(tweets)
    print(f"Loaded {len(tweets)} tweets")

    daily_groups = loader.group_by_day(tweets)
    monthly_groups = loader.group_by_month(tweets)
    print(f"Daily groups: {len(daily_groups)}")
    print(f"Monthly groups: {len(monthly_groups)}")

    env = renderer.create_env(template_dir)
    renderer.render_all(env, output_dir, daily_groups, monthly_groups, len(tweets))

    print(f"Output written to {output_dir}/")
    print(f"  index.html")
    for day in daily_groups:
        print(f"  daily/{day}.html")
    for month in monthly_groups:
        print(f"  monthly/{month}.html")


if __name__ == "__main__":
    main()
