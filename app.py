"""LUNA - Lunar Unified Navigation Assistant (Streamlit app).
Run:  streamlit run app.py
"""
from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import config
from config import t
from modules import horizons, simulated, nasa_api
from modules.solar_analysis import validate_site
from modules.lunar_map import south_pole_map
from modules.mission_conditions import compute_indicators
from modules.site_comparison import score_sites
from modules import human_environment as he

st.set_page_config(page_title="LUNA", page_icon="🌙", layout="wide")
st.markdown("""<style>
.stApp{background:radial-gradient(circle at 20% 0%,#10192e 0%,#070b14 60%);}
h1,h2,h3{letter-spacing:.5px} .luna-warn{border-left:4px solid #f5a623;padding:.6rem 1rem;
background:#1a1f2e;border-radius:4px;font-size:.9rem}</style>""", unsafe_allow_html=True)

# ---------------- Sidebar ----------------
st.sidebar.title("🌙 LUNA")
page = st.sidebar.radio("Navigation", ["Site Explorer", "Sun & Earth Tracker", "Mission Conditions",
                                      "Mission Comparison", "Human Environment", "Data & Methodology"])
st.sidebar.subheader("Data mode")
mode = st.sidebar.radio("Source", ["Real: JPL Horizons", "SIMULATED demo (offline)"])
start = st.sidebar.date_input("Start (UTC)", pd.Timestamp("2026-12-01")).isoformat()
days = st.sidebar.slider("Duration (days)", 7, 60, 30)
stop = (pd.Timestamp(start) + pd.Timedelta(days=days)).strftime("%Y-%m-%d")
step = st.sidebar.selectbox("Time step", ["1h", "2h", "30m"], index=0)
comm_mask = st.sidebar.slider("Earth mask angle for 'potential comms' (deg)", 0.0, 15.0, 5.0, 0.5)
limb = st.sidebar.checkbox("Use Sun's upper limb", True)

if "sites" not in st.session_state:
    st.session_state.sites = {k: dict(v) for k, v in config.SITES.items()}
sites = st.session_state.sites

@st.cache_data(show_spinner="Querying data source...", ttl=3600)
def load(mode, lat, lon, alt, start, stop, step):
    if mode.startswith("SIMULATED"):
        return simulated.simulate_az_el(lat, lon, start, stop, step)
    return {"sun": horizons.fetch_az_el("10", lat, lon, start, stop, step, alt),
            "earth": horizons.fetch_az_el("399", lat, lon, start, stop, step, alt)}

def get_series(name):
    s = sites[name]
    try:
        lat, lon = validate_site(s["lat"], s["lon"])
        return load(mode, lat, lon, s.get("alt_km", 0.0), start, stop, step)
    except Exception as e:      # network, API, or validation problems
        st.error(f"Could not load data for {name}: {e}")
        return None

def badge():
    if mode.startswith("SIMULATED"):
        st.warning("SIMULATED data - crude analytic model, NOT real measurements or JPL ephemerides.")
    else:
        st.info("REAL ephemeris data from JPL Horizons (calculated by NASA/JPL, geometric, no terrain).")
def disclaimer():
    st.markdown(f"<div class='luna-warn'>{t('disclaimer')}</div>", unsafe_allow_html=True)

st.title(t("title"))

# ---------------- Pages ----------------
if page == "Site Explorer":
    st.subheader("Lunar Site Explorer")
    st.caption("Candidate regions are PRELIMINARY STUDY REGIONS with approximate coordinates, not certified landing sites.")
    c1, c2 = st.columns([3, 1])
    with c2:
        for name in list(sites):
            sites[name]["lat"] = st.number_input(f"{name} lat", -90.0, 90.0, float(sites[name]["lat"]), 0.01, key=f"lat{name}")
            sites[name]["lon"] = st.number_input(f"{name} lon (E+)", -180.0, 180.0, float(sites[name]["lon"]), 0.01, key=f"lon{name}")
        with st.expander("Add custom location"):
            n = st.text_input("Name"); la = st.number_input("Lat", -90.0, 90.0, -88.0); lo = st.number_input("Lon", -180.0, 180.0, 0.0)
            if st.button("Add") and n:
                sites[n] = {"lat": la, "lon": lo, "alt_km": 0.0}; st.rerun()
    with c1:
        st.plotly_chart(south_pole_map(sites), use_container_width=True)
    ok, msg = nasa_api.check_trek()
    st.caption(f"NASA Moon Trek tile service: {'reachable' if ok else 'unreachable'} ({msg}). "
               "Raster layers (LOLA DEM, illumination) are planned; see README.")
    disclaimer()

elif page == "Sun & Earth Tracker":
    badge()
    name = st.selectbox("Site", list(sites))
    d = get_series(name)
    if d:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=d["sun"]["time"], y=d["sun"]["elevation_deg"], name="Sun elevation", line=dict(color="#ffd166")))
        fig.add_trace(go.Scatter(x=d["earth"]["time"], y=d["earth"]["elevation_deg"], name="Earth elevation", line=dict(color="#4cc9f0")))
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.update_layout(template="plotly_dark", height=450, yaxis_title="Elevation above local geometric horizon (deg)", xaxis_title="UTC")
        st.plotly_chart(fig, use_container_width=True)
        if d["sun"]["azimuth_deg"].notna().any():
            pf = go.Figure()
            for k, c in (("sun", "#ffd166"), ("earth", "#4cc9f0")):
                pf.add_trace(go.Scatterpolar(r=90 - d[k]["elevation_deg"], theta=d[k]["azimuth_deg"], mode="markers",
                                             name=k.title(), marker=dict(size=4, color=c)))
            pf.update_layout(template="plotly_dark", height=450, title="Sky view (centre = zenith, edge = horizon; azimuth clockwise from N)",
                             polar=dict(radialaxis=dict(range=[0, 90]), angularaxis=dict(direction="clockwise", rotation=90)))
            st.plotly_chart(pf, use_container_width=True)
        st.dataframe(pd.concat([d["sun"].assign(body="Sun"), d["earth"].assign(body="Earth")]).head(500))
    disclaimer()

elif page == "Mission Conditions":
    badge()
    name = st.selectbox("Site", list(sites))
    d = get_series(name)
    if d:
        ind = compute_indicators(d["sun"], d["earth"], comm_mask, limb)
        a, b, c, e = st.columns(4)
        a.metric("Sun above horizon", f"{ind['sun_fraction']*100:.1f}%")
        b.metric("Earth above horizon", f"{ind['earth_fraction']*100:.1f}%")
        c.metric(f"Earth > {comm_mask:.1f}° (potential comms)", f"{ind['earth_comm_fraction']*100:.1f}%")
        e.metric("Sun AND Earth", f"{ind['sun_and_earth_fraction']*100:.1f}%")
        st.write(f"Longest Sun-less period: **{ind['longest_dark_h']:.1f} h** | Longest period without Earth: **{ind['longest_no_earth_h']:.1f} h**")
        st.write("Terrain obstruction: **not assessed** (needs LOLA DEM horizon mask; not shown as zero).")
        st.subheader("Potential communication windows"); st.dataframe(ind["comm_windows"])
        st.subheader("Periods without direct Earth visibility"); st.dataframe(ind["no_earth_intervals"])
    disclaimer()

elif page == "Mission Comparison":
    badge()
    st.caption("Explainable screening score; not a safety or suitability ranking.")
    w1, w2, w3 = st.columns(3)
    w = {"sun": w1.slider("Weight: Sun", 0.0, 1.0, config.DEFAULT_WEIGHTS["sun"], 0.05),
         "earth": w2.slider("Weight: Earth comms", 0.0, 1.0, config.DEFAULT_WEIGHTS["earth"], 0.05),
         "continuity": w3.slider("Weight: Sun continuity", 0.0, 1.0, config.DEFAULT_WEIGHTS["continuity"], 0.05)}
    inds, fig = {}, go.Figure()
    for name in sites:
        d = get_series(name)
        if d:
            inds[name] = compute_indicators(d["sun"], d["earth"], comm_mask, limb)
            fig.add_trace(go.Scatter(x=d["sun"]["time"], y=d["sun"]["elevation_deg"], name=f"{name} - Sun"))
    if inds:
        st.dataframe(score_sites(inds, w).style.format(precision=3))
        fig.add_hline(y=0, line_dash="dash"); fig.update_layout(template="plotly_dark", height=420, yaxis_title="Sun elevation (deg)")
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Data quality: Horizons positions are JPL-computed; the Moon is a smooth sphere here; "
                   "no terrain, no link budget, no power model. Missing indicators propagate as NaN, never 0.")
    disclaimer()

elif page == "Human Environment":
    badge()
    st.caption("External light-dark indicators only. NOT astronaut exposure and NOT a medical prediction.")
    name = st.selectbox("Site", list(sites)); target = st.slider("Planned light-period length (h/day)", 8, 20, 16)
    d = get_series(name)
    if d:
        daily = he.daily_light_table(d["sun"], limb)
        fig = go.Figure(go.Bar(x=daily["day"], y=daily["sun_up_h"], name="Sun above horizon (h)"))
        fig.add_hline(y=target, line_dash="dash"); fig.update_layout(template="plotly_dark", height=400, yaxis_title="hours per UTC day")
        st.plotly_chart(fig, use_container_width=True)
        st.json(he.lighting_planning(daily, target))
        st.markdown("**Starting references** (" + he.REFERENCES_NOTE + ")\n" + "\n".join(f"- {r}" for r in he.REFERENCES))
    disclaimer()

else:
    st.subheader("Data sources & methodology")
    st.markdown("""
**JPL Horizons** (real, public API, no key): apparent azimuth/elevation of Sun (10) and Earth (399) from a lunar surface point
(`CENTER=coord@301`, geodetic, east-positive longitude, airless). **NASA Moon Trek** (public WMTS tiles): map layers (planned).
**LRO/LOLA via PGDA/PDS**: DEMs, illumination and Earth-visibility maps (planned: horizon masks, validation).
**Conventions:** lat south-negative; lon east-positive; azimuth clockwise from N; elevation vs. geometric horizon on a smooth Moon;
UT time scale. **Limits:** no terrain, no refraction (airless), geometric visibility != comms or power.
**Data labels:** *real* = JPL Horizons output; *calculated* = indicators derived here; *simulated* = offline demo model.
""")
    ok, msg = horizons.check_connection(); st.write(f"Horizons status: {'OK' if ok else 'unreachable'} ({msg})")
    disclaimer()
