"""Test the Threema Gateway sensor platform."""

from unittest.mock import AsyncMock, patch

from freezegun.api import FrozenDateTimeFactory
import pytest
from syrupy.assertion import SnapshotAssertion

from homeassistant.components.threema.client import (
    ThreemaAuthError,
    ThreemaConnectionError,
)
from homeassistant.components.threema.coordinator import UPDATE_INTERVAL
from homeassistant.config_entries import SOURCE_REAUTH
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.common import MockConfigEntry, async_fire_time_changed, snapshot_platform

ENTITY_ID = "sensor.threema_testgwy_credits"


async def _setup_sensor_platform(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    """Set up the integration with only the sensor platform."""
    config_entry.add_to_hass(hass)
    with patch("homeassistant.components.threema.PLATFORMS", [Platform.SENSOR]):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_get_credits")
async def test_sensor(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the credits sensor."""
    await _setup_sensor_platform(hass, mock_config_entry)

    await snapshot_platform(hass, entity_registry, snapshot, mock_config_entry.entry_id)


async def test_sensor_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_credits: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the credits sensor picks up a new balance on the next poll."""
    await _setup_sensor_platform(hass, mock_config_entry)
    assert hass.states.get(ENTITY_ID).state == "1000"

    mock_get_credits.return_value = 990
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == "990"


async def test_sensor_unavailable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_credits: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the credits sensor becomes unavailable and recovers."""
    await _setup_sensor_platform(hass, mock_config_entry)

    mock_get_credits.side_effect = ThreemaConnectionError("Connection refused")
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE

    mock_get_credits.side_effect = None
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == "1000"


async def test_sensor_auth_error_starts_reauth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_get_credits: AsyncMock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test an auth error during polling starts a reauth flow."""
    await _setup_sensor_platform(hass, mock_config_entry)

    mock_get_credits.side_effect = ThreemaAuthError("Invalid credentials")
    freezer.tick(UPDATE_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE
    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == mock_config_entry.entry_id
