from __future__ import annotations

import logging
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN
from .const import TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up ZoneClimate entity from a config entry."""
    async_add_entities([ZoneClimate(hass, entry)], True)


class ZoneClimate(ClimateEntity):
    """Representation of a Zone Climate thermostat."""

    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
    _attr_temperature_unit = TEMP_CELSIUS
    _attr_target_temperature_step = 0.5

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.entry.entry_id)},  # Use entry.entry_id for uniqueness
            "name": self._attr_name,
            "manufacturer": "Zenntrix Software Ltd",
            "model": "Zone Climate",
        }

    def __init__(self, hass: HomeAssistant, entry):
        """Initialize the zone climate entity."""
        self.hass = hass
        self.entry = entry
        self._attr_name = entry.data["zone_name"]

        # Config
        self._zone_temp_sensor = entry.data.get("zone_temp_sensor")
        self._zone_humidity_sensor = entry.data.get("zone_humidity_sensor")
        self._trv_temp_sensors = entry.data.get("trv_temp_sensors", [])
        self._trv_humidity_sensors = entry.data.get("trv_humidity_sensors", [])
        self._primary_heating = entry.data.get("primary_heating_control")
        self._backup_heating = entry.data.get("backup_heating_control")

        # State
        self._attr_unique_id = f"{DOMAIN}_{self._attr_name.lower().replace(' ', '_')}"
        self._attr_current_temperature = None
        self._attr_target_temperature = 20.0
        self._attr_hvac_mode = HVACMode.OFF
        self._source_temp = None
        self._source_humidity = None

        # Listen to sensors
        all_sensors = []
        if self._zone_temp_sensor:
            all_sensors.append(self._zone_temp_sensor)
        if self._zone_humidity_sensor:
            all_sensors.append(self._zone_humidity_sensor)
        all_sensors.extend(self._trv_temp_sensors)
        all_sensors.extend(self._trv_humidity_sensors)

        async_track_state_change_event(
            hass,
            all_sensors,
            self._async_sensor_changed,
        )

    async def async_added_to_hass(self):
        """Run when entity is added to HA."""
        # Populate initial values
        await self.async_update()

    @callback
    async def _async_sensor_changed(self, event):
        """Handle sensor state changes."""
        await self.async_update_ha_state(force_refresh=True)

    async def async_update(self):
        """Fetch new state data for the entity."""
        temp = None
        humidity = None

        # Temperature: prefer room
        if self._zone_temp_sensor:
            state = self.hass.states.get(self._zone_temp_sensor)
            if state and state.state not in (None, "unknown", "unavailable"):
                temp = float(state.state)
                self._source_temp = "Room"

        # Fallback to TRVs
        if temp is None and self._trv_temp_sensors:
            vals = []
            for s in self._trv_temp_sensors:
                st = self.hass.states.get(s)
                if st and st.state not in (None, "unknown", "unavailable"):
                    try:
                        vals.append(float(st.state))
                    except ValueError:
                        pass
            if vals:
                temp = sum(vals) / len(vals)
                self._source_temp = "TRV"

        # Humidity: prefer room
        if self._zone_humidity_sensor:
            state = self.hass.states.get(self._zone_humidity_sensor)
            if state and state.state not in (None, "unknown", "unavailable"):
                humidity = float(state.state)
                self._source_humidity = "Room"

        # Fallback to TRVs
        if humidity is None and self._trv_humidity_sensors:
            vals = []
            for s in self._trv_humidity_sensors:
                st = self.hass.states.get(s)
                if st and st.state not in (None, "unknown", "unavailable"):
                    try:
                        vals.append(float(st.state))
                    except ValueError:
                        pass
            if vals:
                humidity = sum(vals) / len(vals)
                self._source_humidity = "TRV"

        self._attr_current_temperature = temp
        self._attr_extra_state_attributes = {
            "zone_temp_source": self._source_temp,
            "zone_humidity_source": self._source_humidity,
            "zone_temp_variation": self._calc_temp_variation(),
            "zone_humidity_variation": self._calc_humidity_variation(),
        }

    def _calc_temp_variation(self):
        """Difference between room and TRV temps."""
        if not self._zone_temp_sensor or not self._trv_temp_sensors:
            return None
        primary_state = self.hass.states.get(self._zone_temp_sensor)
        if not primary_state:
            return None
        try:
            primary_val = float(primary_state.state)
        except (ValueError, TypeError):
            return None
        trv_vals = []
        for s in self._trv_temp_sensors:
            st = self.hass.states.get(s)
            if st:
                try:
                    trv_vals.append(float(st.state))
                except (ValueError, TypeError):
                    pass
        if not trv_vals:
            return None
        return round(primary_val - (sum(trv_vals) / len(trv_vals)), 1)

    def _calc_humidity_variation(self):
        """Difference between room and TRV humidity."""
        if not self._zone_humidity_sensor or not self._trv_humidity_sensors:
            return None
        primary_state = self.hass.states.get(self._zone_humidity_sensor)
        if not primary_state:
            return None
        try:
            primary_val = float(primary_state.state)
        except (ValueError, TypeError):
            return None
        trv_vals = []
        for s in self._trv_humidity_sensors:
            st = self.hass.states.get(s)
            if st:
                try:
                    trv_vals.append(float(st.state))
                except (ValueError, TypeError):
                    pass
        if not trv_vals:
            return None
        return round(primary_val - (sum(trv_vals) / len(trv_vals)), 1)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode):
        """Set HVAC mode."""
        self._attr_hvac_mode = hvac_mode
        if hvac_mode == HVACMode.OFF:
            await self._turn_off_heating()
        elif hvac_mode == HVACMode.HEAT:
            await self._turn_on_heating()

        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        if ATTR_TEMPERATURE in kwargs:
            self._attr_target_temperature = kwargs[ATTR_TEMPERATURE]

            if self._attr_hvac_mode == HVACMode.HEAT:
                await self._turn_on_heating()

            self.async_write_ha_state()

    async def _turn_on_heating(self):
        """Turn on heating via room or TRV control."""
        service_data = {}
        if self._primary_heating.startswith("climate."):
            service = "climate.set_temperature"
            service_data = {
                "entity_id": self._primary_heating,
                "temperature": self._attr_target_temperature,
                "hvac_mode": HVACMode.HEAT,
            }
        else:
            service = "switch.turn_on"
            service_data = {"entity_id": self._primary_heating}

        await self.hass.services.async_call(
            service.split(".")[0], service.split(".")[1], service_data
        )

    async def _turn_off_heating(self):
        """Turn off heating via room or TRV control."""
        if self._primary_heating.startswith("climate."):
            service = "climate.set_hvac_mode"
            service_data = {
                "entity_id": self._primary_heating,
                "hvac_mode": HVACMode.OFF,
            }
        else:
            service = "switch.turn_off"
            service_data = {"entity_id": self._primary_heating}

        await self.hass.services.async_call(
            service.split(".")[0], service.split(".")[1], service_data
	)
