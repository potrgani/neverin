from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .weather import NeverinCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Neverin integration from a config entry."""

    station_url = entry.data.get("station_url")

    # Provjeri odmah prije forwarda
    coordinator = NeverinCoordinator(hass, station_url)
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as e:
        raise ConfigEntryNotReady(f"Cannot fetch data for station {station_url}: {e}")

    # Sve ok, forwardamo weather platformu
    await hass.config_entries.async_forward_entry_setups(entry, ["weather"])

    return True
