"""Tests for device/area/floor/label references (target registry ids)."""
import asyncio
from pathlib import Path

import pytest

from custom_components.watchman.utils.parser_core import WatchmanParser

AUTOMATION = """
- id: lights_on_motion
  alias: Lights on motion
  triggers:
  - trigger: device
    device_id: 6a1b3c4d5e6f
    domain: light
    type: turned_on
  actions:
  - action: light.turn_on
    target:
      area_id: kitchen
      floor_id: ground
      label_id: nightlights
"""


@pytest.fixture
def parser_client(tmp_path):
    """Create a WatchmanParser instance with a temporary database."""
    return WatchmanParser(str(tmp_path / "watchman.db"))


def _write_config(tmp_path: Path, content: str) -> str:
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "automations.yaml").write_text(content, encoding="utf-8")
    return str(config_dir)


def test_target_references_are_collected(parser_client, tmp_path):
    """device_id/area_id/floor_id/label_id are items with their own type."""
    config_dir = _write_config(tmp_path, AUTOMATION)

    asyncio.run(parser_client.async_parse(config_dir, []))
    items = parser_client.get_found_items(item_type="all")
    found = {(item[3], item[0]) for item in items}

    assert ("device", "6a1b3c4d5e6f") in found
    assert ("area", "kitchen") in found
    assert ("floor", "ground") in found
    assert ("label", "nightlights") in found

    # entity and service detection is unaffected
    assert ("service", "light.turn_on") in found


def test_target_reference_lists(parser_client, tmp_path):
    """A list of ids yields one item per entry."""
    config_dir = _write_config(
        tmp_path,
        """
- action:
  - service: light.turn_on
    target:
      area_id:
      - kitchen
      - living_room
""",
    )

    asyncio.run(parser_client.async_parse(config_dir, []))
    items = parser_client.get_found_items(item_type="all")
    areas = {item[0] for item in items if item[3] == "area"}

    assert areas == {"kitchen", "living_room"}


def test_templates_and_tags_are_skipped(parser_client, tmp_path):
    """Templated or secret reference ids cannot be validated, so they are ignored."""
    config_dir = _write_config(
        tmp_path,
        """
- action:
  - service: light.turn_on
    target:
      device_id: "{{ trigger.event.data.device_id }}"
      area_id: !secret secret_area
""",
    )

    asyncio.run(parser_client.async_parse(config_dir, []))
    items = parser_client.get_found_items(item_type="all")

    assert [item for item in items if item[3] in ("device", "area", "floor", "label")] == []


def test_reference_item_carries_automation_context(parser_client, tmp_path):
    """References inherit the automation context like entities do."""
    config_dir = _write_config(tmp_path, AUTOMATION)

    asyncio.run(parser_client.async_parse(config_dir, []))
    items = parser_client.get_found_items(item_type="all")
    device_items = [item for item in items if item[3] == "device"]

    assert device_items
    parent_type, parent_id = device_items[0][4], device_items[0][6]
    assert parent_type == "automation"
    assert parent_id == "lights_on_motion"
