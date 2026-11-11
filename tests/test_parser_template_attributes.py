"""Tests for bare Jinja attribute access ({{ sensor.x.state }})."""
import asyncio
from pathlib import Path

import pytest

from custom_components.watchman.utils.parser_core import WatchmanParser


@pytest.fixture
def parser_client(tmp_path):
    """Create a WatchmanParser instance with a temporary database."""
    return WatchmanParser(str(tmp_path / "watchman.db"))


def _parse(tmp_path: Path, parser_client, template: str) -> set[str]:
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "sensors.yaml").write_text(
        f'value_template: "{template}"\n', encoding="utf-8"
    )
    asyncio.run(parser_client.async_parse(str(config_dir), []))
    items = parser_client.get_found_items(item_type="entity")
    return {item[0] for item in items}


@pytest.mark.parametrize(
    ("template", "expected"),
    [
        ("{{ sensor.e.state }}", "sensor.e"),
        ("{{ light.f.attributes.brightness }}", "light.f"),
        ("{{ device_tracker.phone.state }}", "device_tracker.phone"),
        ("{{ binary_sensor.door.last_changed }}", "binary_sensor.door"),
        ("{{ states.sensor.b.state }}", "sensor.b"),
    ],
)
def test_attribute_access_is_detected(parser_client, tmp_path, template, expected):
    """State-object attribute access yields the entity id."""
    assert _parse(tmp_path, parser_client, template) == {expected}


@pytest.mark.parametrize(
    "template",
    [
        "{{ sensor.host.status }}",  # hostname-like: unknown trailing property
        "{{ sensor.file.json }}",  # filename-like
        "{{ sensor.x-camera }}",  # hyphen suffix
        "{{ 'light.' ~ room }}",  # dynamic id
    ],
)
def test_non_entity_strings_are_ignored(parser_client, tmp_path, template):
    """Dot-separated strings that are not state-object properties stay ignored."""
    assert _parse(tmp_path, parser_client, template) == set()
