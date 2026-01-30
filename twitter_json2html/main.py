"""Entry point for twitter_json2html."""

from __future__ import annotations

from pathlib import Path

from . import loader, renderer


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    template_dir = base_dir / "templates"
    output_dir = base_dir / "output"

    if not data_dir.exists():
        print(f"Error: data directory not found: {data_dir}")
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
