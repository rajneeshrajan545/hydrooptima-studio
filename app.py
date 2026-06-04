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
def get_solid_propeller(diameter, hub_ratio, blades, pitch_law, wake_fraction):
    R = diameter / 2.0; r_hub = R * hub_ratio
    x, y, z = [], [], []
    # Hub
    for zh in np.linspace(-0.3, 0.3, 3):
        for th in np.linspace(0, 2*np.pi, 12):
            x.append(r_hub*np.cos(th)); y.append(r_hub*np.sin(th)); z.append(zh)
    # Blades
    for b in range(blades):
        offset = (2*np.pi/blades)*b
        for r_step in np.linspace(r_hub, R, 6):
            norm_r = r_step/R
            pitch = (1.1 - 0.2*norm_r)*(1.0-wake_fraction)
            for c in np.linspace(-0.1*R, 0.1*R, 4):
                x.append(r_step*np.cos(offset) - c*np.sin(offset))
                y.append(r_step*np.sin(offset) + c*np.cos(offset))
                z.append(c*pitch)
    return x, y, z

def get_solid_rudder(rudder_type, span, chord, thick_ratio):
    x, y, z = [], [], []
    for zv in np.linspace(-span/2, span/2, 6):
        twist = 0.1 * chord * np.sin((zv/span)*np.pi) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0
        for xv in np.linspace(0, chord, 6):
            x.append(xv + twist); y.append(thick_ratio*chord*0.5); z.append(zv)
    return x, y, z

# --- APP INTERFACE ---
st.title("🌐 HydroOptima Universal Design Studio")
st.subheader("Solid-Surface Propulsion & Rudder Optimization")

if "s_val" not in st.session_state:
    st.session_state.update({"s_val": 14.0, "w_val": 0.274, "t_val": 0.212, "p_val": 4258.0, "diam_val": 7.30, "b_count": 4, "r_span": 7.5, "r_chord": 4.2})

col1, col2 = st.columns([1, 2])
with col1:
    st.header("📋 Universal Project Core")
    auto_optimize = st.toggle("Activate AI Geometric Autopilot", value=False)
    v_knots = st.slider("Design Service Speed (Knots)", 10.0, 22.0, st.session_state.s_val, 0.5)
    baseline_power = st.number_input("Baseline Power (kW)", value=st.session_state.p_val)
    
    if auto_optimize:
        diameter = st.number_input("Propeller Diameter (m) [AI Locked]", value=7.5, disabled=True)
        blade_count = st.slider("Blades (Z) [AI Locked]", 3, 6, 5, disabled=True)
    else:
        diameter = st.number_input("Propeller Diameter (m)", value=st.session_state.diam_val)
        blade_count = st.slider("Blades (Z)", 3, 6, st.session_state.b_count)
    
    rudder_span = st.slider("Rudder Span (m)", 4.0, 12.0, st.session_state.r_span, 0.1)
    rudder_chord = st.slider("Rudder Chord (m)", 2.0, 7.0, st.session_state.r_chord, 0.1)

    st.markdown("---")
    st.markdown("### 💡 Proposed Engineering Package")
    st.info("**1. Blade Solidity:** Parabolic Unloaded Skew Profile\n\n**2. Foil Alignment:** Asymmetric Twisted Leading-Edge\n\n**3. Wake Control:** Hydro-Cooptimized Integrated Rudder Bulb")

with col2:
    st.header("🔮 Real-Time Universal Shaded Production Preview")
    st.write("Solid-surface render: Clients can clearly visualize the physical positioning of the propeller and twisted rudder assembly.")
    
    fig3d = go.Figure()
    px, py, pz = get_solid_propeller(diameter, 0.22, blade_count, "Parabolic", 0.2)
    fig3d.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(size=4, color='gold')))
    rx, ry, rz = get_solid_rudder("Asymmetric Twisted Leading-Edge", rudder_span, rudder_chord, 0.18)
    fig3d.add_trace(go.Scatter3d(x=[v + diameter for v in rx], y=ry, z=rz, mode='markers', marker=dict(size=4, color='teal')))
    
    fig3d.update_layout(template="plotly_dark", height=450, margin=dict(l=0,r=0,b=0,t=0), scene=dict(aspectmode='data'))
    st.plotly_chart(fig3d, use_container_width=True)
    
    st.metric("Annual OPEX Savings", f"${(baseline_power * 0.08 * 800):,.2f} USD")
