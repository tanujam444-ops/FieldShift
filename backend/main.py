from datetime import date, timedelta
from typing import Optional
import os
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="FieldShift API", version="1.0.0")

origins = os.getenv("FRONTEND_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[x.strip() for x in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

NASA_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMETERS = "T2M,T2M_MAX,T2M_MIN,PRECTOTCORR,RH2M"

class FieldRequest(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    crop: str = "General"
    field_name: str = "My Field"

def safe_float(value):
    try:
        number = float(value)
        # NASA POWER uses -999 for missing values
        return None if number <= -900 else number
    except (TypeError, ValueError):
        return None

@app.get("/health")
def health():
    return {"status": "ok", "service": "FieldShift API"}

@app.post("/api/field-report")
def field_report(payload: FieldRequest):
    end = date.today() - timedelta(days=2)  # allow near-real-time data processing lag
    start = end - timedelta(days=29)
    params = {
        "parameters": PARAMETERS,
        "community": "AG",
        "longitude": payload.longitude,
        "latitude": payload.latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
        "time-standard": "LST",
    }
    try:
        response = requests.get(NASA_URL, params=params, timeout=35)
        response.raise_for_status()
        raw = response.json()
        values = raw["properties"]["parameter"]
        dates = sorted(values["T2M"].keys())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"NASA POWER request failed: {exc}")

    rows = []
    for day in dates:
        rows.append({
            "date": f"{day[0:4]}-{day[4:6]}-{day[6:8]}",
            "temperature": safe_float(values["T2M"].get(day)),
            "max_temperature": safe_float(values["T2M_MAX"].get(day)),
            "min_temperature": safe_float(values["T2M_MIN"].get(day)),
            "rainfall": safe_float(values["PRECTOTCORR"].get(day)),
            "humidity": safe_float(values["RH2M"].get(day)),
        })

    valid_temp = [r["temperature"] for r in rows if r["temperature"] is not None]
    valid_max = [r["max_temperature"] for r in rows if r["max_temperature"] is not None]
    valid_rain = [r["rainfall"] for r in rows if r["rainfall"] is not None]
    valid_humidity = [r["humidity"] for r in rows if r["humidity"] is not None]

    if not rows or not valid_temp:
        raise HTTPException(status_code=404, detail="NASA POWER returned no usable daily data for this location.")

    avg_temp = round(sum(valid_temp) / len(valid_temp), 1)
    max_temp = round(max(valid_max), 1) if valid_max else None
    rainfall_total = round(sum(valid_rain), 1) if valid_rain else None
    avg_humidity = round(sum(valid_humidity) / len(valid_humidity), 1) if valid_humidity else None

    # Transparent demonstration heuristics, not a validated crop model.
    flags = []
    if avg_temp >= 32:
        flags.append({"level": "high", "title": "High average temperature", "detail": f"30-day mean air temperature is {avg_temp}°C. Inspect crops for heat stress and check local crop guidance."})
    elif avg_temp >= 29:
        flags.append({"level": "moderate", "title": "Warm conditions", "detail": f"30-day mean air temperature is {avg_temp}°C. Monitor sensitive growth stages."})

    if rainfall_total is not None and rainfall_total < 20:
        flags.append({"level": "high", "title": "Low recent rainfall", "detail": f"Accumulated rainfall over the returned period is {rainfall_total} mm. Check root-zone soil moisture before irrigating."})
    elif rainfall_total is not None and rainfall_total < 50:
        flags.append({"level": "moderate", "title": "Limited recent rainfall", "detail": f"Accumulated rainfall over the returned period is {rainfall_total} mm. Review crop water needs and local soil conditions."})

    if avg_humidity is not None and avg_humidity > 85:
        flags.append({"level": "moderate", "title": "High relative humidity", "detail": "High humidity can favour some crop diseases. Scout crops and follow local integrated pest-management advice."})

    if not flags:
        flags.append({"level": "low", "title": "No threshold flags in this screening", "detail": "The simple screening rules did not trigger. Continue routine field scouting; this is not a guarantee of crop health."})

    recommendations = [
        "Verify satellite-scale conditions with an on-farm inspection and, where possible, a root-zone soil-moisture measurement.",
        "Use crop stage, soil type and local agricultural-extension guidance before changing irrigation.",
        "Keep a dated record of rainfall, irrigation and visible crop condition to improve future comparisons."
    ]
    if rainfall_total is not None and rainfall_total < 50:
        recommendations.insert(0, "Review the crop's water requirement and available soil moisture; prioritize irrigation only where field checks show a need.")
    if avg_temp >= 29:
        recommendations.insert(0, "Check for heat stress during the hottest part of the day and consider locally appropriate heat-mitigation practices.")

    return {
        "field": {"name": payload.field_name, "crop": payload.crop, "latitude": payload.latitude, "longitude": payload.longitude},
        "source": "NASA POWER Daily API",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days_requested": 30},
        "resolution_note": "NASA POWER point products represent gridded environmental estimates, not measurements from the exact farm plot.",
        "metrics": {
            "mean_temperature_c": avg_temp,
            "maximum_daily_temperature_c": max_temp,
            "rainfall_total_mm": rainfall_total,
            "mean_relative_humidity_pct": avg_humidity,
        },
        "flags": flags,
        "recommendations": recommendations,
        "daily": rows,
        "method_note": "Risk flags use transparent screening thresholds for hackathon demonstration. They are not calibrated crop-specific forecasts or agronomic prescriptions."
    }

@app.get("/")
def root():
    return {"message": "FieldShift API. See /docs for interactive API documentation."}
