# LUNAR SIGHT

Plataforma experimental de apoio ao planejamento de missões no polo sul lunar.

## Arquitetura
- `backend/`: FastAPI, JPL Horizons, análise de horizonte topográfico via DEM, energia solar.
- `frontend/`: React + TypeScript + Vite, painel de missão e gráficos.
- Fonte de efemérides: NASA/JPL Horizons API.
- Fonte topográfica: NASA GSFC PGDA LOLA South Pole DEM (Cloud Optimized GeoTIFF).

> **Limitação científica importante:** a geometria JPL Horizons é calculada para um observador na superfície lunar com coordenadas geodésicas e referencial do Horizons. A análise de horizonte do DEM é uma segunda etapa. A primeira versão integra um DEM COG configurável; não baixa gigabytes automaticamente. O resultado de sombra topográfica depende de DEM e de transformação de coordenadas compatíveis. Não use esta versão para decisões reais de missão sem validação independente.

## Requisitos
- Python 3.11+
- Node.js 20+
- GDAL/Rasterio compatível com o seu sistema (instalado pelo pip pode funcionar no Windows; em caso de erro, use Conda/OSGeo4W).

## Executar

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
API: http://localhost:8000/docs

### Frontend
Em outro terminal:
```bash
cd frontend
npm install
npm run dev
```
Aplicação: http://localhost:5173

## Dados LOLA
O backend aceita `LUNAR_DEM_PATH` apontando para um GeoTIFF local, ou `LUNAR_DEM_URL` apontando para um Cloud Optimized GeoTIFF com suporte a HTTP Range. Para baixar produtos, consulte:
- NASA PGDA Product 90: https://pgda.gsfc.nasa.gov/products/90
- NASA PGDA Product 78 (locais de pouso específicos): https://pgda.gsfc.nasa.gov/products/78

Confira no README do produto o CRS, datum/referencial e unidades antes de usar. Os produtos podem estar em projeção polar estereográfica lunar; não assuma que latitude/longitude pode ser usada diretamente como coordenada raster.

## Endpoints
- `GET /api/health`
- `GET /api/sites`
- `POST /api/analyze` — consulta Horizons para Sol e Terra, estima potência solar idealizada e identifica janelas geométricas.
- `POST /api/terrain/horizon` — calcula perfil de horizonte a partir de DEM local/COG, quando disponível.
- `GET /api/nasa/dem-sources` — fontes LOLA recomendadas.

## Modelo de energia
A potência estimada usa:
`P = irradiance * panel_area * efficiency * max(0, cos(incidence_angle)) * sunlit_fraction`
A irradiância nesta versão usa 1361 W/m² como constante solar nominal a 1 AU; a variação da distância Sol-Lua ainda não está aplicada. O modelo não inclui degradação, temperatura da célula, poeira, perdas de cabos, conversor, bateria, refletância do solo ou dinâmica detalhada de atitude.

## Referenciais e precisão
- Horizons é consultado com `CENTER=coord@301`, `COORD_TYPE=GEODETIC`, `SITE_COORD=longitude,latitude,altitude_km`, `EPHEM_TYPE=OBSERVER`, `QUANTITIES=4,20`.
- Azimute é medido a partir do norte, no sentido horário; elevação é relativa ao plano horizontal local.
- A posição da Terra acima de 0° indica apenas visibilidade geométrica sem obstáculos; a análise de terreno e o orçamento do enlace são necessários para confirmar comunicação.
- O DEM pode ter limitações de cobertura, resolução e incerteza. O produto LOLA PGDA 90 oferece DEMs polares COG e documentação.
