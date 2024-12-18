"""Platform for Glue Lock integration."""
from __future__ import annotations
from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

from .const import DOMAIN
from .glue_api import GlueApi

_LOGGER = logging.getLogger(__name__)

# Poll every 10 seconds
SCAN_INTERVAL = timedelta(seconds=10)

# Icons for different states
ICON_LOCKED = "mdi:lock"
ICON_UNLOCKED = "mdi:lock-open"
ICON_JAMMED = "mdi:lock-alert"
ICON_UNAVAILABLE = "mdi:lock-off"

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Glue Lock from a config entry."""
    api = GlueApi()
    api.set_api_key(entry.data[CONF_API_KEY])
    
    try:
        locks = await api.get_locks()
        _LOGGER.debug("Found locks: %s", locks)
        entities = [GlueLock(api, lock) for lock in locks]
        async_add_entities(entities)

        # Set up periodic polling for all locks
        async def async_update_locks(now=None):
            """Update all locks."""
            for entity in entities:
                await entity.async_update()

        # Register the periodic update
        entry.async_on_unload(
            async_track_time_interval(hass, async_update_locks, SCAN_INTERVAL)
        )

    except Exception as err:
        _LOGGER.error("Error setting up Glue Lock: %s", err)

class GlueLock(LockEntity):
    """Representation of a Glue Lock."""

    def __init__(self, api: GlueApi, lock_data: dict) -> None:
        """Initialize the lock."""
        self._api = api
        self._lock_id = lock_data["id"]
        self._attr_name = lock_data.get("description", f"Glue Lock {self._lock_id}")
        self._attr_unique_id = f"glue_lock_{self._lock_id}"
        self._last_event_time = None
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._lock_id)},
            "name": self._attr_name,
            "manufacturer": "Glue Home",
            "model": "Glue Lock",
            "sw_version": lock_data.get("firmwareVersion"),
        }
        self._attr_has_entity_name = True
        self._update_from_data(lock_data)

    @property
    def icon(self) -> str:
        """Return the icon to use in the frontend."""
        if not self._attr_available:
            return ICON_UNAVAILABLE
        if self._attr_is_jammed:
            return ICON_JAMMED
        return ICON_LOCKED if self._attr_is_locked else ICON_UNLOCKED

    def _update_from_data(self, data: dict[str, Any]) -> None:
        """Update attributes from lock data."""
        _LOGGER.debug("Updating lock %s with data: %s", self._lock_id, data)
        last_event = data.get("lastLockEvent", {})
        event_type = last_event.get("eventType", "")
        event_time = last_event.get("eventTime")
        
        # Only update state if this is a new event
        if event_time != self._last_event_time:
            self._last_event_time = event_time
            self._attr_is_locked = event_type in ["lock", "remoteLock", "autoLock"]
            _LOGGER.debug(
                "Lock %s state changed - is_locked: %s, event_type: %s, time: %s",
                self._lock_id,
                self._attr_is_locked,
                event_type,
                event_time
            )
            
        self._attr_is_jammed = data.get("connectionStatus") != "connected"
        self._attr_available = data.get("connectionStatus") == "connected"
        
        # Add additional attributes
        self._attr_extra_state_attributes = {
            "battery_level": data.get("batteryStatus"),
            "firmware_version": data.get("firmwareVersion"),
            "serial_number": data.get("serialNumber"),
            "last_event_type": event_type,
            "last_event_time": event_time,
            "connection_status": data.get("connectionStatus"),
        }

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        try:
            _LOGGER.debug("Locking %s", self._lock_id)
            await self._api.lock(self._lock_id)
            # Immediate feedback
            self._attr_is_locked = True
            self.async_write_ha_state()
            # Get actual status
            await self.async_update()
        except Exception as err:
            _LOGGER.error("Error locking device: %s", err)
            raise

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        try:
            _LOGGER.debug("Unlocking %s", self._lock_id)
            await self._api.unlock(self._lock_id)
            # Immediate feedback
            self._attr_is_locked = False
            self.async_write_ha_state()
            # Get actual status
            await self.async_update()
        except Exception as err:
            _LOGGER.error("Error unlocking device: %s", err)
            raise

    async def async_update(self) -> None:
        """Update the lock status."""
        try:
            _LOGGER.debug("Updating status for lock %s", self._lock_id)
            status = await self._api.get_lock_status(self._lock_id)
            self._update_from_data(status)
            self.async_write_ha_state()
        except Exception as err:
            _LOGGER.error("Error updating lock status: %s", err)
            self._attr_available = False