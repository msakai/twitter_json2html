"""Entry point for Twitter DM to HTML conversion."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import dm_loader, dm_renderer


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Twitter DM JSON/XML files to HTML pages.",
    )
    parser.add_argument(
        "data_dir",
        nargs="?",
        default="data_dm",
        help="directory containing DM JSON/XML files (default: ./data_dm)",
    )
    parser.add_argument(
        "-o", "--output",
        default="output_dm",
        help="output directory (default: ./output_dm)",
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir).resolve()
    template_dir = Path(__file__).resolve().parent.parent / "templates"
    output_dir = Path(args.output).resolve()

    if not data_dir.exists():
        parser.error(f"data directory not found: {data_dir}")
        return

    print(f"Loading DMs from {data_dir}...")
    dms = dm_loader.load_all(data_dir)
    print(f"Loaded {len(dms)} DMs")

    if not dms:
        print("No DMs found.")
        return

    owner = dm_loader.detect_owner(dms)
    print(f"Owner: @{owner['screen_name']} ({owner['name']})")

    conversations = dm_loader.group_by_conversation(dms, owner["id"])
    print(f"Conversations: {len(conversations)}")

    env = dm_renderer.create_env(template_dir)
    dm_renderer.render_all(env, output_dir, conversations, owner, len(dms))

    print(f"Output written to {output_dir}/")
    print(f"  index.html")
    for screen_name in conversations:
        print(f"  conversations/{screen_name}.html")


if __name__ == "__main__":
    main()
