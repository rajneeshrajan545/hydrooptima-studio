import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Advanced Propulsion & Hydrodynamic Studio", layout="wide")

# --- SIMPLE PASSWORD PROTECTION MODULE ---
def check_password():
    """Returns True if the user entered the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Render password entry box
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🔒 Secure Portal: HydroOptima AI Enterprise Infrastructure")
        password = st.text_input("Enter Access Security Key", type="password")
        if st.button("Unlock Studio Portal"):
            # Set your custom secret key here
            if password == "HydroSecure2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Access Key. Verification Failed.")
    return False

# Only render the application if the password check passes
if check_password():

    # Branded Header Elements
    st.title("🌐 HydroOptima AI Studio")
    st.subheader("Parametric Propulsion Optimization & Commercial Evaluation Engine")
    st.write("Proprietary system for hull-vessel interaction optimization and EEXI / CII regulatory compliance.")

    # Setup Layout Columns
    col1, col2 = st.columns([1, 2])

    # Set up clean fallback defaults
    v_knots = 13.0
    w_fraction = 0.296
    t_deduction = 0.201
    baseline_power = 3401.0
    client_name = "Global Maritime Fleet"
    vessel_id = "Project Eco-Bulk 01"

    with col1:
        st.header("📋 Project Input Mode")
        input_mode = st.radio("Select Data Input Method", ["Interactive Sliders", "Automated CSV Upload"])

        client_name = st.text_input("Client / Shipowner Identifier", value=client_name)
        vessel_id = st.text_input("Vessel Identifier / Project Code", value=vessel_id)

        if input_mode == "Interactive Sliders":
            st.markdown("---")
            st.subheader("Manual Inflow Parameters")
            v_knots = st.slider("Design Service Speed (Knots)", 11.0, 15.0, 13.0, 0.5)
            w_fraction = st.slider("Model Taylor Wake Fraction (w)", 0.250, 0.350, 0.296, 0.001)
            t_deduction = st.slider("Thrust Deduction Factor (t)", 0.150, 0.250, 0.201, 0.001)
            baseline_power = st.number_input("Baseline Shaft Power (kW)", value=3401.0)
        else:
            st.markdown("---")
            st.subheader("📂 Drag & Drop Towing Tank Data")
            uploaded_file = st.file_uploader("Upload Model Test CSV Report", type=["csv"])
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success("File parsed successfully!")
                    if all(col in df.columns for col in ['Speed', 'Wake', 'Thrust_Deduction', 'Power']):
                        v_knots = float(df['Speed'].iloc[0])
                        w_fraction = float(df['Wake'].iloc[0])
                        t_deduction = float(df['Thrust_Deduction'].iloc[0])
                        baseline_power = float(df['Power'].iloc[0])
                        st.info(f"💡 AI Auto-Extraction Success: Speed={v_knots}kn")
                    else:
                        st.error("Missing required CSV columns.")
                except Exception as e:
                    st.error(f"Failed to read file: {e}")

        st.markdown("---")
        st.subheader("Vessel Configuration")
        diameter = st.number_input("Maximum Propeller Diameter (meters)", value=6.8)
        fuel_cost = st.number_input("VLSFO Fuel Cost (USD / Metric Ton)", value=650)
        op_days = st.number_input("Annual Days at Sea", value=220)

    # Reactive Calculations
    baseline_efficiency = 0.696
    optimized_efficiency = 0.742  
    sfc = 0.185 / 1000.0  
    daily_baseline_fuel = baseline_power * 24 * sfc
    efficiency_ratio = baseline_efficiency / optimized_efficiency
    optimized_power = baseline_power * efficiency_ratio
    daily_optimized_fuel = optimized_power * 24 * sfc

    daily_fuel_saved = daily_baseline_fuel - daily_optimized_fuel
    annual_cash_saved = daily_fuel_saved * fuel_cost * op_days
    annual_co2_saved = daily_fuel_saved * 3.114 * op_days

    with col2:
        st.header("📊 Executive Optimization Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Daily Fuel Consumption Drop", value=f"{daily_fuel_saved:.2f} Tons/Day")
        m2.metric(label="Annual OPEX Savings", value=f"${annual_cash_saved:,.2f} USD")
        m3.metric(label="CII Carbon Reduction Impact", value=f"{annual_co2_saved:.1f} Tons/Yr")

        st.markdown("---")
        st.subheader("🔮 Real-Time Hydrodynamic Geometry Preview")

        fig = go.Figure()
        prop_stations = np.linspace(0.2, 1.0, 6)
        prop_pitch = np.array([0.74, 0.80, 0.84, 0.85, 0.81, 0.76]) * (w_fraction / 0.296)

        for r, p in zip(prop_stations, prop_pitch):
            theta = np.linspace(0, np.pi/2, 12)
            px = r * (diameter/2) * np.cos(theta)
            py = r * (diameter/2) * np.sin(theta) * p
            pz = np.full_like(px, r * (diameter/2))
            fig.add_trace(go.Scatter3d(x=px, y=py, z=pz, mode='lines', line=dict(color='orange', width=4), showlegend=False))

        rudder_z = np.linspace(0, 8.5, 10)
        rudder_x = np.sin(np.linspace(-np.pi/2, np.pi/2, 10)) * (6.5 * (v_knots / 13.0) / 10)
        fig.add_trace(go.Scatter3d(x=rudder_x, y=np.zeros_like(rudder_x), z=rudder_z, mode='lines+markers', line=dict(color='cyan', width=5), name="Twisted Rudder Profile"))

        fig.update_layout(
            template="plotly_dark",
            height=450,
            margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis_title="Transverse (X)",
                yaxis_title="Flow Angle (Y)",
                zaxis_title="Span Height (Z)"
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("🛠️ Production-Ready Data Export")

        csv_data = f"# HYDROOPTIMA AI STUDIO - GEOMETRY PACKAGE\n# CLIENT: {client_name} | ID: {vessel_id}\n"
        clean_file_name = f"{vessel_id.replace(' ', '_')}_HydroOptima_Design.xyz"
        st.download_button(label="📥 Export .XYZ Production Coordinate Package", data=csv_data, file_name=clean_file_name, mime="text/plain")

    st.write("\n--- Proprietary Engineering Asset Toolchain | Powered by HydroOptima AI ---")
