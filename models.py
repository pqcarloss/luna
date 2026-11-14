from datetime import date
from pydantic import BaseModel, Field, model_validator

class Site(BaseModel):
    id: str
    name: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=0, le=360, description="Longitude east, degrees")
    altitude_km: float = Field(default=0.0, ge=-10, le=100)

class PanelConfig(BaseModel):
    area_m2: float = Field(default=4.0, gt=0, le=10000)
    efficiency: float = Field(default=0.30, gt=0, le=1)
    tilt_deg: float = Field(default=0.0, ge=0, le=180)
    azimuth_deg: float = Field(default=180.0, ge=0, le=360)
    minimum_earth_elevation_deg: float = Field(default=10.0, ge=-10, le=90)

class AnalyzeRequest(BaseModel):
    sites: list[Site] = Field(min_length=1, max_length=4)
    start_date: date
    stop_date: date
    step_minutes: int = Field(default=60, ge=10, le=1440)
    panel: PanelConfig = PanelConfig()

    @model_validator(mode="after")
    def validate_dates(self):
        if self.stop_date <= self.start_date:
            raise ValueError("stop_date deve ser posterior a start_date")
        if (self.stop_date - self.start_date).days > 31:
            raise ValueError("A janela máxima desta versão é de 31 dias")
        return self

class HorizonRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=0, le=360)
    radius_m: int = Field(default=2000, ge=100, le=20000)
    azimuth_step_deg: int = Field(default=5, ge=1, le=30)
