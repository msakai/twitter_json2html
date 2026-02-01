"""Normalize Twitter DM JSON and XML to a common internal format."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime

from . import normalizer


def normalize_dm_json(data: dict) -> dict:
    """Normalize a JSON DM object to common format.

    JSON DMs have sender/recipient objects with full user info,
    and entities in v1.1 format.
    """
    created_at = datetime.strptime(
        data["created_at"], "%a %b %d %H:%M:%S %z %Y"
    )

    sender = data.get("sender", {})
    recipient = data.get("recipient", {})

    entities = normalizer._normalize_v1_entities(data.get("entities", {}))

    return {
        "id": data.get("id_str", str(data.get("id", ""))),
        "text": data.get("text", ""),
        "created_at": created_at,
        "sender": _extract_user(sender, data, "sender"),
        "recipient": _extract_user(recipient, data, "recipient"),
        "entities": entities,
    }


def normalize_dm_xml(xml_text: str) -> list[dict]:
    """Parse a Twitter DM XML file and normalize to common format.

    XML format uses <direct-messages type="array"> root with
    <direct_message> child elements.
    """
    root = ET.fromstring(xml_text)

    if root.tag == "direct-messages":
        results = []
        for dm_el in root.findall("direct_message"):
            results.append(_normalize_xml_dm(dm_el))
        return results
    elif root.tag == "direct_message":
        return [_normalize_xml_dm(root)]
    else:
        raise ValueError(
            f"Expected <direct-messages> or <direct_message> root, got <{root.tag}>"
        )


def _normalize_xml_dm(el: ET.Element) -> dict:
    """Normalize a single <direct_message> XML element."""
    def text(tag: str) -> str:
        child = el.find(tag)
        return child.text or "" if child is not None else ""

    created_at = datetime.strptime(
        text("created_at"), "%a %b %d %H:%M:%S %z %Y"
    )

    dm_text = text("text")
    entities = normalizer._auto_detect_entities(dm_text)

    sender_el = el.find("sender")
    recipient_el = el.find("recipient")

    sender = _parse_xml_user(sender_el) if sender_el is not None else {
        "id": text("sender_id"),
        "name": text("sender_screen_name"),
        "screen_name": text("sender_screen_name"),
        "profile_image_url": "",
    }
    recipient = _parse_xml_user(recipient_el) if recipient_el is not None else {
        "id": text("recipient_id"),
        "name": text("recipient_screen_name"),
        "screen_name": text("recipient_screen_name"),
        "profile_image_url": "",
    }

    return {
        "id": text("id"),
        "text": dm_text,
        "created_at": created_at,
        "sender": sender,
        "recipient": recipient,
        "entities": entities,
    }


def _extract_user(user_data: dict, dm_data: dict, role: str) -> dict:
    """Extract user info from JSON DM sender/recipient."""
    return {
        "id": str(
            user_data.get("id")
            or dm_data.get(f"{role}_id", "")
        ),
        "name": user_data.get("name", ""),
        "screen_name": (
            user_data.get("screen_name")
            or dm_data.get(f"{role}_screen_name", "")
        ),
        "profile_image_url": user_data.get(
            "profile_image_url_https",
            user_data.get("profile_image_url", ""),
        ),
    }


def _parse_xml_user(el: ET.Element) -> dict:
    """Parse a <sender> or <recipient> XML element."""
    def text(tag: str) -> str:
        child = el.find(tag)
        return child.text or "" if child is not None else ""

    profile_image = text("profile_image_url_https") or text("profile_image_url")

    return {
        "id": text("id"),
        "name": text("name"),
        "screen_name": text("screen_name"),
        "profile_image_url": profile_image,
    }
