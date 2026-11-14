# LUNA — Lunar Unified Navigation Assistant
NASA Space Apps Challenge 2026 · *Lunar Landing Site Navigator* · **MVP v0.1**

Decision-support app to compare lunar south-polar regions and dates using Sun/Earth geometry from **JPL Horizons**.
Candidate regions (Shackleton, de Gerlache, Connecting Ridge) are **preliminary study regions with approximate
coordinates — not certified landing sites.** Verify coordinates against the IAU Gazetteer / LROC before presenting.

## 1. Install (Windows 10/11, PowerShell)
1. Install Python 3.11 or 3.12 from python.org (tick **"Add python.exe to PATH"**).
2. Copy the whole `LUNA` folder to e.g. `C:\Users\<you>\LUNA`. Then:
```powershell
cd C:\Users\<you>\LUNA
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If PowerShell blocks activation: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, then retry.

## 2. Run
```powershell
streamlit run app.py
```
The browser opens at http://localhost:8501. In the sidebar choose **Real: JPL Horizons** (internet needed) or
**SIMULATED demo (offline)**. Real queries are cached in `data\cache` (30 days).

## 3. Test
```powershell
python -m pytest -v                          # unit tests (offline)
python tests\validate_against_horizons.py    # physical-bound check on real Horizons data (internet)
```

## 4. Authentication
| Source | Key needed? | Status |
|---|---|---|
| JPL Horizons API | No | Verified in docs (public) |
| NASA Moon Trek WMTS tiles | No | Verified in docs; layer IDs read from each product's `WMTSCapabilities.xml` |
| LOLA products (PGDA / PDS) | No | Direct file downloads (large GeoTIFFs); not yet integrated |
(`api.nasa.gov` keys are only for *other* NASA APIs; not used here.)

## 5. Conventions
Lat: degrees, south negative · Lon: degrees **east-positive**, [-180,180] · Azimuth: clockwise from North ·
Elevation: above local **geometric** horizon on a smooth Moon (airless, no refraction, no terrain) ·
Time: UT/UTC · Sun optionally by upper limb (+0.2666°) · "Potential comms" = Earth above a chosen mask angle.

## 6. Data labels
*Real* = Horizons output · *Calculated* = indicators computed here from it · *Simulated* = offline crude model (qualitative only; ignores terrain, so its Sun fractions are NOT realistic).

## 7. Known limitations (MVP)
- No terrain horizon masks yet → "terrain obstruction: not assessed" (never shown as 0).
- Map has graticule + sites only; Moon Trek / LOLA raster layers are Phase 5.
- No power or link-budget model; scores are screening aids, not safety or suitability ratings.
- Validation is limited to unit tests + physical-bound checks. Full cross-check vs. LOLA/PGDA illumination & Earth-visibility maps is TODO.
- Horizons CSV column parsing was tested on synthetic text only: **run once with internet and report any error.**

## 8. Demo video (≈2 min)
1) Problem (15 s) 2) Site Explorer (15 s) 3) Tracker with real data (30 s) 4) Comparison + weights (30 s) 5) Human Environment + limitations (20 s). Record with Win+G (Xbox Game Bar), narrate the caveats on screen.

## 9. Project layout
`app.py` · `config.py` · `modules/` (horizons, nasa_api, solar_analysis, earth_visibility, mission_conditions, site_comparison, human_environment, lunar_map, simulated) · `tests/` · `data/cache/`

## 10. Publicar online (aplicação web com URL pública)
1. Crie uma conta em github.com e um repositório **público** chamado `luna`; envie a pasta LUNA (botão *Add file → Upload files*).
2. Entre em share.streamlit.io com a conta do GitHub → *Create app* → escolha o repositório `luna`, branch `main`, arquivo principal `app.py` → *Deploy*.
3. Em ~3 minutos você recebe um endereço `https://<nome>.streamlit.app` para colocar na submissão do Space Apps.
Observações: o app gratuito "dorme" após inatividade (abra-o antes da apresentação); o cache em disco é temporário na nuvem.
