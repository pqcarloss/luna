from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .models import AnalyzeRequest, HorizonRequest
from .horizons import observer_ephemeris
from .terrain import horizon_profile, dem_source
from .energy import estimate_power

app = FastAPI(
    title="LUNAR SIGHT API",
    version="0.1.0",
    description="Lunar south-pole mission planning: ephemerides, terrain and solar power screening."
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SITES = [
    {"id":"shackleton-rim","name":"Shackleton Rim (reference point)","latitude":-89.5,"longitude":0.0,"altitude_km":0.0},
    {"id":"malapert","name":"Malapert Massif (reference point)","latitude":-85.0,"longitude":0.0,"altitude_km":0.0},
    {"id":"de-gerlache","name":"De Gerlache Rim (reference point)","latitude":-88.0,"longitude":240.0,"altitude_km":0.0},
]

@app.get("/api/health")
async def health():
    return {"ok": True, "service": "lunar-sight-api", "dem_configured": bool(dem_source())}

@app.get("/api/sites")
async def sites():
    return SITES

@app.get("/api/nasa/dem-sources")
async def dem_sources():
    return {
        "configured": bool(dem_source()),
        "selected_source": dem_source(),
        "sources": [
            {"name":"NASA PGDA LOLA South Pole, Product 90","url":"https://pgda.gsfc.nasa.gov/products/90","coverage":"South polar regional/global DEM products","format":"Cloud Optimized GeoTIFF"},
            {"name":"NASA PGDA LOLA High Resolution Landing Sites, Product 78","url":"https://pgda.gsfc.nasa.gov/products/78","coverage":"Selected candidate landing regions","format":"5 m/pixel GeoTIFF"}
        ]
    }

@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    output = []
    for site in req.sites:
        try:
            sun, earth = await __import__("asyncio").gather(
                observer_ephemeris(site, "10", req.start_date, req.stop_date, req.step_minutes),
                observer_ephemeris(site, "399", req.start_date, req.stop_date, req.step_minutes)
            )
            earth_by_time = {p["time"]: p for p in earth}
            series = []
            for p in sun:
                e = earth_by_time.get(p["time"])
                if not e:
                    continue
                # Initial idealized horizontal-panel approximation. The user-
                # configured tilt/azimuth is retained for the next model step;
                # this MVP uses solar elevation as incidence for a horizontal panel.
                incidence = 90.0 - p["elevation_deg"]
                power = estimate_power(
                    None, p["elevation_deg"], req.panel.area_m2,
                    req.panel.efficiency, incidence
                )
                series.append({
                    "time": p["time"],
                    "sun_azimuth_deg": p["azimuth_deg"],
                    "sun_elevation_deg": p["elevation_deg"],
                    "earth_azimuth_deg": e["azimuth_deg"],
                    "earth_elevation_deg": e["elevation_deg"],
                    "solar_power_w_ideal": round(power, 2),
                    "sunlit_geometric": p["elevation_deg"] > 0,
                    "earth_visible_geometric": e["elevation_deg"] >= req.panel.minimum_earth_elevation_deg,
                    "simultaneous_window": p["elevation_deg"] > 0 and e["elevation_deg"] >= req.panel.minimum_earth_elevation_deg
                })
            sunlit = sum(1 for p in series if p["sunlit_geometric"])
            earth_visible = sum(1 for p in series if p["earth_visible_geometric"])
            simultaneous = sum(1 for p in series if p["simultaneous_window"])
            output.append({
                "site": site.model_dump(),
                "series": series,
                "summary": {
                    "samples": len(series),
                    "solar_availability_percent": round(100*sunlit/len(series),1) if series else 0,
                    "earth_visibility_percent": round(100*earth_visible/len(series),1) if series else 0,
                    "simultaneous_availability_percent": round(100*simultaneous/len(series),1) if series else 0,
                    "mean_ideal_power_w_when_sampled": round(sum(p["solar_power_w_ideal"] for p in series)/len(series),2) if series else 0
                },
                "source": "NASA/JPL Horizons API",
                "caveats": [
                    "Horizons angular elevation is geometric/apparent ephemeris output, not terrain-corrected local visibility.",
                    "Energy is a first-order idealized estimate; it does not yet model panel attitude, terrain shadow, thermal losses or battery behavior.",
                    "Candidate coordinates are reference points and must be checked against authoritative site definitions."
                ]
            })
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Falha ao consultar Horizons para {site.name}: {exc}")
    return {"results": output, "method": "JPL Horizons observer ephemerides + first-order solar model"}

@app.post("/api/terrain/horizon")
async def terrain_horizon(req: HorizonRequest):
    try:
        return horizon_profile(req.latitude, req.longitude, req.radius_m, req.azimuth_step_deg)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=str(exc))
