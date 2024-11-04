"""Platform for Glue Lock integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, CONF_LOCKS, CONF_LOCK_ID, CONF_LOCK_NAME
from .glue_api import GlueApi

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Glue Lock from a config entry."""
    api = GlueApi()
    api.set_api_key(entry.data[CONF_API_KEY])
    
    locks_data = entry.data.get(CONF_LOCKS, [])
    _LOGGER.debug("Setting up locks: %s", locks_data)
    
    entities = []
    for lock in locks_data:
        try:
            # Get initial status
            lock_status = await api.get_lock_status(lock[CONF_LOCK_ID])
            entities.append(GlueLock(api, lock[CONF_LOCK_ID], lock[CONF_LOCK_NAME], lock_status))
        except Exception as err:
            _LOGGER.error("Error setting up lock %s: %s", lock[CONF_LOCK_ID], err)
    
    if entities:
        async_add_entities(entities)

class GlueLock(LockEntity):
    """Representation of a Glue Lock."""

    def __init__(self, api: GlueApi, lock_id: str, name: str, initial_status: dict) -> None:
        """Initialize the lock."""
        self._api = api
        self._lock_id = lock_id
        self._attr_name = name
        self._attr_unique_id = f"glue_lock_{lock_id}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, lock_id)},
            "name": name,
            "manufacturer": "Glue Home",
            "model": "Glue Lock",
        }
        self._update_from_data(initial_status)

    def _update_from_data(self, data: dict[str, Any]) -> None:
        """Update attributes from lock data."""
        _LOGGER.debug("Updating lock %s with data: %s", self._lock_id, data)
        last_event = data.get("lastLockEvent", {})
        self._attr_is_locked = last_event.get("eventType") == "lock"
        self._attr_is_jammed = data.get("connectionStatus") != "connected"
        self._attr_available = data.get("connectionStatus") == "connected"

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the device."""
        try:
            await self._api.lock(self._lock_id)
            self._attr_is_locked = True
        except Exception as err:
            _LOGGER.error("Error locking device: %s", err)

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the device."""
        try:
            await self._api.unlock(self._lock_id)
            self._attr_is_locked = False
        except Exception as err:
            _LOGGER.error("Error unlocking device: %s", err)

    async def async_update(self) -> None:
        """Update the lock status."""
        try:
            data = await self._api.get_lock_status(self._lock_id)
            self._update_from_data(data)
        except Exception as err:
            _LOGGER.error("Error updating lock status: %s", err)
            self._attr_available = False