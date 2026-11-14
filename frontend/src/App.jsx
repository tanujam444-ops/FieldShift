
import React, { useEffect, useMemo, useState } from "react";
import axios from "axios";
import { MapContainer, TileLayer, Marker, useMapEvents } from "react-leaflet";
import L from "leaflet";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, BarChart, Bar
} from "recharts";
import {
  Satellite, Sprout, MapPin, CloudRain, ThermometerSun, Droplets,
  Activity, RefreshCw, AlertTriangle, CheckCircle2, ArrowUpRight,
  Gauge, Info
} from "lucide-react";

const API = import.meta.env.VITE_API_URL || "";

const markerIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

function LocationPicker({ position, setPosition }) {
  useMapEvents({
    click(e) {
      setPosition([
        Number(e.latlng.lat.toFixed(4)),
        Number(e.latlng.lng.toFixed(4))
      ]);
    }
  });

  return <Marker position={position} icon={markerIcon} />;
}

const fmt = (v, suffix = "") => v == null ? "—" : `${v}${suffix}`;

function Metric({ icon: Icon, label, value, unit, note }) {
  return (
    <div className="metric">
      <div className="metric-top">
        <span>{label}</span>
        <Icon size={18} />
      </div>
      <div className="metric-value">
        {value}<small>{unit}</small>
      </div>
      <div className="metric-note">{note}</div>
    </div>
  );
}

function App() {
  const [position, setPosition] = useState([12.2958, 76.6394]);
  const [crop, setCrop] = useState("Maize");
  const [fieldName, setFieldName] = useState("Demo Field");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [rainChange, setRainChange] = useState(0);
  const [tempChange, setTempChange] = useState(0);

  async function loadReport() {
    setLoading(true);
    setError("");

    try {
      const { data } = await axios.post(`${API}/api/field-report`, {
        latitude: position[0],
        longitude: position[1],
        crop,
        field_name: fieldName
      });

      setReport(data);
    } catch (e) {
      setError(
        e.response?.data?.detail ||
        "Could not load NASA data. Please try again."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadReport();
  }, []);

  const risk = useMemo(() => {
    if (!report) return { label: "Awaiting data", tone: "neutral" };

    const high = report.flags.filter(x => x.level === "high").length;
    const moderate = report.flags.filter(x => x.level === "moderate").length;

    return high
      ? { label: "Elevated screening risk", tone: "high" }
      : moderate
      ? { label: "Moderate screening risk", tone: "moderate" }
      : { label: "Low screening flags", tone: "low" };
  }, [report]);

  const scenario = useMemo(() => {
    if (!report) return null;

    const rain = report.metrics.rainfall_total_mm;
    const temp = report.metrics.mean_temperature_c;

    const adjustedRain =
      rain == null ? null : Math.max(0, rain * (1 + rainChange / 100));

    const adjustedTemp =
      temp == null ? null : temp + tempChange;

    let score = 0;

    if (adjustedRain != null && adjustedRain < 20) score += 2;
    else if (adjustedRain != null && adjustedRain < 50) score += 1;

    if (adjustedTemp != null && adjustedTemp >= 32) score += 2;
    else if (adjustedTemp != null && adjustedTemp >= 29) score += 1;

    return {
      adjustedRain,
      adjustedTemp,
      score,
      label: score >= 3
        ? "Higher screening concern"
        : score === 2
        ? "Moderate screening concern"
        : "Fewer screening flags"
    };
  }, [report, rainChange, tempChange]);

  const chartData = report?.daily.slice(-21).map(d => ({
    day: d.date.slice(5),
    temp: d.temperature,
    rain: d.rainfall
  })) || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Sprout size={23} /></div>
          <div>
            <b>FieldShift</b>
            <span>EARTH DATA • FARM DECISIONS</span>
          </div>
        </div>

        <div className="side-label">WORKSPACE</div>
        <a className="nav active"><Gauge size={17} /> Overview</a>
        <a className="nav">
          <Satellite size={17} /> Satellite intelligence
          <span className="soon">NEXT</span>
        </a>
        <a className="nav"><Activity size={17} /> Adaptation simulator</a>

        <div className="sidebar-bottom">
          <div className="nasa-mark">
            <Satellite size={19} />
            <div>
              <b>Powered by NASA data</b>
              <span>NASA POWER Daily API</span>
            </div>
          </div>
          <p>Environmental screening support, not a substitute for local agronomic advice.</p>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <div className="eyebrow">FARM INTELLIGENCE / OVERVIEW</div>
            <h1>Good morning, grower.</h1>
            <p>Understand your field. Adapt with confidence.</p>
          </div>
          <div className="live-pill"><span /> NASA DATA CONNECTION</div>
        </header>

        <section className="hero">
          <div className="hero-copy">
            <div className="hero-kicker">
              <Satellite size={15} /> EARTH OBSERVATION FOR RESILIENT FARMING
            </div>
            <h2>Make your next<br /><em>farm decision</em> smarter.</h2>
            <p>
              FieldShift turns NASA environmental data into clear field insights
              and practical adaptation steps.
            </p>
            <button
              className="hero-btn"
              onClick={() => document.getElementById("field-setup").scrollIntoView({ behavior: "smooth" })}
            >
              Explore your field <ArrowUpRight size={16} />
            </button>
          </div>

          <div className="hero-art">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />
            <div className="earth"><div className="earth-land" /></div>
            <div className="satellite-float"><Satellite size={27} /></div>
            <div className="art-caption">
              OBSERVE <span>·</span> UNDERSTAND <span>·</span> ADAPT
            </div>
          </div>
        </section>

        <section className="section-head" id="field-setup">
          <div>
            <div className="eyebrow">01 / FIELD CONFIGURATION</div>
            <h3>Your field workspace</h3>
          </div>
          <button className="refresh-btn" onClick={loadReport} disabled={loading}>
            <RefreshCw size={15} className={loading ? "spin" : ""} />
            {loading ? "Updating" : "Refresh NASA data"}
          </button>
        </section>

        <section className="setup-grid">
          <div className="panel field-form">
            <label>FIELD NAME</label>
            <input
              value={fieldName}
              onChange={e => setFieldName(e.target.value)}
              placeholder="e.g. North Farm"
            />

            <label>CROP TYPE</label>
            <select value={crop} onChange={e => setCrop(e.target.value)}>
              {["Maize", "Rice", "Wheat", "Ragi", "Sugarcane", "Cotton", "Groundnut", "General"].map(c => (
                <option key={c}>{c}</option>
              ))}
            </select>

            <div className="coords">
              <MapPin size={15} />
              <span>{position[0]}, {position[1]}</span>
            </div>

            <button className="primary-btn" onClick={loadReport} disabled={loading}>
              {loading ? "Fetching observations..." : "Analyze this field"}
              <ArrowUpRight size={16} />
            </button>
            <p className="helper">Select any point on the map to change your field location.</p>
          </div>

          <div className="panel map-panel">
            <div className="panel-title">
              <div>
                <b>Field location</b>
                <span>Click map to move your pin</span>
              </div>
              <span className="map-tag"><MapPin size={13} /> SELECT LOCATION</span>
            </div>

            <MapContainer
              center={position}
              zoom={7}
              scrollWheelZoom={true}
              className="map"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <LocationPicker position={position} setPosition={setPosition} />
            </MapContainer>
          </div>
        </section>

        {error && (
          <div className="error-box">
            <AlertTriangle size={18} />
            <div>
              <b>Data connection issue</b>
              <span>{error}</span>
            </div>
          </div>
        )}

        <section className="section-head">
          <div>
            <div className="eyebrow">02 / ENVIRONMENTAL CONDITIONS</div>
            <h3>What is happening around your field?</h3>
          </div>
          {report && (
            <span className="period">
              Period: {report.period.start} – {report.period.end}
            </span>
          )}
        </section>

        {!report && !error && (
          <div className="panel loading-panel">
            Connecting to NASA POWER and preparing your field report…
          </div>
        )}

        {report && (
          <>
            <div className="metric-grid">
              <Metric
                icon={ThermometerSun}
                label="MEAN TEMPERATURE"
                value={fmt(report.metrics.mean_temperature_c)}
                unit="°C"
                note="30-day daily mean"
              />
              <Metric
                icon={CloudRain}
                label="ACCUMULATED RAINFALL"
                value={fmt(report.metrics.rainfall_total_mm)}
                unit="mm"
                note="Across returned daily records"
              />
              <Metric
                icon={Droplets}
                label="MEAN HUMIDITY"
                value={fmt(report.metrics.mean_relative_humidity_pct)}
                unit="%"
                note="Relative humidity"
              />
              <Metric
                icon={Activity}
                label="MAX DAILY TEMPERATURE"
                value={fmt(report.metrics.maximum_daily_temperature_c)}
                unit="°C"
                note="Highest daily maximum"
              />
            </div>

            <div className="content-grid">
              <div className="panel chart-panel">
                <div className="panel-title">
                  <div>
                    <b>Temperature trend</b>
                    <span>Daily mean air temperature · °C</span>
                  </div>
                  <span className="chart-label">NASA POWER</span>
                </div>
                <div className="chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="tempFill" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#77ad78" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#77ad78" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8eee8" />
                      <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#87948a" }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#87948a" }} />
                      <Tooltip />
                      <Area
                        type="monotone"
                        dataKey="temp"
                        name="Temperature"
                        stroke="#4c8c62"
                        strokeWidth={2.5}
                        fill="url(#tempFill)"
                        connectNulls
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="panel chart-panel">
                <div className="panel-title">
                  <div>
                    <b>Daily rainfall</b>
                    <span>Precipitation · mm/day</span>
                  </div>
                  <span className="chart-label">NASA POWER</span>
                </div>
                <div className="chart">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e8eee8" />
                      <XAxis dataKey="day" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#87948a" }} />
                      <YAxis tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: "#87948a" }} />
                      <Tooltip />
                      <Bar dataKey="rain" name="Rainfall" fill="#77a9bd" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            <section className="section-head">
              <div>
                <div className="eyebrow">03 / DECISION SUPPORT</div>
                <h3>Field risk assessment</h3>
              </div>
              <span className={`risk-pill ${risk.tone}`}>{risk.label}</span>
            </section>

            <div className="insight-grid">
              <div className="panel risk-panel">
                <div className="risk-top">
                  <div className="risk-symbol"><Activity size={21} /></div>
                  <div>
                    <b>{risk.label}</b>
                    <span>Based on transparent screening rules</span>
                  </div>
                </div>

                {report.flags.map((f, i) => (
                  <div className="flag" key={i}>
                    <span className={`flag-dot ${f.level}`} />
                    <div>
                      <b>{f.title}</b>
                      <p>{f.detail}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="panel advisor-panel">
                <div className="advisor-heading">
                  <div className="advisor-icon"><Sprout size={20} /></div>
                  <div>
                    <b>FieldShift adaptation advisor</b>
                    <span>Suggested next steps</span>
                  </div>
                </div>

                {report.recommendations.map((r, i) => (
                  <div className="recommendation" key={i}>
                    <CheckCircle2 size={17} />
                    <p>{r}</p>
                  </div>
                ))}
              </div>
            </div>

            <section className="section-head">
              <div>
                <div className="eyebrow">04 / EXPLORE POSSIBILITIES</div>
                <h3>Farm adaptation simulator</h3>
                <p className="section-sub">
                  Explore hypothetical changes to recent rainfall and temperature.
                  This is a simple sensitivity exercise, not a climate forecast.
                </p>
              </div>
            </section>

            <div className="panel simulator">
              <div className="sim-controls">
                <div className="slider-row">
                  <div>
                    <label>RAINFALL CHANGE</label>
                    <b>{rainChange > 0 ? "+" : ""}{rainChange}%</b>
                  </div>
                  <input
                    type="range"
                    min="-60"
                    max="60"
                    step="5"
                    value={rainChange}
                    onChange={e => setRainChange(Number(e.target.value))}
                  />
                  <div className="slider-hints">
                    <span>60% less</span>
                    <span>60% more</span>
                  </div>
                </div>

                <div className="slider-row">
                  <div>
                    <label>TEMPERATURE CHANGE</label>
                    <b>{tempChange > 0 ? "+" : ""}{tempChange}°C</b>
                  </div>
                  <input
                    type="range"
                    min="-3"
                    max="5"
                    step="0.5"
                    value={tempChange}
                    onChange={e => setTempChange(Number(e.target.value))}
                  />
                  <div className="slider-hints">
                    <span>3°C cooler</span>
                    <span>5°C warmer</span>
                  </div>
                </div>
              </div>

              <div className="scenario-result">
                <div className="scenario-icon"><Gauge size={23} /></div>
                <div>
                  <span>SCENARIO SCREENING RESULT</span>
                  <b>{scenario?.label}</b>
                  <p>
                    Adjusted rainfall: {scenario?.adjustedRain?.toFixed(1) ?? "—"} mm
                    · Adjusted mean temperature: {scenario?.adjustedTemp?.toFixed(1) ?? "—"}°C
                  </p>
                </div>
                <button
                  className="reset-btn"
                  onClick={() => {
                    setRainChange(0);
                    setTempChange(0);
                  }}
                >
                  Reset
                </button>
              </div>
            </div>
          </>
        )}

        <footer>
          <div className="footer-brand"><Sprout size={17} /> FieldShift</div>
          <p>Environmental decision support for climate-resilient agriculture.</p>
          <div className="source-note">
            <Info size={14} />
            Data source: <a href="https://power.larc.nasa.gov/" target="_blank" rel="noreferrer">NASA POWER</a>.
            {" "}{report?.method_note}
          </div>
          <p className="disclaimer">
            NASA POWER data are gridded estimates and may not represent conditions
            at an individual field. Verify conditions locally and consult
            agricultural extension experts before making farm-management decisions.
          </p>
        </footer>
      </main>
    </div>
  );
}

export default App;
