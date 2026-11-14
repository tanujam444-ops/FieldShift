# 🌍 FieldShift: Adapting Farms with NASA Data
**Official NASA International Space Apps Challenge Decision-Support System**

> **"NASA DATA IS THE CORE OF FIELDSHIFT."**  
> FieldShift is not a generic weather dashboard or an ordinary farming website. It is an Earth-observation-powered adaptive crop rotation decision-support system that combines real NASA satellite observations, NASA environmental datasets, local farmer soil-test reports, crop physiological characteristics, and farmer priorities.

---

## 🚀 Key Features

1. **🛰️ NASA Earth Observation Intelligence Dashboard**
   - **NASA POWER API (Live Integration):** Live automated retrieval of daily agroclimatology parameters (`T2M`, `T2M_MAX`, `T2M_MIN`, `PRECTOTCORR`, `RH2M`, `ALLSKY_SFC_SW_DWN`). Calculates Growing Degree Days (GDD), dry spell frequencies, frost days, heat stress thresholds, and solar radiation budgets.
   - **NASA GPM IMERG:** Rainfall variability analysis, extreme storm percentiles (p75, p90, p99), and explicit scientific comparison between GPM radar/microwave sensing (0.1°) and NASA POWER reanalysis (0.5° x 0.625°).
   - **NASA SMAP:** Volumetric soil moisture regimes, distinguishing surface skin moisture (0-5 cm) from root-zone moisture (0-100 cm). Transparent Earthdata Login (NSIDC DAAC) authentication reporting without fabricated values.
   - **NASA MODIS:** 250m 16-day NDVI and EVI vegetation greenness dynamics, quality flags (cloud, aerosol, snow), and phenological length.
   - **NASA ECOSTRESS:** Thermal infrared Land Surface Temperature (LST) and Evaporative Stress Index (ESI = AET / PET) to detect crop water stress before visible wilting.

2. **🔄 Adaptive Multi-Season Crop Rotation Engine**
   - Combines NASA climate evidence with farmer soil tests (pH, texture, NPK, Soil Organic Matter %).
   - Evaluates crop water requirements ($ET_c$) against NASA POWER historical rainfall.
   - Generates and compares 4 multi-season rotation plans:
     - **Climate-Adaptive & Drought-Resilient Strategy**
     - **Soil Health & Bio-Regenerative Nitrogen-Fixing Strategy**
     - **High-Yield Economic Market Strategy**
     - **Water-Conserving Low-Footprint Strategy**
   - Side-by-side comparison matrix: Water demand, net nitrogen balance (kg N/ha), soil organic carbon change (SOM Δ), climate resilience score, and economic index.
   - Complete explainability cards detailing NASA evidence, soil test evidence, crop characteristics, agronomic justification, and operational trade-offs.

3. **🌾 Farmer Registration & SQLite Database**
   - Persistent farm profiles, field boundaries, and laboratory soil test records stored in `data/fieldshift.db`.
   - Seeded with representative real-world farms across major agro-ecological zones (Iowa Midwest Corn Belt, Punjab Indo-Gangetic Plain, Kenya Rift Valley, California Central Valley, Cerrado Brazil).
   - Allows farmers to register new fields, update soil test records, and save evaluated rotation plans.

4. **🛡️ Scientific Integrity & Anti-Fabrication Principles**
   - **No Fake Data:** If a NASA product requires authentication or is unreachable, FieldShift transparently displays its official status rather than substituting invented values.
   - **Macro vs In-Situ Distinction:** Satellites measure atmospheric moisture, cloud dynamics, and surface radiometric fluxes; they do *not* measure laboratory chemical soil pH or available phosphorus.
   - **Spatial Scale Transparency:** Explicitly communicates the difference between satellite grid cell resolutions (70m to 50km) and individual farm furrows.

---

## 📂 Architecture & Directory Structure

```
c:\fieldshift\
├── app.py                            # Interactive Streamlit Decision-Support Application
├── requirements.txt                  # Python dependencies
├── README.md                         # Documentation and architecture guide
├── data\
│   └── fieldshift.db                 # Persistent SQLite database for farms and plans
├── cache\                            # Disk cache for NASA requests (JSON/TTL)
│   ├── nasa_power\
│   ├── nasa_gpm\
│   ├── nasa_smap\
│   ├── nasa_modis\
│   └── nasa_ecostress\
├── modules\
│   ├── __init__.py
│   ├── database.py                   # SQLite farm registration and plan persistence
│   ├── nasa_power.py                 # NASA POWER live API client & climate statistics
│   ├── nasa_gpm.py                   # NASA GPM IMERG precipitation & variability
│   ├── nasa_smap.py                  # NASA SMAP soil moisture & CMR catalog
│   ├── nasa_modis.py                 # NASA MODIS NDVI/EVI & quality flags
│   ├── nasa_ecostress.py             # NASA ECOSTRESS LST skin temp & ESI stress index
│   ├── nasa_data_manager.py          # Central NASA coordinator & spatial scaling
│   ├── soil_crop_db.py               # Soil physics & crop physiological database
│   └── crop_engine.py                # Multi-season adaptive crop rotation engine
└── tests\
    ├── test_nasa_power.py            # Independent NASA POWER HTTP verification
    └── test_fieldshift_pipeline.py   # End-to-end integration test suite
```

---

## 🧪 Testing NASA POWER Independently

Run the standalone verification script to test live connectivity directly against `https://power.larc.nasa.gov`:

```bash
python tests/test_nasa_power.py
```

Expected output:
```
=================================================================
 NASA POWER API INDEPENDENT VERIFICATION
 Official Endpoint: https://power.larc.nasa.gov/api/temporal/daily/point
 Test Coordinates: Latitude 42.0308, Longitude -93.6319
=================================================================

[1/3] Dispatching HTTP GET request to NASA POWER API...
[2/3] Response received in 3.00 seconds. HTTP Status Code: 200
[3/3] Validating returned parameters and observation structure:
  [PASS] T2M                : Date=20230601, Sample Value=21.34
  [PASS] T2M_MAX            : Date=20230601, Sample Value=24.11
  [PASS] T2M_MIN            : Date=20230601, Sample Value=19.18
  [PASS] PRECTOTCORR        : Date=20230601, Sample Value=15.26
  [PASS] RH2M               : Date=20230601, Sample Value=92.17
  [PASS] ALLSKY_SFC_SW_DWN  : Date=20230601, Sample Value=13.51

>>> NASA POWER API STATUS: 100% OPERATIONAL & VERIFIED LIVE <<<
```

---

## 🏃 Running the FieldShift Application

Launch the Streamlit interface:

```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501`.

---

## 📡 NASA Integration Status Summary

| Integration | Priority | Official Source | Status | Authentication |
| :--- | :---: | :--- | :---: | :--- |
| **NASA POWER** | **P1** | `power.larc.nasa.gov` | 🟢 **Live Operational** | Public API (No credentials needed) |
| **NASA GPM** | **P2** | `gpm.nasa.gov` | 🟡 **Catalog Online** | CMR Public / Earthdata for NetCDF |
| **NASA SMAP** | **P3** | `smap.jpl.nasa.gov` | 🔒 **Auth Required** | NASA Earthdata Login (NSIDC DAAC) |
| **NASA MODIS** | **P4** | `modis.gsfc.nasa.gov` | 🟡 **Catalog Online** | CMR Public / LP DAAC for raw HDF |
| **NASA ECOSTRESS** | **P5** | `ecostress.jpl.nasa.gov` | 🟡 **Catalog Online** | CMR Public / LP DAAC for raw H5 |
