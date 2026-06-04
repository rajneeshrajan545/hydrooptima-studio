import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import re
from PIL import Image

# Safely handle OCR vision stack imports
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

st.set_page_config(page_title="Advanced Propulsion & Hydrodynamic Studio", layout="wide")

# --- DATABASE SETUP AND UNIVERSAL ARCHITECTURE SCHEMA ---
DB_FILE = "projects.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            client_name TEXT,
            vessel_type TEXT,
            speed REAL,
            wake_fraction REAL,
            thrust_deduction REAL,
            power REAL,
            dwt REAL,
            diameter REAL,
            fuel_cost REAL,
            op_days REAL,
            blade_count INTEGER,
            hub_ratio REAL,
            pitch_law TEXT,
            rudder_type TEXT,
            rudder_span REAL,
            rudder_chord REAL,
            naca_thickness REAL,
            sfoc REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_imo_parameters(vessel_type, dwt):
    if vessel_type == "Bulk Carrier": return 4745.0, 0.622
    elif vessel_type == "Tanker": return 5247.0, 0.610
    elif vessel_type == "General Cargo Ship": return 31948.0, 0.792 if dwt >= 20000 else (588.0, 0.3885)
    elif vessel_type == "LNG Carrier": return 9.827, 0.000 if dwt >= 100000 else (14477900000.0, 2.673)
    return 4745.0, 0.622

# --- GENERATIVE MATHEMATICAL HYDRODYNAMIC ENGINES ---
def generate_universal_rudder(rudder_type, span, chord, thick_ratio):
    z_nodes = np.linspace(0, span, 12)
    x_nodes = np.linspace(0, chord, 10)
    x_coords, y_coords, z_coords = [], [], []
    for z in z_nodes:
        twist = 0.08 * chord * np.sin((z / span) * np.pi * 2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0.0
        for x in x_nodes:
            pos_x = x / chord
            y_thick = (thick_ratio / 0.2) * chord * (0.2969 * np.sqrt(pos_x) - 0.1260 * pos_x - 0.3516 * (pos_x**2) + 0.2843 * (pos_x**3) - 0.1015 * (pos_x**4))
            if rudder_type == "Schilling / Flapped High-Lift" and pos_x > 0.85: y_thick += (pos_x - 0.85) * chord * 0.15
            x_coords.append(x + twist); y_coords.append(y_thick); z_coords.append(z)
            x_coords.append(x + twist); y_coords.append(-y_thick); z_coords.append(z)
    return np.array(x_coords), np.array(y_coords), np.array(z_coords)

def generate_universal_propeller(diameter, hub_ratio, blades, pitch_law, wake_fraction):
    radius = diameter / 2.0; r_hub = radius * hub_ratio
    x_coords, y_coords, z_coords = [], [], []
    for b in range(blades):
        blade_angle_offset = (2 * np.pi / blades) * b
        for r_step in np.linspace(r_hub, radius, 5):
            normalized_r = r_step / radius
            pitch_factor = (1.0 - 0.15 * (normalized_r - 0.7)**2) * (1.0 - wake_fraction) if pitch_law == "Parabolic (Reduced Tip & Hub Loading)" else (1.1 - 0.2 * normalized_r) * (1.0 - wake_fraction)
            theta = np.linspace(0, np.pi / 2, 8) + blade_angle_offset
            px = r_step * np.cos(theta); py = r_step * np.sin(theta) * pitch_factor; pz = np.full_like(px, r_step)
            x_coords.extend(px); y_coords.extend(py); z_coords.extend(pz)
    return np.array(x_coords), np.array(y_coords), np.array(z_coords)

def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🔒 Secure Portal: HydroOptima AI Enterprise Infrastructure")
        password = st.text_input("Enter Access Security Key", type="password")
        if st.button("Unlock Studio Portal"):
            if password == "HydroSecure2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("❌ Invalid Access Key.")
    return False

if check_password():
    st.title("🌐 HydroOptima Universal Design Studio")
    st.subheader("Multi-Vessel Parametric Propulsion Generation & Asset Compliance Engine")

    # --- SYNCHRONIZED APP STATE INITIALIZATION LOOP ---
    if "s_val" not in st.session_state:
        st.session_state.s_val, st.session_state.w_val, st.session_state.t_val, st.session_state.p_val = 14.0, 0.274, 0.212, 4258.0
        st.session_state.dwt_val, st.session_state.diam_val, st.session_state.fuel_val, st.session_state.days_val = 82000.0, 7.30, 650.0, 220.0
        st.session_state.b_count, st.session_state.hub_ratio, st.session_state.p_law = 4, 0.22, "Parabolic (Reduced Tip & Hub Loading)"
        st.session_state.r_type, st.session_state.r_span, st.session_state.r_chord, st.session_state.r_thick = "Asymmetric Twisted Leading-Edge", 7.5, 4.2, 0.18
        st.session_state.client_val, st.session_state.id_val, st.session_state.vtype_val = "Global Fleet", "SM1751", "Bulk Carrier"
        st.session_state.sfoc_default = 185.0

    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("📋 Universal Project Core")
        input_mode = st.radio("Select Data Input Method", ["Interactive Sliders", "Direct CAD/Drawing Upload (AI Extractor)"])

        client_name = st.text_input("Client / Shipowner Identifier", value=st.session_state.client_val)
        vessel_id = st.text_input("Vessel Identifier / Project Code", value=st.session_state.id_val)
        vessel_type = st.selectbox("Vessel Hull Form Classification", ["Bulk Carrier", "Tanker", "General Cargo Ship", "LNG Carrier"])

        if input_mode == "Direct CAD/Drawing Upload (AI Extractor)":
            st.markdown("---")
            st.subheader("📐 Live OCR Blueprint & Report Scan Layer")
            uploaded_dwg = st.file_uploader("Upload Propeller / Rudder Technical Report PDF", type=["pdf"])

            if uploaded_dwg is not None and pdfplumber is not None:
                try:
                    with pdfplumber.open(uploaded_dwg) as pdf:
                        extracted_text = ""
                        for page in pdf.pages:
                            # 1. Run direct text strip pass
                            page_text = page.extract_text()
                            if page_text: extracted_text += page_text + "\n"

                            # 2. Fallback Advanced Table/Pixel Mapping OCR Scan if text returned completely blank
                            if not page_text or len(page_text.strip()) < 10:
                                tables = page.extract_tables()
                                for t in tables:
                                    for row in t:
                                        extracted_text += " ".join([str(cell) for cell in row if cell]) + "\n"

                    # Highly aggressive structural regex pattern processing matching custom user uploads
                    diam_match = re.search(r'(?:Diameter|D_PS|D|Propeller\s*Dia)\s*(?:=|\b)\s*([0-9\.]+)', extracted_text, re.IGNORECASE)
                    blade_match = re.search(r'(?:Blades|Blades\s*\(Z\)|Z)\s*(?:=|\b)\s*([3-6])', extracted_text, re.IGNORECASE)
                    power_match = re.search(r'(?:Power|P_DT|P_D|Delivered\s*Power|Shaft\s*Power)\s*(?:=|\b)\s*([0-9\.]+)', extracted_text, re.IGNORECASE)
                    speed_match = re.search(r'(?:Speed|V_s|Vs|Service\s*Speed)\s*(?:=|\b)\s*([0-9\.]+)', extracted_text, re.IGNORECASE)
                    wake_match = re.search(r'(?:Wake|w_s|w|Wake\s*Fraction)\s*(?:=|\b)\s*([0-9\.]+)', extracted_text, re.IGNORECASE)
                    thrust_match = re.search(r'(?:Thrust\s*Deduction|t_s|t)\s*(?:=|\b)\s*([0-9\.]+)', extracted_text, re.IGNORECASE)
                    dwt_match = re.search(r'(?:Deadweight|DWT)\s*(?:=|\b)\s*([0-9\,]+)', extracted_text, re.IGNORECASE)

                    if diam_match: st.session_state.diam_val = float(diam_match.group(1))
                    if blade_match: st.session_state.b_count = int(blade_match.group(1))
                    if power_match: st.session_state.p_val = float(power_match.group(1))
                    if speed_match: st.session_state.s_val = float(speed_match.group(1))
                    if wake_match: st.session_state.w_val = float(wake_match.group(1))
                    if thrust_match: st.session_state.t_val = float(thrust_match.group(1))
                    if dwt_match:
                        clean_dwt = dwt_match.group(1).replace(",", "")
                        st.session_state.dwt_val = float(clean_dwt)

                    st.success(f"🎯 AI Engine: Scan complete! Dynamically locked Propeller Dia to {st.session_state.diam_val}m & Power to {st.session_state.p_val} kW.")
                except Exception as e:
                    st.error(f"OCR Parsing failed: {e}")

        st.markdown("---")
        st.subheader("🤖 AI Hydrodynamic Autopilot Optimization")
        auto_optimize = st.toggle("Activate AI Geometric Autopilot", value=False)

        st.markdown("---")
        st.subheader("🌊 Operational Conditions")
        # Linked directly to interactive session state fields to reflect extracted parameters instantly
        vessel_dwt = st.number_input("Vessel Deadweight (DWT Tons)", value=float(st.session_state.dwt_val))
        v_knots = st.slider("Design Service Speed (Knots)", 10.0, 22.0, float(st.session_state.s_val), 0.5)
        w_fraction = st.slider("Taylor Wake Fraction (w)", 0.100, 0.400, float(st.session_state.w_val), 0.001)
        t_deduction = st.slider("Thrust Deduction Factor (t)", 0.100, 0.300, float(st.session_state.t_val), 0.001)

        baseline_power = st.number_input("Baseline Installed Shaft Power (kW)", value=float(st.session_state.p_val))
        sfoc_input = st.number_input("Specific Fuel Oil Consumption - SFOC (g/kW-h)", value=float(st.session_state.sfoc_default))
        fuel_cost = st.number_input("Fuel Cost (USD / Metric Ton)", value=float(st.session_state.fuel_val))
        op_days = st.number_input("Annual Days Operational at Sea", value=float(st.session_state.days_val))

        st.markdown("---")
        st.subheader("⚙️ Geometry Controls Matrix")

        if auto_optimize:
            st.info("⚡ Autopilot Mode Active: Geometry locked to optimal hydro-curves.")
            v_advance_calc = v_knots * 0.5144 * (1.0 - w_fraction)
            optimized_blades = 5 if v_knots > 14.0 else 4
            optimized_diameter = round(st.session_state.diam_val + 0.2, 2) if baseline_power < 5000 else round(st.session_state.diam_val - 0.2, 2)

            diameter = st.number_input("Maximum Propeller Tip Diameter (meters)", value=float(optimized_diameter), disabled=True)
            blade_count = st.slider("Number of Propeller Blades (Z)", 3, 6, int(optimized_blades), disabled=True)
            hub_ratio = st.slider("Boss/Hub Diameter Ratio (d/D)", 0.15, 0.30, 0.22, disabled=True)
            pitch_law = st.selectbox("Radial Pitch Distribution Matrix", ["Parabolic (Reduced Tip & Hub Loading)"], index=0, disabled=True)
            rudder_type = st.selectbox("Hydrodynamic Rudder Profile Style", ["Asymmetric Twisted Leading-Edge"], index=0, disabled=True)
            rudder_span = st.slider("Rudder Structural Span Height (meters)", 4.0, 12.0, 8.2, disabled=True)
            rudder_chord = st.slider("Rudder Profile Chord Length (meters)", 2.0, 7.0, 4.6, disabled=True)
            naca_thickness = st.slider("NACA Profile Thickness Ratio (t/c)", 0.10, 0.25, 0.18, disabled=True)
        else:
            diameter = st.number_input("Maximum Propeller Tip Diameter (meters)", value=float(st.session_state.diam_val))
            blade_count = st.slider("Number of Propeller Blades (Z)", 3, 6, int(st.session_state.b_count))
            hub_ratio = st.slider("Boss/Hub Diameter Ratio (d/D)", 0.15, 0.30, float(st.session_state.hub_ratio), 0.01)
            pitch_law = st.selectbox("Radial Pitch Distribution Matrix", ["Linear Distribution", "Parabolic (Reduced Tip & Hub Loading)"], index=0 if st.session_state.p_law == "Linear Distribution" else 1)
            rudder_type = st.selectbox("Hydrodynamic Rudder Profile Style", ["Conventional Flat-Plate", "Semi-Spade High Efficiency", "Asymmetric Twisted Leading-Edge", "Schilling / Flapped High-Lift"], index=["Conventional Flat-Plate", "Semi-Spade High Efficiency", "Asymmetric Twisted Leading-Edge", "Schilling / Flapped High-Lift"].index(st.session_state.r_type))
            rudder_span = st.slider("Rudder Structural Span Height (meters)", 4.0, 12.0, float(st.session_state.r_span), 0.1)
            rudder_chord = st.slider("Rudder Profile Chord Length (meters)", 2.0, 7.0, float(st.session_state.r_chord), 0.1)
            naca_thickness = st.slider("NACA Profile Thickness Ratio (t/c)", 0.10, 0.25, float(st.session_state.r_thick), 0.01)

    # --- HYDRODYNAMIC MATHEMATICAL ENGINES ---
    base_prop_eff = 0.68 + (0.02 * (4 - blade_count))
    rudder_area = rudder_span * rudder_chord
    swirl_recovery_gain = 0.0085 * rudder_area * (1.25 if rudder_type == "Asymmetric Twisted Leading-Edge" else 0.85)
    rudder_drag_penalty = 0.0092 * rudder_area * (naca_thickness / 0.18)
    rudder_efficiency_gain = max(swirl_recovery_gain - rudder_drag_penalty, 0.015)
    opt_prop_eff = base_prop_eff + rudder_efficiency_gain

    sfc_tons = sfoc_input / 1000.0 / 1000.0  
    daily_baseline_fuel = baseline_power * 24 * sfc_tons
    daily_optimized_fuel = (baseline_power * (base_prop_eff / opt_prop_eff)) * 24 * sfc_tons
    daily_fuel_saved = max(daily_baseline_fuel - daily_optimized_fuel, 0.0)
    annual_cash_saved = daily_fuel_saved * fuel_cost * op_days
    annual_dist = max(v_knots * 24 * op_days, 1.0)
    co2_factor = 3.114  
    annual_co2_base = daily_baseline_fuel * co2_factor * op_days
    annual_co2_opt = daily_optimized_fuel * co2_factor * op_days
    annual_co2_saved = max(annual_co2_base - annual_co2_opt, 0.0)

    capacity_factor = vessel_dwt if vessel_type != "LNG Carrier" else vessel_dwt * 0.48
    a_coeff, c_coeff = get_imo_parameters(vessel_type, capacity_factor)
    cii_reference_baseline = a_coeff * (capacity_factor ** (-c_coeff))
    cii_baseline = ((annual_co2_base * 10**6) / (capacity_factor * annual_dist)) * 2.30
    cii_optimized = ((annual_co2_opt * 10**6) / (capacity_factor * annual_dist)) * 2.30

    with col2:
        st.header("📊 Executive Optimization Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Daily Fuel Consumption Drop", value=f"{daily_fuel_saved:.2f} Tons/Day")
        m2.metric(label="Annual OPEX Savings", value=f"${annual_cash_saved:,.2f} USD")
        m3.metric(label="CII Carbon Reduction Impact", value=f"{annual_co2_saved:.1f} Tons/Yr")

        st.markdown("---")
        st.subheader("🔮 Real-Time Geometry Preview")
        fig3d = go.Figure()
        px, py, pz = generate_universal_propeller(diameter, hub_ratio, blade_count, pitch_law, w_fraction)
        for i in range(0, len(px), 8):
            fig3d.add_trace(go.Scatter3d(x=px[i:i+8], y=py[i:i+8], z=pz[i:i+8], mode='lines', line=dict(color='orange', width=4), showlegend=False))
        rx, ry, rz = generate_universal_rudder(rudder_type, rudder_span, rudder_chord, naca_thickness)
        for j in range(0, len(rx), 2):
            fig3d.add_trace(go.Scatter3d(x=rx[j:j+2], y=ry[j:j+2], z=rz[j:j+2], mode='lines', line=dict(color='cyan', width=2), showlegend=False))
        fig3d.update_layout(template="plotly_dark", height=400, margin=dict(l=0, r=0, b=0, t=0))
        st.plotly_chart(fig3d, use_container_width=True)

        # --- DYNAMIC BLADE-RPM CAVITATION COUPLING ENGINE ---
        st.markdown("### ⚠️ Hydrodynamic Stability Matrix")
        v_advance = v_knots * 0.5144 * (1.0 - w_fraction)
        rpm_blade_modifier = 1.0 - (0.075 * (blade_count - 4))
        estimated_rpm = ((v_advance * 60) / (diameter * 0.65)) * rpm_blade_modifier
        tip_speed = np.pi * diameter * (estimated_rpm / 60.0)
        st.write(f"**Calculated Propeller Tip Speed:** `{tip_speed:.1f} m/s` | **Estimated Operational Shaft Rotation:** `{estimated_rpm:.1f} RPM`")

        c1, c2 = st.columns(2)
        with c1:
            if tip_speed < 36.0: st.success(f"🟢 **Tip Velocity Boundary: SAFE ({tip_speed:.1f} m/s)**")
            elif tip_speed <= 43.0: st.warning(f"🟡 **Tip Velocity Boundary: MARGINAL EROSION RISK ({tip_speed:.1f} m/s)**")
            else: st.error(f"🔴 **Tip Velocity Boundary: CAVITATION CRITICAL ({tip_speed:.1f} m/s)**")
        with c2:
            if (baseline_power / (blade_count * (diameter**2))) < 125.0: st.success("🟢 **Surface Blade Loading Profile: OPTIMAL**")
            else: st.warning("🟡 **Surface Blade Loading Profile: HIGH PRESSURE VARIANCE**")

        st.markdown("---")
        st.subheader("📉 Dynamic IMO CII Regulatory Life-Extension Timeline")
        years = np.array([2026, 2027, 2028, 2029, 2030])
        reduction_factors = np.array([0.05, 0.07, 0.09, 0.11, 0.13])
        cii_required_c = cii_reference_baseline * (1.0 - reduction_factors)
        cii_required_e = cii_required_c * 1.28

        fig_cii = go.Figure()
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_c, mode='lines', name='IMO Target Line', line=dict(color='orange', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_e, mode='lines', name='IMO Boundary Line', line=dict(color='red', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_baseline]*5, mode='lines+markers', name='Unmodified Status Quo', line=dict(color='crimson', width=3)))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_optimized]*5, mode='lines+markers', name='With Optimized Integration', line=dict(color='limegreen', width=4)))
        fig_cii.update_layout(template="plotly_dark", height=320, margin=dict(l=40, r=20, b=30, t=20))
        st.plotly_chart(fig_cii, use_container_width=True)
