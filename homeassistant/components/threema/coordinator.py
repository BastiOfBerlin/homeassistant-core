"""Data update coordinator for the Threema Gateway integration."""

from datetime import timedelta
import logging
from typing import override

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import ThreemaAPIClient, ThreemaAuthError, ThreemaConnectionError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=1)

type ThreemaConfigEntry = ConfigEntry[ThreemaCoordinator]


class ThreemaCoordinator(DataUpdateCoordinator[int]):
    """Coordinator fetching the remaining Threema Gateway credits."""

    config_entry: ThreemaConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ThreemaConfigEntry,
        client: ThreemaAPIClient,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client

    @override
    async def _async_update_data(self) -> int:
        """Fetch the remaining credits."""
        try:
            return await self.client.get_credits()
        except ThreemaAuthError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="invalid_auth",
            ) from err
        except ThreemaConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
            ) from err
