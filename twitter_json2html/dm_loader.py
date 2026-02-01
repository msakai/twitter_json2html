"""Load DM JSON/XML files from data directory and group by conversation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from . import dm_normalizer


def load_all(data_dir: Path) -> list[dict]:
    """Load all JSON and XML DM files from data_dir.

    Deduplicates by DM ID (JSON takes priority over XML).
    """
    dms_by_id: dict[str, dict] = {}

    # Load JSON files first (higher priority)
    for json_path in sorted(data_dir.glob("*.json")):
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        try:
            if isinstance(data, list):
                for item in data:
                    dm = dm_normalizer.normalize_dm_json(item)
                    dms_by_id[dm["id"]] = dm
            else:
                dm = dm_normalizer.normalize_dm_json(data)
                dms_by_id[dm["id"]] = dm
        except (ValueError, KeyError) as e:
            print(f"Warning: skipping {json_path.name}: {e}")

    # Load XML files (skip if ID already seen from JSON)
    for xml_path in sorted(data_dir.glob("*.xml")):
        with open(xml_path, encoding="utf-8") as f:
            xml_text = f.read()
        try:
            normalized = dm_normalizer.normalize_dm_xml(xml_text)
            for dm in normalized:
                if dm["id"] not in dms_by_id:
                    dms_by_id[dm["id"]] = dm
        except (ValueError, KeyError, ET.ParseError) as e:
            print(f"Warning: skipping {xml_path.name}: {e}")

    return list(dms_by_id.values())


def detect_owner(dms: list[dict]) -> dict:
    """Detect the owner (most frequent user) across all DMs.

    Returns the user dict of the most frequent participant.
    """
    user_counter: Counter[str] = Counter()
    user_info: dict[str, dict] = {}

    for dm in dms:
        for role in ("sender", "recipient"):
            user = dm[role]
            uid = user["id"]
            user_counter[uid] += 1
            # Keep the most recent user info
            user_info[uid] = user

    if not user_counter:
        raise ValueError("No DMs found")

    owner_id = user_counter.most_common(1)[0][0]
    return user_info[owner_id]


def group_by_conversation(
    dms: list[dict], owner_id: str
) -> dict[str, list[dict]]:
    """Group DMs by conversation partner.

    Each conversation is keyed by the partner's screen_name.
    Self-messages (sender_id == recipient_id) go under "_self".
    Messages are sorted by created_at ascending within each conversation.
    Conversations are ordered by their earliest message.
    """
    conversations: dict[str, list[dict]] = {}

    for dm in dms:
        sender_id = dm["sender"]["id"]
        recipient_id = dm["recipient"]["id"]

        if sender_id == recipient_id:
            key = "_self"
        elif sender_id == owner_id:
            key = dm["recipient"]["screen_name"]
        else:
            key = dm["sender"]["screen_name"]

        if key not in conversations:
            conversations[key] = []
        conversations[key].append(dm)

    # Sort messages within each conversation by created_at
    for key in conversations:
        conversations[key].sort(key=lambda d: d["created_at"])

    # Sort conversations by earliest message
    sorted_convs = dict(
        sorted(
            conversations.items(),
            key=lambda item: item[1][0]["created_at"],
        )
    )

    return sorted_convs
