# Zone Climate (Home Assistant Integration)

A custom Home Assistant integration that creates a **Zone Climate entity**.

It allows you to define a "zone" (e.g. a bedroom or office) with:
- A **primary temperature sensor** and optional backup TRV sensors  
- A **primary humidity sensor** and optional backup TRV humidity sensors  
- A **primary heating control** (climate or switch) and optional backup  

The integration creates a **full Climate entity** (`climate.<zone_name>`) that:
- Uses primary → fallback logic for temp/humidity sensors  
- Controls heating via the chosen climate/switch device(s)  
- Exposes extra sensors for data source/variation if configured  

---

## 🔧 Installation

1. Go to **HACS → Integrations → Custom Repositories**  
2. Add your GitHub repo URL  
   - Category: **Integration**  
3. Install the integration via HACS  
4. Restart Home Assistant  

---

## 🚀 Configuration

1. Go to **Settings → Devices & Services → Add Integration → Zone Climate**  
2. Enter:  
   - Zone Name  
   - Zone Temp Sensor  
   - TRV Temp Sensors (comma separated list, optional)  
   - Zone Humidity Sensor (optional)  
   - TRV Humidity Sensors (comma separated list, optional)  
   - Primary Heating Control (climate or switch)  
   - Backup Heating Control (optional)  

---

## 📦 Example

If you set up “Oakley’s Room”, you’ll get:
- `climate.oakleys_room`
- `sensor.oakleys_room_temp_source`
- `sensor.oakleys_room_humidity_source`

---

## 📝 License

MIT License. See [LICENSE](LICENSE).
