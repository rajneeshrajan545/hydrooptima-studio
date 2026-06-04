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

def save_project(p_id, client, v_type, speed, wake, thrust, power, dwt, diam, fuel, days, b_count, h_ratio, p_law, r_type, r_span, r_chord, r_thick, sfoc_val):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO projects VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
                   (p_id, client, v_type, speed, wake, thrust, power, dwt, diam, fuel, days, b_count, h_ratio, p_law, r_type, r_span, r_chord, r_thick, sfoc_val))
    conn.commit()
    conn.close()

def get_all_projects():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

# --- MATH ENGINES ---
def get_imo_parameters(vessel_type, dwt):
    if vessel_type == "Bulk Carrier": return 4745.0, 0.622
    return 4745.0, 0.622

def generate_universal_propeller(diameter, hub_ratio, blades, pitch_law, wake_fraction):
    radius = diameter / 2.0
    r_hub = radius * hub_ratio
    x, y, z = [], [], []
    for b in range(blades):
        offset = (2 * np.pi / blades) * b
        for r_step in np.linspace(r_hub, radius, 5):
            norm_r = r_step / radius
            pitch = (1.0 - 0.15 * (norm_r - 0.7)**2) * (1.0 - wake_fraction) if pitch_law == "Parabolic (Reduced Tip & Hub Loading)" else (1.1 - 0.2 * norm_r) * (1.0 - wake_fraction)
            theta = np.linspace(0, np.pi / 2, 8) + offset
            px = r_step * np.cos(theta); py = r_step * np.sin(theta) * pitch; pz = np.full_like(px, r_step)
            x.extend(px); y.extend(py); z.extend(pz)
    return np.array(x), np.array(y), np.array(z)

def generate_universal_rudder(rudder_type, span, chord, thick_ratio):
    z_nodes = np.linspace(0, span, 12)
    x_nodes = np.linspace(0, chord, 10)
    x, y, z = [], [], []
    for z_val in z_nodes:
        twist = 0.08 * chord * np.sin((z_val / span) * np.pi * 2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0.0
        for x_val in x_nodes:
            pos_x = x_val / chord
            y_thick = (thick_ratio / 0.2) * chord * (0.2969 * np.sqrt(pos_x) - 0.1260 * pos_x - 0.3516 * (pos_x**2) + 0.2843 * (pos_x**3) - 0.1015 * (pos_x**4))
            x.extend([x_val + twist, x_val + twist]); y.extend([y_thick, -y_thick]); z.extend([z_val, z_val])
    return np.array(x), np.array(y), np.array(z)

# --- APP LAYOUT ---
st.title("🌐 HydroOptima Universal Design Studio")
if "s_val" not in st.session_state:
    st.session_state.update({"s_val": 14.0, "p_val": 4258.0, "diam_val": 7.30, "b_count": 4, "r_span": 7.5, "r_chord": 4.2})

col1, col2 = st.columns([1, 2])
with col1:
    st.header("📋 Project Inputs")
    speed = st.slider("Service Speed (kn)", 10.0, 20.0, st.session_state.s_val, 0.5)
    power = st.number_input("Baseline Power (kW)", value=st.session_state.p_val)
    diam = st.number_input("Propeller Diameter (m)", value=st.session_state.diam_val)
    blades = st.slider("Blades (Z)", 3, 6, st.session_state.b_count)
    span = st.slider("Rudder Span (m)", 4.0, 10.0, st.session_state.r_span, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 6.0, st.session_state.r_chord, 0.1)

with col2:
    st.header("🔮 Real-Time Universal Geometry Preview")
    fig = go.Figure()
    px, py, pz = generate_universal_propeller(diam, 0.22, blades, "Parabolic (Reduced Tip & Hub Loading)", 0.2)
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='lines', line=dict(color='gold', width=4)))
    rx, ry, rz = generate_universal_rudder("Asymmetric Twisted Leading-Edge", span, chord, 0.18)
    fig.add_trace(go.Scatter3d(x=[v + diam*0.6 for v in rx], y=ry, z=rz, mode='lines', line=dict(color='cyan', width=2)))
    fig.update_layout(template="plotly_dark", height=450, scene=dict(aspectmode='data'))
    st.plotly_chart(fig, use_container_width=True)
    st.metric("Annual OPEX Savings (USD)", f"${(power * 0.08 * 800):,.2f}")
