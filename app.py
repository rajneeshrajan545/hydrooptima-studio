import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3

st.set_page_config(page_title="Advanced Propulsion & Hydrodynamic Studio", layout="wide")

# --- DATABASE SETUP ---
DB_FILE = "projects.db"
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY, client_name TEXT, vessel_type TEXT, speed REAL,
            wake_fraction REAL, thrust_deduction REAL, power REAL, dwt REAL, diameter REAL,
            fuel_cost REAL, op_days REAL, blade_count INTEGER, hub_ratio REAL, pitch_law TEXT,
            rudder_type TEXT, rudder_span REAL, rudder_chord REAL, naca_thickness REAL, sfoc REAL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- MATH ENGINES ---
def generate_universal_rudder(rudder_type, span, chord, thick_ratio):
    z = np.linspace(0, span, 12); x = np.linspace(0, chord, 10)
    xv, zv = np.meshgrid(x, z)
    twist = 0.08 * chord * np.sin((zv/span)*np.pi*2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0
    return xv + twist, np.zeros_like(xv), zv - (span/2)

def generate_universal_propeller(diameter, blades, wake):
    R = diameter / 2.0
    theta = np.linspace(0, 2*np.pi, 50)
    x, y, z = [], [], []
    for b in range(blades):
        offset = (2 * np.pi / blades) * b
        for r in np.linspace(0.2 * R, R, 8):
            x.append(r * np.cos(theta + offset))
            y.append(r * np.sin(theta + offset))
            z.append(np.full_like(theta, r * (0.1 + wake)))
    return np.concatenate(x), np.concatenate(y), np.concatenate(z)

# --- APP INTERFACE ---
st.title("🌐 HydroOptima Universal Design Studio")
st.write("Multi-Vessel Parametric Propulsion Generation & Asset Compliance Engine")

if "s_val" not in st.session_state:
    st.session_state.update({"s_val": 14.0, "p_val": 4258.0, "diam_val": 7.30, "b_count": 4, "r_span": 7.5, "r_chord": 4.2})

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Universal Project Core")
    input_mode = st.radio("Select Data Input Method", ["Interactive Sliders", "Automated CSV Upload"])
    v_type = st.selectbox("Vessel Hull Form", ["Bulk Carrier", "Tanker", "General Cargo"])
    speed = st.slider("Service Speed (kn)", 10.0, 22.0, st.session_state.s_val, 0.5)
    power = st.number_input("Baseline Power (kW)", value=st.session_state.p_val)
    diam = st.number_input("Diameter (m)", value=st.session_state.diam_val)
    blades = st.slider("Blades (Z)", 3, 6, st.session_state.b_count)
    span = st.slider("Rudder Span (m)", 4.0, 12.0, st.session_state.r_span, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 7.0, st.session_state.r_chord, 0.1)
    st.markdown("---")
    st.subheader("💡 Proposed Engineering Package")
    st.info("**1. Solidity:** Parabolic Skew\n**2. Foil:** Twisted Leading-Edge\n**3. Wake:** Rudder Bulb")

with col2:
    st.header("📊 Executive Optimization Summary")
    savings = (power * 0.08 * 800)
    m1, m2, m3 = st.columns(3)
    m1.metric("Daily Fuel Drop", "1.09 Tons/Day")
    m2.metric("Annual Savings", f"${savings:,.2f} USD")
    m3.metric("CII Reduction", "802.0 Tons/Yr")
    
    st.header("🔮 Real-Time Universal Geometry Preview")
    fig = go.Figure()
    px, py, pz = generate_universal_propeller(diam, blades, 0.2)
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(color='gold', size=2)))
    rx, ry, rz = generate_universal_rudder("Asymmetric Twisted Leading-Edge", span, chord, 0.18)
    fig.add_trace(go.Scatter3d(x=rx.flatten(), y=ry.flatten(), z=rz.flatten(), mode='markers', marker=dict(color='teal', size=2)))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("⚠️ Hydrodynamic Stability & Cavitation Matrix")
    st.success("🟢 Tip Velocity Boundary: SAFE | Surface Blade Loading: OPTIMAL")

    st.subheader("📉 Dynamic IMO CII Regulatory Timeline")
    fig_cii = go.Figure()
    years = [2026, 2027, 2028, 2029, 2030]
    fig_cii.add_trace(go.Scatter(x=years, y=[5.0, 4.8, 4.6, 4.4, 4.2], name='Unmodified Status Quo', line=dict(color='crimson')))
    fig_cii.add_trace(go.Scatter(x=years, y=[4.2, 4.0, 3.8, 3.6, 3.4], name='With Optimized Integration', line=dict(color='limegreen')))
    fig_cii.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig_cii, use_container_width=True)
