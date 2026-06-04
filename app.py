import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(page_title="HydroOptima Studio", layout="wide")

# Geometry functions
def get_propeller_mesh(diameter, blades):
    R = diameter / 2.0
    theta = np.linspace(0, 2*np.pi, blades+1)[:-1]
    x, y, z = [], [], []
    for t in theta:
        for r in np.linspace(0.15*R, R, 20):
            x.append(r * np.cos(t)); y.append(r * np.sin(t)); z.append(0.08 * r)
    return x, y, z

def get_rudder_mesh(span, chord):
    x, y, z = [], [], []
    for zv in np.linspace(-span/2, span/2, 20):
        twist = 0.15 * chord * np.sin((zv/span)*np.pi)
        for xv in np.linspace(0, chord, 15):
            x.append(xv + twist); y.append(0.3); z.append(zv)
    return x, y, z

# Interface
st.title("🌐 HydroOptima Universal Design Studio")
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Project Inputs")
    diam = st.number_input("Propeller Diameter (m)", value=7.30)
    blades = st.slider("Blades (Z)", 3, 6, 4)
    span = st.slider("Rudder Span (m)", 4.0, 10.0, 7.5, 0.1)
    chord = st.slider("Rudder Chord (m)", 2.0, 6.0, 4.2, 0.1)

with col2:
    st.header("Real-Time Production Preview")
    fig = go.Figure()
    px, py, pz = get_propeller_mesh(diam, blades)
    rx, ry, rz = get_rudder_mesh(span, chord)
    
    fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='markers', marker=dict(color='gold', size=8)))
    fig.add_trace(go.Scatter3d(x=[v + diam*0.6 for v in rx], y=ry, z=rz, mode='markers', marker=dict(color='teal', size=8)))
    
    fig.update_layout(template="plotly_dark", height=500, scene=dict(aspectmode='manual', aspectratio=dict(x=1.5, y=1, z=1)))
    st.plotly_chart(fig, use_container_width=True)
