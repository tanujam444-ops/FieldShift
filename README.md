# FieldShift — NASA-powered farm adaptation MVP

A hackathon-ready React + FastAPI web application. It fetches real daily climate data from the NASA POWER API for a selected latitude/longitude and produces transparent, rule-based environmental screening insights.

## What is included

- React + Vite dashboard
- Interactive Leaflet map; click to select a location
- FastAPI backend
- NASA POWER Daily API integration for temperature, rainfall and relative humidity
- Temperature and rainfall charts
- Explainable screening flags and adaptation suggestions
- What-if rainfall/temperature sensitivity simulator
- Render backend and Vercel frontend deployment configuration

## Important scientific scope

This MVP currently integrates **NASA POWER** only. It does not yet directly ingest MODIS NDVI or SMAP soil-moisture raster products. Those are sensible next-phase additions, but do not claim that this build displays them.

The backend uses simple demonstration thresholds, not a validated crop-specific model. The simulator changes recent observed values hypothetically; it is not a climate forecast. NASA POWER is gridded data and does not measure the exact farm plot. Verify local conditions and consult local agricultural extension experts.

## Requirements

- Python 3.10+
- Node.js 20+
- Git (for deployment)

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Check `http://localhost:8000/health` and API docs at `http://localhost:8000/docs`.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

On Windows PowerShell use `Copy-Item .env.example .env` instead of `cp`.

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

The initial map pin is centered on Mysuru, Karnataka. Click elsewhere on the map, choose a crop and field name, then select **Analyze this field**.

## API

`POST /api/field-report`

Example body:

```json
{
  "latitude": 12.2958,
  "longitude": 76.6394,
  "crop": "Ragi",
  "field_name": "Demo Field"
}
```

The backend requests the latest 30-day window ending two days before the current date to allow for data processing lag. Returned period dates are included in the response.

## Deploy backend to Render

1. Push this project to GitHub.
2. In Render, create a **New Web Service** and connect the repository.
3. Set the service root directory to `backend`.
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
6. Deploy. Copy the public backend URL.
7. Optional environment variable: `FRONTEND_ORIGINS` = your Vercel frontend URL (comma-separated if multiple).

A `render.yaml` blueprint is also included at the project root.

## Deploy frontend to Vercel

1. Import the GitHub repository into Vercel.
2. Set the project root directory to `frontend`.
3. Add environment variable `VITE_API_URL` = your deployed Render backend URL, without a trailing slash.
4. Build command: `npm run build`
5. Output directory: `dist`
6. Deploy.
7. Add the Vercel URL to Render's `FRONTEND_ORIGINS`, then redeploy the backend if needed.

Vite environment variables are embedded at build time. If you change `VITE_API_URL`, trigger a new frontend deployment.

## Team split (4–6 people)

1. Team lead: challenge alignment, user research, pitch and submission.
2. Frontend: React screens, responsive UI and map.
3. Backend: FastAPI, validation, NASA POWER integration.
4. Data/science: verify parameters, units, missing values and risk thresholds.
5. QA/deployment: test locations, error states, mobile view and hosting.
6. Demo/story: scenario walkthrough, slides, video and documentation.

For a four-person team, combine roles 1+6 and 4+5.

## Suggested next phase

- MODIS MOD13Q1 NDVI: integrate a real vegetation-index product through an Earthdata-supported service/workflow. Product is a 16-day composite at 250 m; account for scale factors, QA flags, cloud effects and temporal lag.
- SMAP: add soil-moisture product data with its true spatial resolution and overpass/temporal characteristics.
- Crop-specific baselines: calibrate thresholds by crop, growth stage, soil and local region with agronomist/extension input.
- Add historical comparisons and uncertainty display before claiming predictive capability.

## Data references

- NASA POWER Daily API: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA POWER API tutorial: https://power.larc.nasa.gov/docs/tutorials/service-data-request/api/
- NASA MODIS MOD13Q1 product: https://ladsweb.modaps.eosdis.nasa.gov/missions-and-measurements/products/MOD13Q1/
- NASA MODIS vegetation indices overview: https://modis.gsfc.nasa.gov/data/dataprod/mod13.php
