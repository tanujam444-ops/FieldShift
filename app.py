"""
FieldShift: Adapting Farms with NASA Data
Official NASA Space Apps Challenge Decision-Support System

Integrates official NASA Earth observations (NASA POWER, GPM, SMAP, MODIS, ECOSTRESS)
with farmer local soil tests to deliver explainable, adaptive crop rotation strategies.
"""

import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Ensure root directory is on Python path
sys.path.insert(0, os.path.dirname(__file__))

# Enable native Windows SSL certificates
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

from modules.database import (
    init_db,
    get_all_farms,
    get_farm_by_id,
    add_farm,
    update_farm,
    save_rotation_plan,
    get_farm_plans
)
from modules.nasa_data_manager import NASADataManager
from modules.crop_engine import CropRotationEngine
from modules.soil_crop_db import SOIL_TEXTURES, CROP_DATABASE

# Page configuration
st.set_page_config(
    page_title="FieldShift | NASA Earth Observation Crop Rotation",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
init_db()

# Custom Styling for NASA Theme
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #0b1a30 0%, #0d3b66 50%, #1d2d44 100%);
        padding: 24px;
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 25px;
        border: 1px solid #1e3a5f;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
    }
    .nasa-badge {
        background-color: #0b3d91;
        color: #ffffff;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.85rem;
        letter-spacing: 0.05em;
        display: inline-block;
        margin-bottom: 8px;
    }
    .stat-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .stat-val {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0b3d91;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748b;
        font-weight: 500;
    }
    .transparency-box {
        background-color: #eff6ff;
        border-left: 5px solid #3b82f6;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 15px 0;
        font-size: 0.9rem;
    }
    .warning-box {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 6px;
        margin: 15px 0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# Sidebar - Navigation & Farm Selection
with st.sidebar:
    st.image("https://www.nasa.gov/wp-content/themes/nasa/assets/images/nasa-logo.svg", width=120)
    st.title("FieldShift")
    st.caption("NASA Space Apps Challenge 2024/2025")
    st.markdown("**Adapting Farms with NASA Data**")
    st.divider()

    farms = get_all_farms()
    farm_names = [f"{f['farm_name']} ({f['region']}, {f['country']})" for f in farms]
    
    selected_idx = st.selectbox(
        "📍 Select Active Farm",
        range(len(farms)),
        format_func=lambda i: farm_names[i],
        index=0 if farms else None
    )
    
    selected_farm = farms[selected_idx] if farms else None

    st.divider()
    
    # Earthdata credentials
    st.markdown("### 🔐 NASA Earthdata Access")
    earthdata_token = st.text_input(
        "Earthdata Bearer Token (Optional)",
        type="password",
        value=st.session_state.get("earthdata_token", ""),
        help="Required for direct Level-3 SMAP, GPM NetCDF, and MODIS HDF downloads from NSIDC/GES DISC/LP DAAC."
    )
    if earthdata_token:
        st.session_state["earthdata_token"] = earthdata_token

    st.caption("Free registration: [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov)")


# Main Header Banner
st.markdown("""
<div class="main-header">
    <span class="nasa-badge">NASA SPACE APPS CHALLENGE</span>
    <h1 style="margin: 0; font-size: 2.2rem; font-weight: 800;">FieldShift: Adapting Farms with NASA Data</h1>
    <p style="margin: 6px 0 0 0; opacity: 0.9; font-size: 1.05rem;">
        NASA Earth-observation-powered adaptive crop rotation decision-support system.
        Bridging satellite environmental observations and local farmer soil chemistry.
    </p>
</div>
""", unsafe_allow_html=True)


# Tabs Navigation
tab_intelligence, tab_rotation, tab_profile, tab_db, tab_docs = st.tabs([
    "🛰️ NASA Earth Observation Intelligence",
    "🔄 Adaptive Crop Rotation Engine",
    "🌾 Farm Profile & Soil Registration",
    "📊 Database & Farm Records",
    "📖 Scientific Methodology & Data Disclosures"
])


# ==============================================================================
# TAB 1: NASA EARTH OBSERVATION INTELLIGENCE
# ==============================================================================
with tab_intelligence:
    if not selected_farm:
        st.warning("Please select or register a farm to view NASA Earth Observation data.")
    else:
        st.subheader(f"NASA Earth Observation Intelligence: {selected_farm['farm_name']}")
        st.caption(f"Coordinates: Latitude {selected_farm['latitude']:.4f}° N/S, Longitude {selected_farm['longitude']:.4f}° E/W | Region: {selected_farm['region']}, {selected_farm['country']}")

        # Query controls
        col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([2, 2, 1])
        with col_ctrl1:
            date_range_choice = st.selectbox(
                "Historical Baseline Observation Period",
                ["2023 Full Year (Recommended Climate Baseline)", "2022 Full Year", "2021 Full Year", "Custom Range"],
                index=0
            )
        
        if date_range_choice == "2023 Full Year (Recommended Climate Baseline)":
            start_d, end_d = "20230101", "20231231"
        elif date_range_choice == "2022 Full Year":
            start_d, end_d = "20220101", "20221231"
        elif date_range_choice == "2021 Full Year":
            start_d, end_d = "20210101", "20211231"
        else:
            with col_ctrl2:
                c_start = st.date_input("Start Date", datetime(2023, 1, 1))
                c_end = st.date_input("End Date", datetime(2023, 12, 31))
                start_d = c_start.strftime("%Y%m%d")
                end_d = c_end.strftime("%Y%m%d")

        with col_ctrl3:
            st.write("")
            st.write("")
            refresh_btn = st.button("🔄 Refresh NASA Data", use_container_width=True)

        # NASA Data Retrieval
        with st.spinner("Connecting to official NASA Earth Observation APIs (NASA POWER & NASA CMR)..."):
            nasa_mgr = NASADataManager(earthdata_token=st.session_state.get("earthdata_token"))
            nasa_data = nasa_mgr.get_full_environmental_intelligence(
                lat=selected_farm["latitude"],
                lon=selected_farm["longitude"],
                start_date=start_d,
                end_date=end_d,
                force_refresh=refresh_btn
            )

        # 1. Multi-Sensor Integration Status Table
        st.markdown("### 📡 NASA Sensor Integration Matrix")
        status_df = pd.DataFrame(nasa_data["sources_status"])
        
        display_status = status_df[["source_name", "product_id", "product_type", "spatial_resolution", "status_badge", "latest_observation"]]
        display_status.columns = ["NASA Source", "Product ID", "Environmental Discipline", "Spatial Resolution", "Connection Status", "Latest Available Observation"]
        
        st.dataframe(display_status, hide_index=True, use_container_width=True)

        # Spatial Transparency Notice
        st.markdown(f"""
        <div class="transparency-box">
            <b>🔬 Spatial Scale Disclosure:</b><br/>
            {nasa_data['spatial_transparency_notice'].replace(chr(10), '<br/>')}
        </div>
        """, unsafe_allow_html=True)

        # 2. NASA POWER Live Climatology
        power_data = nasa_data.get("nasa_power", {})
        if power_data.get("status") == "success":
            summary = power_data["summary"]
            st.markdown("### 🌤️ Live NASA POWER Agroclimatology Records")
            st.caption(f"Source: {power_data['source']} | Product: {power_data['product']} | Total Valid Daily Records: {summary['observation_count']}")

            # KPI Metrics Row
            kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
            kpi1.metric("Annualized Precip", f"{summary['annualized_precipitation_mm']:.1f} mm", help="Corrected precipitation total scaled to annual cycle (PRECTOTCORR)")
            kpi2.metric("Mean Air Temp", f"{summary['mean_temperature_c']:.1f} °C", help="Daily 2-meter air temperature (T2M)")
            kpi3.metric("Max Dry Spell", f"{summary['max_consecutive_dry_days']} days", help="Longest consecutive period with daily rainfall < 1.0mm")
            kpi4.metric("Heat Stress Days", f"{summary['heat_stress_days_count']} days", help="Days with T2M_MAX >= 35°C (thermal crop stress threshold)")
            kpi5.metric("Frost Days", f"{summary['frost_days_count']} days", help="Days with T2M_MIN <= 0°C (killing frost risk)")
            kpi6.metric("Annual GDD (Base 10°C)", f"{summary['annualized_gdd_base10']:.0f}°C-days", help="Accumulated Growing Degree Days above 10°C")

            records = power_data.get("records", [])
            if records:
                rec_df = pd.DataFrame(records)
                rec_df["date"] = pd.to_datetime(rec_df["date"])

                # Chart 1: Temperature & Frost/Heat thresholds
                st.markdown("#### 1. Air Temperature Regimes & Thermal Risk (T2M, T2M_MAX, T2M_MIN)")
                fig_temp = go.Figure()
                fig_temp.add_trace(go.Scatter(
                    x=rec_df["date"], y=rec_df["T2M_MAX"],
                    mode="lines", name="Max Temperature (T2M_MAX)",
                    line=dict(color="#e63946", width=1.2)
                ))
                fig_temp.add_trace(go.Scatter(
                    x=rec_df["date"], y=rec_df["T2M"],
                    mode="lines", name="Mean Temperature (T2M)",
                    line=dict(color="#f4a261", width=1.8)
                ))
                fig_temp.add_trace(go.Scatter(
                    x=rec_df["date"], y=rec_df["T2M_MIN"],
                    mode="lines", name="Min Temperature (T2M_MIN)",
                    line=dict(color="#457b9d", width=1.2),
                    fill="tonexty", fillcolor="rgba(69, 123, 157, 0.1)"
                ))
                fig_temp.add_hline(y=35, line_dash="dash", line_color="red", annotation_text="Heat Stress Threshold (35°C)")
                fig_temp.add_hline(y=0, line_dash="dash", line_color="blue", annotation_text="Freezing Threshold (0°C)")
                fig_temp.update_layout(
                    height=360,
                    margin=dict(l=20, r=20, t=30, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis_title="Temperature (°C)",
                    xaxis_title="Observation Date"
                )
                st.plotly_chart(fig_temp, use_container_width=True)

                # Chart 2: Daily Precipitation & Dry Spells
                st.markdown("#### 2. Corrected Daily Precipitation Patterns (PRECTOTCORR)")
                fig_precip = go.Figure()
                fig_precip.add_trace(go.Bar(
                    x=rec_df["date"], y=rec_df["PRECTOTCORR"],
                    name="Daily Precipitation (mm)",
                    marker_color="#1d3557"
                ))
                fig_precip.add_hline(y=25, line_dash="dot", line_color="orange", annotation_text="Heavy Rainfall (25 mm/day)")
                fig_precip.add_hline(y=1, line_dash="solid", line_color="#a8dadc", annotation_text="Dry Day Threshold (1 mm)")
                fig_precip.update_layout(
                    height=300,
                    margin=dict(l=20, r=20, t=30, b=20),
                    yaxis_title="Precipitation (mm/day)",
                    xaxis_title="Observation Date"
                )
                st.plotly_chart(fig_precip, use_container_width=True)

                # Chart 3 & 4: Solar Radiation & Relative Humidity
                col_c3, col_c4 = st.columns(2)
                with col_c3:
                    st.markdown("#### 3. Solar Radiation (ALLSKY_SFC_SW_DWN)")
                    fig_sol = px.line(
                        rec_df, x="date", y="ALLSKY_SFC_SW_DWN",
                        color_discrete_sequence=["#e76f51"],
                        labels={"ALLSKY_SFC_SW_DWN": "Irradiance (MJ/m²/day)", "date": "Date"}
                    )
                    fig_sol.update_layout(height=260, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_sol, use_container_width=True)

                with col_c4:
                    st.markdown("#### 4. Relative Humidity at 2m (RH2M)")
                    fig_rh = px.line(
                        rec_df, x="date", y="RH2M",
                        color_discrete_sequence=["#2a9d8f"],
                        labels={"RH2M": "Relative Humidity (%)", "date": "Date"}
                    )
                    fig_rh.update_layout(height=260, margin=dict(l=20, r=20, t=20, b=20))
                    st.plotly_chart(fig_rh, use_container_width=True)

        else:
            st.error(f"NASA POWER API Error: {power_data.get('error_message', 'Unable to retrieve live data.')}")
            st.info("FieldShift will continue using fallback regional agro-climatic baselines for crop rotation modeling.")

        st.divider()

        # 3. NASA GPM Precipitation Analytics
        st.markdown("### 🌧️ NASA GPM Precipitation Dynamics & Methodological Comparison")
        gpm_data = nasa_data.get("nasa_gpm", {})
        
        col_gpm1, col_gpm2 = st.columns([1, 1])
        with col_gpm1:
            st.markdown("**Rainfall Distribution & Variability (GPM IMERG Framework)**")
            r_dist = gpm_data.get("rainfall_distribution_analysis", {})
            if r_dist:
                st.write(f"• **Rainfall Variability Rating**: `{r_dist.get('rainfall_variability_rating', 'N/A')}` (Coefficient of Variation: {r_dist.get('coefficient_of_variation_pct', 0):.1f}%)")
                st.write(f"• **Median Daily Rainfall**: {r_dist.get('median_daily_mm', 0):.2f} mm")
                st.write(f"• **75th Percentile Rainfall**: {r_dist.get('p75_daily_mm', 0):.2f} mm")
                st.write(f"• **90th Percentile Rainfall**: {r_dist.get('p90_daily_mm', 0):.2f} mm")
                st.write(f"• **99th Percentile Extreme Rainfall Event**: {r_dist.get('p99_extreme_rain_mm', 0):.2f} mm/day")
                st.write(f"• **Dry Days Count (<1 mm)**: {r_dist.get('dry_spells_less_than_1mm_days', 0)} days")
                st.write(f"• **Torrential Storm Days (>25 mm)**: {r_dist.get('torrential_rain_gt_25mm_days', 0)} days")
            else:
                st.info("Statistical distribution calculated when NASA rainfall records are queried.")

        with col_gpm2:
            st.markdown("**Methodological Difference: NASA GPM vs NASA POWER**")
            st.markdown("""
            | Dimension | NASA GPM IMERG | NASA POWER (PRECTOTCORR) |
            | :--- | :--- | :--- |
            | **Primary Sensor** | Active Dual-frequency Radar (DPR) & Passive Microwave (GMI) | MERRA-2 Atmospheric Global Data Assimilation |
            | **Spatial Resolution** | **0.1° (~10 km)** | **0.5° x 0.625° (~50 km x 60 km)** |
            | **Primary Utility** | Captures localized convective cloudbursts and high-intensity storm cells | Long-term continuous water balance & energy reanalysis |
            | **Farmer Takeaway** | Informs erosion protection, ditch capacity, and seed wash risk | Informs seasonal crop water budgets and drought frequency |
            """)

        st.divider()

        # 4. NASA SMAP, MODIS & ECOSTRESS Deep Dive
        col_smap, col_modis, col_eco = st.columns(3)
        
        with col_smap:
            st.markdown("#### 💧 NASA SMAP Soil Moisture")
            smap_info = nasa_data.get("nasa_smap", {})
            st.caption(f"Product: `{smap_info.get('product', 'SPL3SMP_E')}` | Resolution: `{smap_info.get('spatial_resolution', '9 km')}`")
            st.markdown(f"**Authentication Status**: `{smap_info.get('authentication_status', 'AUTH_REQUIRED')}`")
            st.info(smap_info.get("status_message", "Earthdata authentication required for HDF5 raster retrieval."))
            with st.expander("🔬 Soil Moisture Physics & Depth"):
                sp = smap_info.get("scientific_profile", {})
                st.write(f"• **Surface (0-5 cm)**: {sp.get('surface_soil_moisture_depth', 'N/A')}")
                st.write(f"• **Root-Zone (0-100 cm)**: {sp.get('root_zone_moisture_depth', 'N/A')}")
                st.write(f"• **Aggregation Notice**: {sp.get('spatial_aggregation_warning', 'N/A')}")

        with col_modis:
            st.markdown("#### 🌿 NASA MODIS Vegetation Indices")
            modis_info = nasa_data.get("nasa_modis", {})
            st.caption(f"Product: `{modis_info.get('product', 'MOD13Q1')}` | Resolution: `{modis_info.get('spatial_resolution', '250 m')}`")
            st.markdown(f"**Catalog Status**: `{modis_info.get('data_status', 'CMR_ONLINE')}`")
            st.info("Verified active collection in NASA CMR. Direct raster tile downloading managed via LP DAAC.")
            with st.expander("🔬 NDVI & EVI Scientific Caveats"):
                st.write("**Indices Explained:**")
                st.write("• **NDVI**: (NIR - Red) / (NIR + Red) - Chlorophyll absorption.")
                st.write("• **EVI**: Decoupled from aerosol scattering and bright soil backgrounds.")
                st.write("**Integrity Constraints:**")
                st.write("• NDVI measures canopy greenness; it does NOT measure soil chemical fertility.")
                st.write("• NDVI alone cannot distinguish between botanical crop species.")

        with col_eco:
            st.markdown("#### 🌡️ NASA ECOSTRESS Thermal & ET")
            eco_info = nasa_data.get("nasa_ecostress", {})
            st.caption(f"Product: `{eco_info.get('product', 'ECO2LSTE')}` | Resolution: `{eco_info.get('spatial_resolution', '70 m')}`")
            st.markdown(f"**Platform**: International Space Station (ISS)")
            st.info("Thermal infrared observations from precessing low-Earth orbit. Catalog indexed in CMR.")
            with st.expander("🔬 LST vs Air Temp & ESI"):
                st.write("**Skin Temp vs Air Temp:**")
                st.write("• LST is the direct radiometric temperature of leaves and soil surface, whereas T2M is 2m ambient air temperature.")
                st.write("• Stressed canopies with closed stomata can reach 5-10°C hotter than surrounding air.")
                st.write("**Evaporative Stress Index (ESI):**")
                st.write("• ESI = Actual ET / Potential ET. Signals water deficit weeks before leaf wilting.")


# ==============================================================================
# TAB 2: ADAPTIVE CROP ROTATION ENGINE
# ==============================================================================
with tab_rotation:
    if not selected_farm:
        st.warning("Please select a farm to evaluate crop rotation strategies.")
    else:
        st.subheader(f"Adaptive Crop Rotation Engine: {selected_farm['farm_name']}")
        st.markdown("""
        FieldShift combines **NASA Earth observation climate evidence** with **local soil laboratory tests**
        and **crop physiological water/thermal requirements** to construct 4 distinct multi-season rotation plans.
        """)

        # Execute Engine
        engine = CropRotationEngine()
        power_summary = nasa_data.get("nasa_power", {}).get("summary", {}) if "nasa_data" in locals() and nasa_data.get("nasa_power") else {
            "annualized_precipitation_mm": 650.0,
            "mean_temperature_c": 12.0,
            "heat_stress_days_count": 8,
            "frost_days_count": 45,
            "max_consecutive_dry_days": 16,
            "annualized_gdd_base10": 1350.0
        }
        gpm_res = nasa_data.get("nasa_gpm") if "nasa_data" in locals() else None

        plans = engine.evaluate_rotation_plans(
            farm_profile=selected_farm,
            nasa_power_summary=power_summary,
            nasa_gpm_data=gpm_res
        )

        # Plan Comparison Cards & Metrics
        st.markdown("### 🏆 Multi-Strategy Comparative Matrix")
        
        comp_cols = st.columns(4)
        for idx, p in enumerate(plans):
            with comp_cols[idx]:
                m = p["metrics"]
                st.markdown(f"""
                <div style="border-top: 5px solid {p['theme_color']}; background: #ffffff; border-radius: 8px; padding: 14px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); height: 100%;">
                    <h4 style="margin: 0 0 6px 0; color: {p['theme_color']}; font-size: 1.05rem;">{p['strategy_title']}</h4>
                    <p style="font-size: 0.8rem; color: #475569; min-height: 48px;">{p['strategy_focus']}</p>
                    <hr style="margin: 8px 0;"/>
                    <div style="font-size: 0.85rem;">
                        <b>💧 Water Demand:</b> {m['total_water_demand_mm']} mm<br/>
                        <b>🌧️ 2-Yr NASA Precip:</b> {m['two_year_precip_mm']} mm<br/>
                        <b>⚖️ Water Stress Ratio:</b> <span style="color: {'red' if m['water_stress_ratio'] > 1.0 else 'green'};"><b>{m['water_stress_ratio']}</b></span><br/>
                        <b>🌱 Net N Balance:</b> <span style="color: {'green' if m['net_nitrogen_balance_kg_ha'] >= 0 else '#b91c1c'};"><b>{m['net_nitrogen_balance_kg_ha']:+d} kg N/ha</b></span><br/>
                        <b>📈 Projected SOM Δ:</b> <b>+{m['projected_som_delta_pct']:.2f}%</b><br/>
                        <b>🛡️ Climate Resilience:</b> <b>{m['climate_resilience_score']} / 100</b><br/>
                        <b>🌾 Soil Health Score:</b> <b>{m['soil_health_score']} / 100</b><br/>
                        <b>💰 Economic Yield Index:</b> <b>{m['economic_yield_index']} / 100</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Detailed Season Timeline & Explainability
        selected_plan_id = st.selectbox(
            "🔍 Inspect Detailed Strategy & Evidence Breakdown",
            [p["strategy_id"] for p in plans],
            format_func=lambda pid: next(p["strategy_title"] for p in plans if p["strategy_id"] == pid)
        )
        plan_detail = next(p for p in plans if p["strategy_id"] == selected_plan_id)

        st.markdown(f"### 🗓️ 4-Season Sequence: {plan_detail['strategy_title']}")
        
        # Sequence Timeline Display
        season_cols = st.columns(4)
        for s in plan_detail["seasons"]:
            with season_cols[s["season_number"] - 1]:
                st.markdown(f"""
                <div style="background: #f1f5f9; border-radius: 8px; padding: 12px; border: 1px solid #cbd5e1;">
                    <span style="font-size: 0.75rem; background: #0b3d91; color: white; padding: 2px 6px; border-radius: 4px;">{s['season_label']}</span>
                    <h4 style="margin: 8px 0 2px 0; color: #0f172a;">{s['crop_name']}</h4>
                    <p style="font-size: 0.75rem; color: #64748b; margin: 0 0 6px 0;"><i>{s['scientific_name']}</i> ({s['family']})</p>
                    <div style="font-size: 0.8rem; color: #334155;">
                        • <b>Duration:</b> {s['duration_days']} days<br/>
                        • <b>Water Req:</b> {s['water_req_mm']} mm<br/>
                        • <b>Root Depth:</b> {s['rooting_depth']}<br/>
                        • <b>N Impact:</b> <b>{s['n_balance_kg_ha']:+d} kg N/ha</b><br/>
                        • <b>Value:</b> {s['economic_value']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        # Deep-dive explainability tabs
        exp_col1, exp_col2 = st.columns(2)
        with exp_col1:
            st.markdown("#### 🛰️ NASA Earth Observation Evidence")
            for item in plan_detail["explanations"]["nasa_evidence"]:
                st.markdown(f"• {item}")
            
            st.markdown("#### 🧪 Local Soil Test Evidence Used")
            for item in plan_detail["explanations"]["soil_evidence"]:
                st.markdown(f"• {item}")

        with exp_col2:
            st.markdown("#### 🌿 Crop Physiological Compatibility Rationale")
            for item in plan_detail["explanations"]["crop_characteristics"]:
                st.markdown(f"• {item}")

            st.markdown("#### ⚠️ Risks, Trade-offs & Missing Data")
            st.markdown("**Missing / Unmeasured Factors:**")
            for item in plan_detail["explanations"]["missing_information"]:
                st.markdown(f"• {item}")
            st.markdown("**Operational Risks:**")
            for item in plan_detail["explanations"]["risks_and_tradeoffs"]:
                st.markdown(f"• {item}")

        # Scientific Integrity & Caveats Alert
        st.markdown("""
        <div class="warning-box">
            <b>🛡️ FieldShift Scientific Integrity & Caveats:</b><br/>
            • <b>NASA Satellites Observe Environmental Baselines:</b> Satellites measure atmospheric moisture, cloud cover, and surface radiation. They do <u>not</u> directly measure laboratory soil chemical pH, available phosphorus (Bray/Olsen), or potassium.<br/>
            • <b>Vegetation Indices Do Not Equal Soil Health:</b> Satellite greenness (NDVI/EVI) indicates active canopy chlorophyll; it cannot verify disease absence or soil nutrient fertility.<br/>
            • <b>Historical Baselines vs Weather Forecasts:</b> NASA POWER climatologies represent multi-year historical MERRA-2 assimilation baselines, not guaranteed deterministic day-by-day future weather forecasts.
        </div>
        """, unsafe_allow_html=True)

        # Save Plan to Database
        if st.button("💾 Save This Rotation Plan to Farm Database", key=f"save_plan_{plan_detail['strategy_id']}"):
            plan_id = save_rotation_plan(
                farm_id=selected_farm["id"],
                plan_name=f"{selected_farm['farm_name']} - {plan_detail['strategy_title']}",
                plan_strategy=plan_detail["strategy_id"],
                nasa_evidence="\n".join(plan_detail["explanations"]["nasa_evidence"]),
                soil_evidence="\n".join(plan_detail["explanations"]["soil_evidence"]),
                plan_dict=plan_detail
            )
            st.success(f"Successfully saved rotation plan #{plan_id} to database!")


# ==============================================================================
# TAB 3: FARM PROFILE & SOIL REGISTRATION
# ==============================================================================
with tab_profile:
    st.subheader("🌾 Farm Profile & Soil Chemistry Management")
    st.markdown("Manage farm boundaries, coordinates, and local laboratory soil test reports.")

    prof_mode = st.radio("Action", ["Edit Current Farm Profile", "Register New Farm"], horizontal=True)

    if prof_mode == "Edit Current Farm Profile" and selected_farm:
        with st.form("edit_farm_form"):
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                e_name = st.text_input("Farm Name", value=selected_farm["farm_name"])
                e_farmer = st.text_input("Farmer / Operator Name", value=selected_farm["farmer_name"])
                e_country = st.text_input("Country", value=selected_farm["country"])
                e_region = st.text_input("Region / State", value=selected_farm["region"])
                e_area = st.number_input("Field Area (Hectares)", min_value=0.1, max_value=10000.0, value=float(selected_farm["area_hectares"]), step=0.5)
            
            with c_f2:
                e_lat = st.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=float(selected_farm["latitude"]), format="%.4f")
                e_lon = st.number_input("Longitude (°)", min_value=-180.0, max_value=180.0, value=float(selected_farm["longitude"]), format="%.4f")
                e_irr = st.selectbox("Irrigation System", ["Rainfed", "Drip / Micro-irrigation", "Canal / Borewell", "Sprinkler / Center Pivot"], index=["Rainfed", "Drip / Micro-irrigation", "Canal / Borewell", "Sprinkler / Center Pivot"].index(selected_farm["irrigation_type"]) if selected_farm["irrigation_type"] in ["Rainfed", "Drip / Micro-irrigation", "Canal / Borewell", "Sprinkler / Center Pivot"] else 0)
                e_priority = st.selectbox("Farmer Strategic Priority", ["Climate Resilience", "Soil Health & Regeneration", "High Economic Yield", "Water Conservation"], index=["Climate Resilience", "Soil Health & Regeneration", "High Economic Yield", "Water Conservation"].index(selected_farm["primary_priority"]) if selected_farm["primary_priority"] in ["Climate Resilience", "Soil Health & Regeneration", "High Economic Yield", "Water Conservation"] else 0)
                e_crop = st.selectbox("Current Standing Crop", list(CROP_DATABASE.keys()) + ["Fallow"], index=(list(CROP_DATABASE.keys()) + ["Fallow"]).index(selected_farm["current_crop"]) if selected_farm["current_crop"] in (list(CROP_DATABASE.keys()) + ["Fallow"]) else 0)

            st.markdown("#### 🧪 Local Soil Test Results (Laboratory Input)")
            s_c1, s_c2, s_c3, s_c4, s_c5 = st.columns(5)
            with s_c1:
                e_tex = st.selectbox("Soil Texture", list(SOIL_TEXTURES.keys()), index=list(SOIL_TEXTURES.keys()).index(selected_farm["soil_texture"]) if selected_farm["soil_texture"] in SOIL_TEXTURES else 0)
            with s_c2:
                e_ph = st.slider("Soil pH", min_value=3.5, max_value=9.5, value=float(selected_farm["soil_ph"]), step=0.1)
            with s_c3:
                e_n = st.selectbox("Nitrogen (N) Rating", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(selected_farm["soil_n_status"]))
            with s_c4:
                e_p = st.selectbox("Phosphorus (P) Rating", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(selected_farm["soil_p_status"]))
            with s_c5:
                e_som = st.slider("Organic Matter (SOM %)", min_value=0.2, max_value=10.0, value=float(selected_farm["soil_organic_matter_pct"]), step=0.1)

            submit_edit = st.form_submit_button("💾 Update Farm Profile", use_container_width=True)
            if submit_edit:
                updated_data = {
                    "farm_name": e_name,
                    "farmer_name": e_farmer,
                    "country": e_country,
                    "region": e_region,
                    "latitude": e_lat,
                    "longitude": e_lon,
                    "area_hectares": e_area,
                    "soil_texture": e_tex,
                    "soil_ph": e_ph,
                    "soil_n_status": e_n,
                    "soil_p_status": e_p,
                    "soil_organic_matter_pct": e_som,
                    "irrigation_type": e_irr,
                    "primary_priority": e_priority,
                    "current_crop": e_crop
                }
                update_farm(selected_farm["id"], updated_data)
                st.success("Farm profile and soil test updated successfully! Please refresh.")
                st.rerun()

    elif prof_mode == "Register New Farm":
        with st.form("new_farm_form"):
            c_n1, c_n2 = st.columns(2)
            with c_n1:
                n_name = st.text_input("Farm Name", placeholder="e.g. Cedar Creek Farm")
                n_farmer = st.text_input("Farmer Name", placeholder="e.g. Samuel Ortiz")
                n_country = st.text_input("Country", placeholder="e.g. Spain")
                n_region = st.text_input("Region / Province", placeholder="e.g. Andalusia")
                n_area = st.number_input("Field Area (Hectares)", min_value=0.1, max_value=10000.0, value=10.0, step=0.5)
            
            with c_n2:
                n_lat = st.number_input("Latitude (°)", min_value=-90.0, max_value=90.0, value=37.3891, format="%.4f")
                n_lon = st.number_input("Longitude (°)", min_value=-180.0, max_value=180.0, value=-5.9845, format="%.4f")
                n_irr = st.selectbox("Irrigation System", ["Rainfed", "Drip / Micro-irrigation", "Canal / Borewell", "Sprinkler / Center Pivot"])
                n_priority = st.selectbox("Farmer Strategic Priority", ["Climate Resilience", "Soil Health & Regeneration", "High Economic Yield", "Water Conservation"])
                n_crop = st.selectbox("Current Standing Crop", list(CROP_DATABASE.keys()) + ["Fallow"])

            st.markdown("#### 🧪 Local Soil Test Results")
            sn_c1, sn_c2, sn_c3, sn_c4, sn_c5 = st.columns(5)
            with sn_c1:
                n_tex = st.selectbox("Soil Texture", list(SOIL_TEXTURES.keys()), index=2)
            with sn_c2:
                n_ph = st.slider("Soil pH", min_value=3.5, max_value=9.5, value=6.8, step=0.1)
            with sn_c3:
                n_n = st.selectbox("Nitrogen (N) Rating", ["Low", "Medium", "High"], index=1)
            with sn_c4:
                n_p = st.selectbox("Phosphorus (P) Rating", ["Low", "Medium", "High"], index=1)
            with sn_c5:
                n_som = st.slider("Organic Matter (SOM %)", min_value=0.2, max_value=10.0, value=2.2, step=0.1)

            submit_new = st.form_submit_button("➕ Register Farm into SQLite Database", use_container_width=True)
            if submit_new:
                if not n_name or not n_farmer:
                    st.error("Please provide both Farm Name and Farmer Name.")
                else:
                    new_id = add_farm({
                        "farm_name": n_name,
                        "farmer_name": n_farmer,
                        "country": n_country,
                        "region": n_region,
                        "latitude": n_lat,
                        "longitude": n_lon,
                        "area_hectares": n_area,
                        "soil_texture": n_tex,
                        "soil_ph": n_ph,
                        "soil_n_status": n_n,
                        "soil_p_status": n_p,
                        "soil_k_status": "Medium",
                        "soil_organic_matter_pct": n_som,
                        "irrigation_type": n_irr,
                        "primary_priority": n_priority,
                        "current_crop": n_crop
                    })
                    st.success(f"Farm registered successfully with ID #{new_id}! Refreshing...")
                    st.rerun()


# ==============================================================================
# TAB 4: DATABASE & FARM RECORDS
# ==============================================================================
with tab_db:
    st.subheader("📊 SQLite Database & Historical Rotation Records")
    st.markdown(f"Database File: `{os.path.abspath('data/fieldshift.db')}`")

    tab_db_farms, tab_db_plans = st.tabs(["🌾 All Registered Farms", "💾 Saved Rotation Plans"])

    with tab_db_farms:
        all_f = get_all_farms()
        if all_f:
            df_farms = pd.DataFrame(all_f)
            st.dataframe(df_farms[[
                "id", "farm_name", "farmer_name", "country", "region",
                "latitude", "longitude", "area_hectares", "soil_texture",
                "soil_ph", "soil_n_status", "soil_organic_matter_pct",
                "irrigation_type", "primary_priority", "current_crop"
            ]], use_container_width=True, hide_index=True)
        else:
            st.info("No farms registered in database.")

    with tab_db_plans:
        if selected_farm:
            plans_history = get_farm_plans(selected_farm["id"])
            if plans_history:
                st.write(f"Saved plans for **{selected_farm['farm_name']}**: {len(plans_history)}")
                for hp in plans_history:
                    with st.expander(f"Plan #{hp['id']} - {hp['plan_name']} (Saved: {hp['created_at'][:19]})"):
                        st.markdown(f"**Strategy Type**: `{hp['plan_strategy']}`")
                        st.markdown("**NASA Evidence Influencing Plan:**")
                        st.write(hp["nasa_evidence_summary"])
                        st.markdown("**Soil Test Evidence Used:**")
                        st.write(hp["soil_evidence_summary"])
                        st.json(hp["plan_data"].get("sequence", []))
            else:
                st.info(f"No saved rotation plans yet for {selected_farm['farm_name']}. You can generate and save plans in the Crop Rotation tab.")


# ==============================================================================
# TAB 5: SCIENTIFIC METHODOLOGY & DISCLOSURES
# ==============================================================================
with tab_docs:
    st.subheader("📖 FieldShift Scientific Methodology & NASA Integration Principles")
    st.markdown("""
    ### NASA Space Apps Challenge Alignment:
    **"Field Shift: Adapting Farms with NASA Data"**

    FieldShift strictly implements the project requirement that **NASA Earth observations form the core evidence foundation of the system**, not an ornamental weather widget.

    #### 1. Data Integrity & Anti-Fabrication Guarantee
    - **Never fabricate NASA values:** If an Earth observation product requires NASA Earthdata authentication (such as SMAP Level-3 or GPM IMERG NetCDF rasters), FieldShift queries genuine metadata via NASA Common Metadata Repository (CMR), transparently labels the authentication requirement, and strictly avoids substituting synthetic or invented observations.
    - **Physical distinctions:** FieldShift distinguishes between satellite-observed variables and in-situ laboratory soil tests. Satellites quantify canopy radiation, atmospheric moisture fluxes, and thermal skin radiance; they do not measure laboratory chemical soil pH or available phosphorus.

    #### 2. Satellite Sensors & Resolutions
    - **NASA POWER:** 0.5° x 0.625° reanalysis climatology (MERRA-2 / GEOS-FP). Provides daily air temperature (T2M), corrected precipitation (PRECTOTCORR), solar irradiance, and relative humidity.
    - **NASA GPM IMERG:** 0.1° (~10 km) multi-satellite radar/radiometer calibrated precipitation. Quantifies localized cloudburst intensity and rainfall variability.
    - **NASA SMAP:** 9 km L-band radiometer volumetric soil moisture. Identifies surface (0-5 cm) vs root-zone (0-100 cm) water deficits.
    - **NASA MODIS:** 250 m 16-day composite Normalized Difference Vegetation Index (NDVI) & Enhanced Vegetation Index (EVI).
    - **NASA ECOSTRESS:** 70 m thermal infrared from the International Space Station. Quantifies canopy Land Surface Temperature (LST) and Evaporative Stress Index (ESI = AET / PET).

    #### 3. Crop Rotation Agronomic Logic
    The multi-season crop rotation engine enforces:
    - **Crop Water Balance:** Compares cumulative crop water requirements ($ET_c$) against NASA POWER historical rainfall.
    - **Biological Nitrogen Replenishment:** Integrates leguminous nitrogen-fixing crops (Soybean, Chickpea, Pigeon Pea, Hairy Vetch) following heavy nitrogen extractors (Corn, Wheat) to rebuild fertility without excessive synthetic fertilizers.
    - **Pathogen & Pest Cycle Disruption:** Breaks host-specific pathogen lifecycles by alternating botanical families (Poaceae → Fabaceae → Brassicaceae / Asteraceae) and alternating taproot and fibrous root architectures.
    """)
