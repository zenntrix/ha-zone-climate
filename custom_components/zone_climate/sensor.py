import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity import Entity
from .const import DOMAIN
from .const import TEMP_CELSIUS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Zone Climate sensors from config entry."""
    zone_name = entry.data.get("zone_name")
    zone_temp_sensor = entry.data.get("zone_temp_sensor")
    trv_temp_sensors = entry.data.get("trv_temp_sensors", [])
    zone_humidity_sensor = entry.data.get("zone_humidity_sensor")
    trv_humidity_sensors = entry.data.get("trv_humidity_sensors", [])

    entities = [
        ZoneTemperatureSensor(
            entry=entry,
            name=f"{zone_name} Temperature",
            zone_temp_sensor=zone_temp_sensor,
            trv_temp_sensors=trv_temp_sensors,
        ),
        ZoneHumiditySensor(
            entry=entry,
            name=f"{zone_name} Humidity",
            zone_humidity_sensor=zone_humidity_sensor,
            trv_humidity_sensors=trv_humidity_sensors,
        ),
        ZoneSensor(entry, f"{zone_name} Temperature Source", "zone_temp_source"),
        ZoneSensor(entry, f"{zone_name} Humidity Source", "zone_humidity_source"),
        ZoneSensor(entry, f"{zone_name} Temperature Variation", "zone_temp_variation"),
        ZoneSensor(entry, f"{zone_name} Humidity Variation", "zone_humidity_variation"),
    ]
    async_add_entities(entities, True)


class ZoneSensor(Entity):
    def __init__(self, entry, name, kind):
        self._entry = entry
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{kind}"
        self._kind = kind
        self._state = None

    @property
    def unique_id(self):
        return self._attr_unique_id

    @property
    def state(self):
        return self._state

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("zone_name"),
            "manufacturer": "Zenntrix Software",
            "model": "Zone Climate",
        }
    
class ZoneTemperatureSensor(SensorEntity):
    """Representation of a Zone Temperature Sensor."""

    def __init__(self, entry, name, zone_temp_sensor, trv_temp_sensors):
        self._entry = entry
        self._attr_name = name
        self._zone_temp_sensor = zone_temp_sensor
        self._trv_temp_sensors = trv_temp_sensors
        self._state = None
        
    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("zone_name"),
            "manufacturer": "Zenntrix Software",
            "model": "Zone Climate",
        }
    
    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_temperature"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._state if self._state is not None else "unavailable"

    @property
    def unit_of_measurement(self):
        return TEMP_CELSIUS

    async def async_update(self):
        """Fetch new state data for the sensor."""
        if self._zone_temp_sensor:
            self._state = self.hass.states.get(self._zone_temp_sensor).state
        elif self._trv_temp_sensors:
            values = [
                float(self.hass.states.get(sensor).state)
                for sensor in self._trv_temp_sensors
                if self.hass.states.get(sensor) is not None
            ]
            self._state = sum(values) / len(values) if values else None

class ZoneHumiditySensor(SensorEntity):
    """Representation of a Zone Humidity Sensor."""

    def __init__(self, entry, name, zone_humidity_sensor, trv_humidity_sensors):
        self._entry = entry
        self._attr_name = name
        self._zone_humidity_sensor = zone_humidity_sensor
        self._trv_humidity_sensors = trv_humidity_sensors
        self._state = None

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.data.get("zone_name"),
            "manufacturer": "Zenntrix Software",
            "model": "Zone Climate",
        }
    
    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_humidity"

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._state if self._state is not None else "unavailable"

    @property
    def unit_of_measurement(self):
        return "%"

    async def async_update(self):
        """Fetch new state data for the sensor."""
        if self._zone_humidity_sensor:
            self._state = self.hass.states.get(self._zone_humidity_sensor).state
        elif self._trv_humidity_sensors:
            values = [
                float(self.hass.states.get(sensor).state)
                for sensor in self._trv_humidity_sensors
                if self.hass.states.get(sensor) is not None
            ]
            self._state = sum(values) / len(values) if values else None

class ZoneTempSource(SensorEntity):
    def __init__(self, hass, config, uid):
        self.hass = hass
        self._primary = config["zone_temp_sensor"]
        self._backups = [
            s.strip() for s in config.get("trv_temp_sensors", "").split(",") if s.strip()
        ]
        self._attr_name = f"{config['name']} Temp Source"
        self._attr_unique_id = uid
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Fetch new state data for the sensor."""
        state = self.hass.states.get(self._primary)
        if state and state.state not in ("unknown", "unavailable", "0"):
            self._state = "Primary"
        elif self._backups:
            self._state = "Backup"
        else:
            self._state = None


class ZoneHumiditySource(SensorEntity):
    def __init__(self, hass, config, uid):
        self.hass = hass
        self._primary = config.get("zone_humidity_sensor")
        self._backups = [
            s.strip() for s in config.get("trv_humidity_sensors", "").split(",") if s.strip()
        ]
        self._attr_name = f"{config['name']} Humidity Source"
        self._attr_unique_id = uid
        self._state = None

    @property
    def native_value(self):
        return self._state

    async def async_update(self):
        """Fetch new state data for the sensor."""
        state = self.hass.states.get(self._primary)
        if state and state.state not in ("unknown", "unavailable", "0"):
            self._state = "Primary"
        elif self._backups:
            self._state = "Backup"
        else:
            self._state = None
