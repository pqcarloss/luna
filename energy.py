import math

SOLAR_CONSTANT_W_M2 = 1361.0

def estimate_power(earth_sun_distance_au: float | None, sun_elevation_deg: float,
                   panel_area_m2: float, efficiency: float, incidence_angle_deg: float,
                   sunlit_fraction: float = 1.0) -> float:
    # First version: nominal solar constant at 1 AU. Pass a measured
    # Earth-Sun distance only after adding a separately validated ephemeris.
    distance = earth_sun_distance_au if earth_sun_distance_au and earth_sun_distance_au > 0 else 1.0
    irradiance = SOLAR_CONSTANT_W_M2 / (distance * distance)
    incidence = max(0.0, math.cos(math.radians(incidence_angle_deg)))
    if sun_elevation_deg <= 0:
        return 0.0
    return irradiance * panel_area_m2 * efficiency * incidence * max(0.0, min(1.0, sunlit_fraction))
