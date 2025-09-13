from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([ZoneClimate(hass, entry.data)])


class ZoneClimate(ClimateEntity):
    def __init__(self, hass, config):
        self.hass = hass
        self._config = config
        self._attr_name = config["name"]
        self._attr_unique_id = f"{config['name'].lower().replace(' ', '_')}_climate"

        self._primary_temp = config["zone_temp_sensor"]
        self._backup_temps = [
            s.strip() for s in config.get("trv_temp_sensors", "").split(",") if s.strip()
        ]
        self._primary_humidity = config.get("zone_humidity_sensor")
        self._backup_humidities = [
            s.strip() for s in config.get("trv_humidity_sensors", "").split(",") if s.strip()
        ]
        self._primary_control = config["primary_heating_control"]
        self._backup_control = config.get("backup_heating_control")

        # Defaults
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_supported_features = SUPPORT_TARGET_TEMPERATURE
        self._attr_hvac_modes = [HVAC_MODE_HEAT, HVAC_MODE_OFF]
        self._attr_hvac_mode = HVAC_MODE_OFF
        self._attr_target_temperature = 20.0

    @property
    def device_info(self):
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Custom",
            model="Zone Climate",
        )

    @property
    def current_temperature(self):
        """Return the effective room temperature (primary or fallback)."""
        state = self.hass.states.get(self._primary_temp)
        if state and self._is_valid_number(state.state):
            return float(state.state)

        vals = [
            float(s.state)
            for s in (self.hass.states.get(eid) for eid in self._backup_temps)
            if s and self._is_valid_number(s.state)
        ]
        return sum(vals) / len(vals) if vals else None

    def set_temperature(self, **kwargs):
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        self._attr_target_temperature = temp

        if self._primary_control.startswith("climate."):
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "climate",
                    "set_temperature",
                    {"entity_id": self._primary_control, "temperature": temp, "hvac_mode": "heat"},
                )
            )
        else:
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "switch", "turn_on", {"entity_id": self._primary_control}
                )
            )

    def set_hvac_mode(self, hvac_mode):
        self._attr_hvac_mode = hvac_mode
        if hvac_mode == HVAC_MODE_OFF:
            self._turn_off(self._primary_control)
            if self._backup_control:
                self._turn_off(self._backup_control)
        elif hvac_mode == HVAC_MODE_HEAT:
            self._turn_on(self._primary_control)

    #
    # --- Helpers ---
    #
    def _is_valid_number(self, val):
        try:
            return float(val) > 0
        except (ValueError, TypeError):
            return False

    def _turn_on(self, eid):
        if eid.startswith("climate."):
            self.hass.async_create_task(
                self.hass.services.async_call(
                    "climate", "set_hvac_mode", {"entity_id": eid, "hvac_mode": "heat"}
                )
            )
        else:
            self.hass.async_create_task(
                self.hass.services.async_call("switch", "turn_on", {"entity_id": eid})
            )

    def _turn_off(self, eid):
        if eid.startswith("climate."):
            self.hass.async_create_task(
