from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    config = entry.data
    name = config["name"]
    unique_prefix = name.lower().replace(" ", "_")

    async_add_entities(
        [
            ZoneTempSource(hass, config, f"{unique_prefix}_temp_source"),
            ZoneHumiditySource(hass, config, f"{unique_prefix}_humidity_source"),
        ]
    )


class ZoneTempSource(SensorEntity):
    def __init__(self, hass, config, uid):
        self.hass = hass
        self._primary = config["zone_temp_sensor"]
        self._backups = [
            s.strip() for s in config.get("trv_temp_sensors", "").split(",") if s.strip()
        ]
        self._attr_name = f"{config['name']} Temp Source"
        self._attr_unique_id = uid

    @property
    def native_value(self):
        state = self.hass.states.get(self._primary)
        if state and state.state not in ("unknown", "unavailable", "0"):
            return "Primary"
        elif self._backups:
            return "Backup"
        return None


class ZoneHumiditySource(SensorEntity):
    def __init__(self, hass, config, uid):
        self.hass = hass
        self._primary = config.get("zone_humidity_sensor")
        self._backups = [
            s.strip() for s in config.get("trv_humidity_sensors", "").split(",") if s.strip()
        ]
        self._attr_name = f"{config['name']} Humidity Source"
        self._attr_unique_id = uid

    @property
    def native_value(self):
        state = self.hass.states.get(self._primary)
        if state and state.state not in ("unknown", "unavailable", "0"):
            return "Primary"
        elif self._backups:
            return "Backup"
        return None
