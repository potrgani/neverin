from datetime import timedelta, datetime
import logging
import requests
import json
import re

from homeassistant.components.weather import WeatherEntity, Forecast, WeatherEntityFeature
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfPressure,
    UnitOfSpeed,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.components.weather import (
    WeatherEntity,
    Forecast,
    WeatherEntityFeature,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_TEMP,
    ATTR_FORECAST_TEMP_LOW,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_WIND_SPEED,
    ATTR_FORECAST_WIND_BEARING,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_PRESSURE,
    ATTR_FORECAST_PRECIPITATION,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity, UpdateFailed
from .const import API_UPDATE_INTERVAL, DOMAIN
_LOGGER = logging.getLogger(__name__)

# API_UPDATE_INTERVAL = 300  # 5 minuta

# DOMAIN = "neverin"
# ==============================
# SETUP ENTRY
# ==============================

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Neverin weather entity from a config entry."""
    station_url = entry.data["station_url"]

    coordinator = NeverinCoordinator(hass, station_url)
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([NeverinWeather(coordinator, station_url)])


# ==============================
# COORDINATOR
# ==============================
class NeverinCoordinator(DataUpdateCoordinator):
    """Coordinator koji dohvaća podatke sa Neverin API-ja."""

    def __init__(self, hass, station_url):
        self.station_url = station_url
        self.detailed_forecast = []  # spremamo satne podatke

        super().__init__(
            hass,
            _LOGGER,
            name=f"Neverin {station_url}",
            update_interval=timedelta(seconds=API_UPDATE_INTERVAL),
        )

    async def _async_update_data(self):
        """Dohvati podatke sa API-ja."""
        try:
            # -------------------------------
            # 1️⃣ STATION DATA
            # -------------------------------
            station_api = (
                f"https://api.neverin.hr/v2/stations/?station={self.station_url}&callback=_jsonp_4"
            )

            r = await self.hass.async_add_executor_job(
                lambda: requests.get(station_api, timeout=10)
            )
            r.raise_for_status()

            json_str = re.sub(r"^_jsonp_\d+\(|\);$", "", r.text)
            station_data = json.loads(json_str)

            last = station_data.get("data", {}).get("last")
            station = station_data.get("data", {}).get("station", {})

            if not last:
                raise UpdateFailed("No station data")

            lat = station.get("lat")
            lon = station.get("lon")

            # -------------------------------
            # 2️⃣ ECMWF DETAILED FORECAST
            # -------------------------------
            ecmwf_api = (
                f"https://api.neverin.hr/ecmwf/v2/?lat={lat}&lon={lon}&alt=123&tz=Europe/Zagreb&callback=_jsonp_0"
            )

            r = await self.hass.async_add_executor_job(
                lambda: requests.get(ecmwf_api, timeout=10)
            )
            r.raise_for_status()

            json_str = re.sub(r"^_jsonp_\d+\(|\);$", "", r.text)
            data = json.loads(json_str)

            self.detailed_forecast = data.get("data", {}).get("detailed", [])

            # -------------------------------
            # 3️⃣ ICON (trenutni sat)
            # -------------------------------
            now = datetime.now().replace(minute=0, second=0, microsecond=0)
            icon = None
            for item in self.detailed_forecast:
                dt = datetime.fromisoformat(item["datetime"])
                if dt >= now:
                    weather = item.get("weather", {})
                    if weather:
                        period_key = next(iter(weather))
                        icon = weather[period_key].get("icon")
                    break

            return {
                "last": last,
                "icon": icon,
            }

        except Exception as err:
            raise UpdateFailed(err) from err


# ==============================
# WEATHER ENTITY
# ==============================
class NeverinWeather(CoordinatorEntity, WeatherEntity):
    """Neverin Weather entity."""

    _attr_has_entity_name = True
    _attr_supported_features = WeatherEntityFeature.FORECAST_HOURLY
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR

    def __init__(self, coordinator, station_url):
        super().__init__(coordinator)
        self._attr_unique_id = f"neverin_{station_url}"
        self._attr_name = f"Neverin {station_url.replace('-', ' ').title()}"
        # self._attr_device_info = DeviceInfo(
        #     identifiers={(DOMAIN, self._attr_unique_id)},
        #     manufacturer="Neverin",
        #     model="Weather Station",
        # )

    # ----------------------
    # BASIC CURRENT DATA
    # ----------------------
    @property
    def native_temperature(self):
        return self._safe_float(self.coordinator.data["last"].get("temp"))

    @property
    def native_apparent_temperature(self):
        last = self.coordinator.data["last"]
        return self._safe_float(last.get("wchill") or last.get("heat"))

    @property
    def humidity(self):
        return self._safe_float(self.coordinator.data["last"].get("rh"))

    @property
    def native_pressure(self):
        return self._safe_float(self.coordinator.data["last"].get("press"))

    @property
    def native_wind_speed(self):
        # konvertiraj m/s u km/h
        speed = self._safe_float(self.coordinator.data["last"].get("wavg"))
        if speed is not None:
            return round(speed * 3.6, 1)  # zaokruži na 1 decimalu
        return None

    @property
    def wind_gust_speed(self):
        speed = self._safe_float(self.coordinator.data["last"].get("wgust"))
        if speed is not None:
            return round(speed * 3.6, 1)
        return None

    @property
    def wind_bearing(self):
        return self.coordinator.data["last"].get("wdir")

    @property
    def precipitation(self):
        return self._safe_float(self.coordinator.data["last"].get("precip"))

    # ----------------------
    # CONDITION ICON
    # ----------------------
    @property
    def condition(self):
        icon = self.coordinator.data.get("icon")
        if icon is None:
            return None
        return self.map_icon(icon)

    def map_icon(self, icon):
        """Map Neverin icon to HA condition string."""
        if isinstance(icon, str):
            icon_num = int(icon.rstrip("n"))
            is_night = icon.endswith("n")
        else:
            icon_num = int(icon)
            is_night = False

        if icon_num == 1:
            return "clear-night" if is_night else "sunny"
        if icon_num in (2, 3):
            return "partlycloudy"
        if icon_num == 4:
            return "cloudy"
        if icon_num in (11, 12, 13, 14, 15, 16):
            return "rainy"
        if icon_num in (17, 18):
            return "pouring"
        if icon_num in (21, 22, 23):
            return "snowy"
        if icon_num in (26, 27):
            return "hail"
        if icon_num in (31, 32, 33, 34, 35, 36):
            return "snowy-rainy"
        if icon_num in (41, 42):
            return "rainy"
        if icon_num in (43, 44):
            return "pouring"
        if icon_num in (45, 46, 47):
            return "snowy"
        if icon_num in (51, 52, 53):
            return "lightning"
        if icon_num in (54, 55, 56, 57, 58, 59, 61, 62, 63, 64, 65, 66, 67):
            return "lightning-rainy"
        if icon_num in (71, 72, 73, 74, 75, 76, 77, 78):
            return "fog"
        return None

    # ----------------------
    # HOURLY FORECAST
    # ----------------------
    async def async_forecast_hourly(self) -> list[Forecast] | None:
        ha_forecast: list[Forecast] = []

        for item in self.coordinator.detailed_forecast:
            dt_str = item.get("datetime")
            if not dt_str:
                continue
            dt = datetime.fromisoformat(dt_str)

            weather = item.get("weather", {})
            period_key = next(iter(weather), None)
            icon = weather[period_key]["icon"] if period_key else None

            precip = item.get("precip") or {}

            entry: Forecast = {
                ATTR_FORECAST_TIME: dt.isoformat(),
                ATTR_FORECAST_TEMP: self._safe_float(item.get("temp")),
                ATTR_FORECAST_TEMP_LOW: None,
                ATTR_FORECAST_CONDITION: self.map_icon(icon) if icon else None,
                ATTR_FORECAST_WIND_SPEED: round(self._safe_float(item.get("wspeed")) * 3.6, 1) if item.get("wspeed") else None,                ATTR_FORECAST_WIND_BEARING: item.get("wdir"),
                ATTR_FORECAST_HUMIDITY: self._safe_float(item.get("rh")),
                ATTR_FORECAST_PRESSURE: self._safe_float(item.get("press")),
                ATTR_FORECAST_PRECIPITATION: self._safe_float(precip.get("1h")),
            }

            ha_forecast.append({k: v for k, v in entry.items() if v is not None})

        return ha_forecast

    # ----------------------
    # EXTRA ATTRIBUTES
    # ----------------------
    # @property
    # def extra_state_attributes(self):
    #     return {
    #         "icon_raw": self.coordinator.data.get("icon"),
    #         "raw": self.coordinator.data.get("last"),
    #     }

    # ----------------------
    # HELPER: SAFE FLOAT
    # ----------------------
    def _safe_float(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return None
