from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    EntitySelectorConfig,
)

from .const import DOMAIN


class ZoneClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Zone Climate."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Step 1: user input."""
        if user_input is not None:
            return self.async_create_entry(
                title=user_input["zone_name"],
                data=user_input,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("zone_name"): str,

                    # Room sensors
                    vol.Optional("zone_temp_sensor"): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),
                    vol.Optional("zone_humidity_sensor"): EntitySelector(
                        EntitySelectorConfig(domain="sensor")
                    ),

                    # TRV fallback sensors (multi select)
                    vol.Optional("trv_temp_sensors"): EntitySelector(
                        EntitySelectorConfig(domain="sensor", multiple=True)
                    ),
                    vol.Optional("trv_humidity_sensors"): EntitySelector(
                        EntitySelectorConfig(domain="sensor", multiple=True)
                    ),

                    # Heating controls (climate or switch)
                    vol.Required("primary_heating_control"): EntitySelector(
                        EntitySelectorConfig(domain=["climate", "switch"])
                    ),
                    vol.Optional("backup_heating_control"): EntitySelector(
                        EntitySelectorConfig(domain=["climate", "switch"])
                    ),
                }
            ),
        )
