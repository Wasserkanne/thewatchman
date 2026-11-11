"""Tests for the missing references sensor."""
import pytest

from custom_components.watchman.const import (
    COORD_DATA_MISSING_REFERENCES,
    COORD_DATA_REFERENCE_ATTRS,
    DOMAIN,
    SENSOR_MISSING_REFERENCES,
)
from tests import async_init_integration

from homeassistant.helpers import entity_registry as er


@pytest.mark.asyncio
async def test_missing_references_sensor(hass):
    """The sensor exposes the count and the list of missing registry references."""
    config_entry = await async_init_integration(hass)

    ent_reg = er.async_get(hass)
    entity_id = next(
        entry.entity_id
        for entry in ent_reg.entities.values()
        if entry.unique_id == f"watchman_{SENSOR_MISSING_REFERENCES}"
    )

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_set_updated_data(
        {
            **coordinator.data,
            COORD_DATA_MISSING_REFERENCES: 2,
            COORD_DATA_REFERENCE_ATTRS: [
                {"id": "6a1b3c4d5e6f", "type": "device", "occurrences": "automations.yaml:5"},
                {"id": "kitchen", "type": "area", "occurrences": "automations.yaml:7"},
            ],
        }
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)

    assert state is not None
    assert state.state == "2"
    assert [ref["id"] for ref in state.attributes["references"]] == [
        "6a1b3c4d5e6f",
        "kitchen",
    ]
    assert [ref["type"] for ref in state.attributes["references"]] == ["device", "area"]
