import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_ENTITY_ID
from .const import DOMAIN


class ZoneClimateConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required("zone_temp_sensor"): str,
                vol.Optional("trv_temp_sensors", default=""): str,
                vol.Optional("zone_humidity_sensor", default=""): str,
                vol.Optional("trv_humidity_sensors", default=""): str,
                vol.Required("primary_heating_control"): str,
                vol.Optional("backup_heating_control", default=""): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)
