"""Tests for domain discovery via the entity registry (custom integrations)."""
import asyncio
from pathlib import Path

import pytest

from custom_components.watchman.utils.parser_core import WatchmanParser, get_domains
from homeassistant.helpers import entity_registry as er

CUSTOM_DOMAIN = "my_custom_domain"


@pytest.mark.asyncio
async def test_registry_only_domain_is_included(hass, tmp_path):
    """A domain that exists only in the entity registry is a valid domain."""
    registry = er.async_get(hass)
    registry.async_get_or_create(CUSTOM_DOMAIN, "custom_platform", "unique_1")

    domains = get_domains(hass)

    assert CUSTOM_DOMAIN in domains


@pytest.mark.asyncio
async def test_registry_only_domain_entities_are_parsed(hass, tmp_path):
    """Entity ids of a registry-only domain are picked up by the parser."""
    registry = er.async_get(hass)
    registry.async_get_or_create(CUSTOM_DOMAIN, "custom_platform", "unique_2")

    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "automations.yaml").write_text(
        """
- action:
  - service: light.turn_on
    target:
      entity_id: my_custom_domain.thing
""",
        encoding="utf-8",
    )

    parser = WatchmanParser(str(tmp_path / "watchman.db"))
    await parser.async_parse(str(config_dir), [], custom_domains=get_domains(hass))

    found = {item[0] for item in parser.get_found_items(item_type="entity")}

    assert f"{CUSTOM_DOMAIN}.thing" in found
