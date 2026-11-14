"""LUNA configuration: sites, endpoints, constants, UI strings (i18n-ready)."""
from pathlib import Path

ROOT = Path(__file__).parent
CACHE_DIR = ROOT / "data" / "cache"
CACHE_TTL_HOURS = 24 * 30   # ephemerides are deterministic; long TTL is fine

# ---- NASA endpoints (verified: no API key required) -------------------------
HORIZONS_API = "https://ssd.jpl.nasa.gov/api/horizons.api"
MOON_TREK_BASE = "https://trek.nasa.gov/tiles/Moon"
# Layer IDs for the south-polar WMTS products MUST be read from the product's
# WMTSCapabilities.xml (see modules/nasa_api.py). Not hard-coded here on purpose.

# ---- Physical constants (units in names) ------------------------------------
MOON_RADIUS_KM = 1737.4          # IAU reference sphere used by LOLA polar maps
SOLAR_DISK_RADIUS_DEG = 0.2666   # mean angular radius of the Sun's disk
EARTH_SEARCH_DEG = 0.0

# ---- Candidate regions: PRELIMINARY STUDY REGIONS, NOT CERTIFIED SITES ------
# APPROXIMATE centre coordinates (selenographic, degrees; lon east-positive).
# !! VERIFY against the IAU Gazetteer / LROC / NASA's published candidate-region
# !! maps before any claim. Near the pole, longitude is poorly defined (all
# !! meridians converge), so small latitude/longitude edits move the point little.
SITES = {
    "Shackleton rim region": {"lat": -89.9, "lon": 0.0, "alt_km": 0.0},
    "de Gerlache rim region": {"lat": -88.5, "lon": -87.1, "alt_km": 0.0},
    "Connecting Ridge region": {"lat": -89.45, "lon": -137.0, "alt_km": 0.0},
}

# ---- Default scoring weights (user-configurable in the UI) ------------------
DEFAULT_WEIGHTS = {"sun": 0.4, "earth": 0.4, "continuity": 0.2}

# ---- UI strings (English default; add a PT dict later) ----------------------
STRINGS = {
    "en": {
        "title": "LUNA — Lunar Unified Navigation Assistant",
        "disclaimer": ("Geometric indicators only. They do not certify a landing site "
                       "as safe, and do not determine actual power or radio-link performance."),
    }
}
LANG = "en"

def t(key: str) -> str:
    """Translate a UI string key (falls back to English)."""
    return STRINGS.get(LANG, STRINGS["en"]).get(key, key)
