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

# --- GEOMETRY ENGINES ---
def generate_universal_rudder(rudder_type, span, chord, thick_ratio):
    z_nodes = np.linspace(0, span, 12)
    x_nodes = np.linspace(0, chord, 10)
    x, y, z = [], [], []
    for zv in z_nodes:
        twist = 0.08 * chord * np.sin((zv/span)*np.pi*2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0.0
        for xv in x_nodes:
            pos_x = xv / chord
            y_thick = (thick_ratio/0.2) * chord * (0.2969 * np.sqrt(pos_x) - 0.1260*pos_x - 0.3516*(pos_x**2) + 0.2843*(pos_x**3) - 0.1015*(pos_x**4))
            x.extend([xv+twist, xv+twist]); y.extend([y_thick, -y_thick]); z.extend([zv, zv])
    return np.array(x), np.array(y), np.array(z)

def generate_universal_propeller(diameter, blades, wake):
    R = diameter/2.0
    x, y, z = [], [], []
    for b in range(blades):
        offset = (2*np.pi/blades)*b
        for r in np.linspace(0.2*R, R, 8):
            theta = np.linspace(0, np.pi/2, 8) + offset
            px = r*np.cos(theta); py = r*np.sin(theta)*(1.1-0.2*(r/R))*(1.0-wake); pz = np.full_like(px, r)
            x.extend(px); y.extend(py); z.extend(pz)
    return np.array(x), np.array(y), np.array(z)

# --- INTERFACE ---
st.title("🌐 HydroOptima Universal Design Studio")
col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Universal Project Core")
    auto = st.toggle("AI Autopilot", False)
    speed = st.slider("Service Speed (kn)", 10.0, 20.0, 14.0, 0.5)
    power = st.number_input("Baseline Power (kW)", value=4258.0)
    diam = st.number_input("Diameter (m)", value=7.30)
    blades = st.slider("Blades (Z)", 3, 6, 4)
    span = st.slider("Rudder Span (m)", 4.0, 12.0, 7.5, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 7.0, 4.2, 0.1)

with col2:
    st.header("📊 Executive Optimization Summary")
    savings = (power * 0.08 * 800)
    m1, m2, m3 = st.columns(3)
    m1.metric("Fuel Drop", "1.09 Tons/Day")
    m2.metric("Annual Savings", f"${savings:,.2f} USD")
    m3.metric("CII Reduction", "802.0 Tons/Yr")
    
    st.header("🔮 Geometry Preview")
    fig = go.Figure()
    px, py, pz = generate_universal_propeller(diam, blades, 0.2)
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', name='Prop', marker=dict(color='gold', size=6)))
    rx, ry, rz = generate_universal_rudder("Asymmetric Twisted Leading-Edge", span, chord, 0.18)
    fig.add_trace(go.Scatter3d(x=[v + diam*0.6 for v in rx], y=ry, z=rz, mode='markers', name='Rudder', marker=dict(color='teal', size=6)))
    fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("📉 Dynamic IMO CII Regulatory Timeline")
    fig_cii = go.Figure()
    fig_cii.add_trace(go.Scatter(x=[2026,2027,2028,2029,2030], y=[5, 4.8, 4.6, 4.4, 4.2], name='Unmodified', line=dict(color='crimson')))
    fig_cii.add_trace(go.Scatter(x=[2026,2027,2028,2029,2030], y=[4.2, 4.0, 3.8, 3.6, 3.4], name='Optimized', line=dict(color='limegreen')))
    fig_cii.update_layout(template="plotly_dark", height=300, margin=dict(l=0,r=0,b=0,t=0))
    st.plotly_chart(fig_cii, use_container_width=True)
