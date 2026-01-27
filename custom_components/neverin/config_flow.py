import requests
import json
import re
import voluptuous as vol
from homeassistant import config_entries
from .const import API_STATIONS, DOMAIN

class NeverinConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Neverin."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            # Dohvatimo ime stanice za title
            station_name = next((s["station"] for s in await self.hass.async_add_executor_job(fetch_stations)
                                 if s["url"] == user_input["station_url"]), "Neverin")
            return self.async_create_entry(title=station_name, data=user_input)

        # Dohvati stanice
        stations = await self.hass.async_add_executor_job(fetch_stations)
        filtered_sorted_stations = sorted(
            (
                s for s in stations
                if "test" not in s["station"].lower()
            ),
            key=lambda s: s["station"].lower()
        )

        station_options = {s["url"]: s["station"] for s in filtered_sorted_stations}

        schema = vol.Schema({
            vol.Required("station_url"): vol.In(list(station_options.keys()))
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors
        )

def fetch_stations():
    """Fetch all stations from Neverin API."""
    try:
        r = requests.get(API_STATIONS, timeout=10)
        r.raise_for_status()
        text = r.text
        json_str = re.sub(r'^_jsonp_\d+\(|\);$', '', text)
        data = json.loads(json_str)
        return data["data"]
    except Exception:
        return []
