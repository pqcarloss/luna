import os
from pydantic import BaseModel

class Settings(BaseModel):
    horizons_api_url: str = os.getenv(
        "HORIZONS_API_URL", "https://ssd.jpl.nasa.gov/api/horizons.api"
    )
    dem_path: str | None = os.getenv("LUNAR_DEM_PATH") or None
    dem_url: str | None = os.getenv("LUNAR_DEM_URL") or None
    cors_origins: list[str] = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173"
    ).split(",")

settings = Settings()
