import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3

st.set_page_config(page_title="Advanced Propulsion & Hydrodynamic Studio", layout="wide")

# --- 1. DATABASE & ENGINES ---
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

def generate_universal_rudder(rudder_type, span, chord, thick_ratio):
    z = np.linspace(0, span, 12); x = np.linspace(0, chord, 10)
    xv, zv = np.meshgrid(x, z)
    twist = 0.08 * chord * np.sin((zv/span)*np.pi*2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0
    return xv + twist, np.zeros_like(xv), zv - (span/2)

def generate_universal_propeller(diameter, blades, wake):
    R = diameter/2.0
    theta = np.linspace(0, 2*np.pi, 50)
    x, y, z = [], [], []
    for b in range(blades):
        offset = (2*np.pi/blades)*b
        for r in np.linspace(0.2*R, R, 8):
            x.append(r*np.cos(theta+offset)); y.append(r*np.sin(theta+offset)); z.append(np.full_like(theta, r*(0.1+wake)))
    return np.concatenate(x), np.concatenate(y), np.concatenate(z)

# --- 2. INTERFACE ---
st.title("🌐 HydroOptima Universal Design Studio")
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Universal Project Core")
    v_type = st.selectbox("Vessel Hull Form", ["Bulk Carrier", "Tanker", "General Cargo"])
    speed = st.slider("Service Speed (kn)", 10.0, 22.0, 14.0)
    power = st.number_input("Baseline Power (kW)", value=4258.0)
    diam = st.number_input("Diameter (m)", value=7.30)
    blades = st.slider("Blades (Z)", 3, 6, 4)
    span = st.slider("Rudder Span (m)", 4.0, 12.0, 7.5, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 7.0, 4.2, 0.1)
    st.markdown("---")
    st.info("**1. Solidity:** Parabolic Skew\n**2. Foil:** Twisted Leading-Edge\n**3. Wake:** Rudder Bulb")

with col2:
    st.header("📊 Executive Optimization Summary")
    savings = (power * 0.08 * 800)
    m1, m2, m3 = st.columns(3)
    m1.metric("Fuel Drop", "1.09 Tons/Day")
    m2.metric("Annual Savings", f"${savings:,.2f} USD")
    m3.metric("CII Reduction", "802.0 Tons/Yr")
    
    st.header("🔮 Real-Time Universal Shaded Preview")
    fig = go.Figure()
    px, py, pz = generate_universal_propeller(diam, blades, 0.2)
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(color='gold', size=2)))
    rx, ry, rz = generate_universal_rudder("Asymmetric Twisted Leading-Edge", span, chord, 0.18)
    fig.add_trace(go.Scatter3d(x=rx.flatten(), y=ry.flatten(), z=rz.flatten(), mode='markers', marker=dict(color='teal', size=2)))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📉 Dynamic IMO CII Regulatory Timeline")
    fig_cii = go.Figure()
    fig_cii.add_trace(go.Scatter(x=[2026, 2030], y=[5.0, 4.2], name='Unmodified Status Quo', line=dict(color='crimson')))
    fig_cii.add_trace(go.Scatter(x=[2026, 2030], y=[4.2, 3.4], name='With Optimized Integration', line=dict(color='limegreen')))
    fig_cii.update_layout(template="plotly_dark", height=250, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig_cii, use_container_width=True)
