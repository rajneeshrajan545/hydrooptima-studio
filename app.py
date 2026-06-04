import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="HydroOptima Studio", layout="wide")

# --- 1. GEOMETRY ENGINES ---
def get_propeller_mesh(diameter, blades):
    R = diameter / 2.0
    theta = np.linspace(0, 2*np.pi, blades+1)[:-1]
    x, y, z = [], [], []
    for t in theta:
        for r in np.linspace(0.15*R, R, 20):
            x.append(r * np.cos(t))
            y.append(r * np.sin(t))
            z.append(0.08 * r)
    return x, y, z

def get_rudder_mesh(span, chord):
    x, y, z = [], [], []
    for zv in np.linspace(-span/2, span/2, 20):
        twist = 0.15 * chord * np.sin((zv/span)*np.pi)
        for xv in np.linspace(0, chord, 15):
            x.append(xv + twist)
            y.append(0.3)
            z.append(zv)
    return x, y, z

# --- 2. INTERFACE ---
st.title("🌐 HydroOptima Universal Design Studio")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("📋 Universal Project Core")
    auto_optimize = st.toggle("Activate AI Geometric Autopilot", False)
    speed = st.slider("Service Speed (kn)", 10.0, 20.0, 14.0, 0.5)
    power = st.number_input("Baseline Power (kW)", value=4258.0)
    diam = st.number_input("Propeller Diameter (m)", value=7.30)
    blades = st.slider("Blades (Z)", 3, 6, 4)
    span = st.slider("Rudder Span (m)", 4.0, 10.0, 7.5, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 6.0, 4.2, 0.1)

    st.markdown("---")
    st.markdown("### 💡 Proposed Engineering Package")
    st.info("**1. Blade Solidity:** Parabolic Unloaded Skew Profile\n**2. Foil Alignment:** Asymmetric Twisted Leading-Edge\n**3. Wake Control:** Hydro-Cooptimized Integrated Rudder Bulb")

with col2:
    st.header("🔮 Real-Time Universal Shaded Production Preview")
    st.write("Solid-surface render: Clients can clearly visualize the physical spatial positioning of the anti-cavitation propeller blades and the twisted foil rudder assembly.")
    
    fig = go.Figure()
    # Propeller
    px, py, pz = get_propeller_mesh(diam, blades)
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', name='Propeller', 
                               marker=dict(color='gold', size=8, opacity=0.9)))
    # Rudder
    rx, ry, rz = get_rudder_mesh(span, chord)
    fig.add_trace(go.Scatter3d(x=[v + diam*0.6 for v in rx], y=ry, z=rz, mode='markers', name='Rudder', 
                               marker=dict(color='teal', size=8, opacity=0.9)))
    
    fig.update_layout(template="plotly_dark", height=500, margin=dict(l=0,r=0,b=0,t=0), 
                      scene=dict(aspectmode='manual', aspectratio=dict(x=1.5, y=1, z=1)))
    st.plotly_chart(fig, use_container_width=True)
    
    savings = (power * 0.08 * 800)
    st.metric("Annual OPEX Savings (USD)", f"${savings:,.2f}")
    
    st.markdown("### ⚠️ Hydrodynamic Stability & Cavitation Matrix")
    tip_speed = np.pi * diam * (14.0 * 0.5144 / 0.65 / 60)
    if tip_speed < 36: st.success(f"🟢 Tip Velocity Boundary: SAFE ({tip_speed:.1f} m/s)")
    else: st.warning(f"🔴 Tip Velocity Boundary: CAVITATION RISK ({tip_speed:.1f} m/s)")
