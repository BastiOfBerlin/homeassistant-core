"""Sensor platform for Threema Gateway integration."""

from typing import override

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ThreemaConfigEntry, ThreemaCoordinator

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ThreemaConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Threema credits sensor."""
    async_add_entities([ThreemaCreditsSensor(entry)])


class ThreemaCreditsSensor(CoordinatorEntity[ThreemaCoordinator], SensorEntity):
    """Sensor reporting the remaining Threema Gateway credits."""

    _attr_has_entity_name = True
    _attr_translation_key = "credits"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, entry: ThreemaConfigEntry) -> None:
        """Initialize the credits sensor."""
        super().__init__(entry.runtime_data)
        gateway_id = self.coordinator.client.gateway_id
        self._attr_unique_id = f"{gateway_id}_credits"
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            manufacturer="Threema",
            identifiers={(DOMAIN, gateway_id)},
            name=entry.title,
        )

    @property
    @override
    def native_value(self) -> int:
        """Return the remaining credits."""
        return self.coordinator.data
