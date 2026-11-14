import math
import rasterio
from rasterio.windows import Window
from .config import settings

LUNAR_RADIUS_M = 1_737_400.0


def dem_source():
    return settings.dem_path or settings.dem_url


def south_polar_stereographic(latitude_deg: float, longitude_east_deg: float):
    """Approximate PGDA south-polar stereographic coordinates (MOON_ME sphere).

    Product metadata must be checked for the exact longitude convention,
    projection parameters and reference frame before using a DEM operationally.
    """
    phi = math.radians(latitude_deg)
    lam = math.radians(longitude_east_deg)
    rho = 2.0 * LUNAR_RADIUS_M * math.tan(math.radians(45.0) + phi / 2.0)
    x = rho * math.sin(lam)
    y = rho * math.cos(lam)
    return x, y


def horizon_profile(latitude: float, longitude: float, radius_m: int, step_deg: int):
    source = dem_source()
    if not source:
        raise RuntimeError(
            "DEM não configurado. Defina LUNAR_DEM_PATH ou LUNAR_DEM_URL "
            "com um GeoTIFF LOLA compatível."
        )
    x0, y0 = south_polar_stereographic(latitude, longitude)
    with rasterio.open(source) as ds:
        if ds.crs is None:
            raise ValueError("O DEM não possui CRS definido.")
        # The projection math above yields lunar polar-stereographic metres.
        # Validate that the opened raster bounds contain this point; do not
        # silently transform through terrestrial EPSG:4326.
        row0, col0 = ds.index(x0, y0)
        if not (0 <= row0 < ds.height and 0 <= col0 < ds.width):
            raise ValueError(
                "Coordenada projetada fora do DEM. Verifique longitude, "
                "convenção do produto e parâmetros de projeção LOLA."
            )
        base = ds.read(1, window=Window(col0, row0, 1, 1), masked=True)[0, 0]
        if getattr(base, "mask", False):
            raise ValueError("O pixel do local de observação não possui elevação válida.")
        base_m = float(base)
        px = abs(ds.transform.a)
        py = abs(ds.transform.e)
        sample_step = max(10, int(min(px, py) * 2))
        result = []
        for az in range(0, 360, step_deg):
            best_angle = -90.0
            angle = math.radians(az)
            for distance in range(sample_step, radius_m + 1, sample_step):
                x = x0 + distance * math.sin(angle)
                y = y0 + distance * math.cos(angle)
                row, col = ds.index(x, y)
                if row < 0 or col < 0 or row >= ds.height or col >= ds.width:
                    continue
                value = ds.read(1, window=Window(col, row, 1, 1), masked=True)[0, 0]
                if getattr(value, "mask", False):
                    continue
                elevation_angle = math.degrees(math.atan2(float(value) - base_m, distance))
                best_angle = max(best_angle, elevation_angle)
            result.append({"azimuth_deg": az, "horizon_elevation_deg": round(best_angle, 3)})
        return {
            "profile": result,
            "dem": source,
            "crs": str(ds.crs),
            "resolution_m_approx": round(min(px, py), 2),
            "observer_elevation_m": base_m,
            "warning": (
                "Perfil de horizonte de triagem. Confirme parâmetros de projeção, "
                "datum/referencial MOON_ME, escala vertical e cobertura do DEM LOLA. "
                "Amostragem radial não substitui validação geodésica/mission-grade."
            ),
        }
