"""Config flow for Glue Lock integration."""
from __future__ import annotations

from typing import Any

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

class GlueLockConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Glue Lock."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(step_id="user")

        return self.async_create_entry(title="Glue Lock", data=user_input)
