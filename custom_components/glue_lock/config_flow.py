"""Config flow for Glue Lock integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import (
    CONF_API_KEY,
    CONF_PASSWORD,
    CONF_USERNAME,
)
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN, 
    CONF_AUTH_METHOD, 
    AUTH_API_KEY, 
    AUTH_CREDENTIALS,
    CONF_LOCKS,
    CONF_LOCK_ID,
    CONF_LOCK_NAME,
)
from .glue_api import GlueApi, GlueApiError, GlueAuthError

_LOGGER = logging.getLogger(__name__)

class GlueLockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Glue Lock."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api = GlueApi()
        self._api_key = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({
                    vol.Required(CONF_AUTH_METHOD, default=AUTH_CREDENTIALS): vol.In({
                        AUTH_CREDENTIALS: "Username and Password",
                        AUTH_API_KEY: "API Key",
                    })
                })
            )

        if user_input[CONF_AUTH_METHOD] == AUTH_CREDENTIALS:
            return await self.async_step_credentials()
        return await self.async_step_api_key()

    async def async_step_credentials(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the credentials step."""
        errors = {}

        if user_input is not None:
            try:
                self._api_key = await self._api.authenticate(
                    user_input[CONF_USERNAME],
                    user_input[CONF_PASSWORD],
                )
                return await self.async_step_fetch_locks()
            except GlueAuthError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="credentials",
            data_schema=vol.Schema({
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_PASSWORD): str,
            }),
            errors=errors,
        )

    async def async_step_api_key(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the API key step."""
        errors = {}

        if user_input is not None:
            try:
                self._api_key = user_input[CONF_API_KEY]
                self._api.set_api_key(self._api_key)
                return await self.async_step_fetch_locks()
            except GlueApiError:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="api_key",
            data_schema=vol.Schema({
                vol.Required(CONF_API_KEY): str,
            }),
            errors=errors,
        )

    async def async_step_fetch_locks(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Fetch and store lock information."""
        try:
            self._api.set_api_key(self._api_key)
            locks_data = await self._api.get_locks()
            _LOGGER.debug("Found locks: %s", locks_data)

            # Process locks data
            locks = []
            for lock in locks_data:
                locks.append({
                    CONF_LOCK_ID: lock["id"],
                    CONF_LOCK_NAME: lock.get("description", f"Glue Lock {lock['id']}")
                })

            # Create the config entry
            return self.async_create_entry(
                title="Glue Lock",
                data={
                    CONF_API_KEY: self._api_key,
                    CONF_LOCKS: locks,
                }
            )
        except Exception as err:
            _LOGGER.error("Error fetching locks: %s", err)
            return self.async_abort(reason="cannot_connect")
