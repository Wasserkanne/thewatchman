"""Tests for validating device/area/floor/label references against their registries."""
import pytest

from custom_components.watchman.coordinator import (
    FilterContext,
    check_single_reference_status,
    renew_missing_references_list,
)
from homeassistant.helpers import area_registry as ar, entity_registry as er, floor_registry as fr, label_registry as lr


def _parsed_entry(ref_type: str) -> dict:
    return {
        "type": ref_type,
        "locations": {"automations.yaml": [1]},
        "automations": set(),
        "occurrences": [{"path": "automations.yaml", "line": 1, "context": None}],
    }


@pytest.fixture
def filter_context(hass) -> FilterContext:
    """Minimal filter context: no ignored states/labels, no automation exclusion."""
    return FilterContext(
        entity_registry=er.async_get(hass),
        disabled_automations=set(),
        automation_map={},
        ignored_states=set(),
        ignored_labels=set(),
        exclude_disabled=False,
    )


@pytest.mark.asyncio
async def test_existing_references_are_not_reported(hass, filter_context):
    """A reference to an existing registry object is not missing."""
    area = ar.async_get(hass).async_create("Kitchen")
    floor = fr.async_get(hass).async_create("Ground floor")
    label = lr.async_get(hass).async_create("Nightlights")

    parsed = {
        area.area_id: _parsed_entry("area"),
        floor.floor_id: _parsed_entry("floor"),
        label.label_id: _parsed_entry("label"),
    }

    assert renew_missing_references_list(hass, parsed, filter_context) == {}


@pytest.mark.asyncio
async def test_unknown_references_are_reported(hass, filter_context):
    """A reference whose registry object disappeared is reported."""
    parsed = {
        "removed_area": _parsed_entry("area"),
        "removed_floor": _parsed_entry("floor"),
        "removed_label": _parsed_entry("label"),
    }

    missing = renew_missing_references_list(hass, parsed, filter_context)

    assert set(missing) == set(parsed)


@pytest.mark.asyncio
async def test_single_reference_status_keeps_occurrences(hass, filter_context):
    """Reported references keep their config locations for the report."""
    parsed = _parsed_entry("area")

    result = check_single_reference_status(hass, "unknown_area", parsed, filter_context)

    assert result == parsed["occurrences"]
