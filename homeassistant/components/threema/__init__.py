"""The Threema Gateway integration."""

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .client import ThreemaAPIClient
from .const import CONF_API_SECRET, CONF_GATEWAY_ID, CONF_PRIVATE_KEY
from .coordinator import ThreemaConfigEntry, ThreemaCoordinator

PLATFORMS: list[Platform] = [Platform.NOTIFY, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ThreemaConfigEntry) -> bool:
    """Set up Threema Gateway from a config entry."""
    client = ThreemaAPIClient(
        hass,
        gateway_id=entry.data[CONF_GATEWAY_ID],
        api_secret=entry.data[CONF_API_SECRET],
        private_key=entry.data.get(CONF_PRIVATE_KEY),
    )

    coordinator = ThreemaCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def _async_update_listener(
    hass: HomeAssistant, entry: ThreemaConfigEntry
) -> None:
    """Reload entry when config is updated (e.g. subentry added/removed)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ThreemaConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
