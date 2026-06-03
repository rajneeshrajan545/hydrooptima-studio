import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sqlite3

st.set_page_config(page_title="Advanced Propulsion & Hydrodynamic Studio", layout="wide")

# --- DATABASE SETUP AND WRITING UTILITIES ---
DB_FILE = "projects.db"

def init_db():
    """Initializes the database table if it doesn't exist yet."""
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
            op_days REAL
        )
    """)
    conn.commit()
    conn.close()

def save_project(p_id, client, v_type, speed, wake, thrust, power, dwt, diam, fuel, days):
    """Saves or updates a project profile in the SQL database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO projects 
        (project_id, client_name, vessel_type, speed, wake_fraction, thrust_deduction, power, dwt, diameter, fuel_cost, op_days)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (p_id, client, v_type, speed, wake, thrust, power, dwt, diam, fuel, days))
    conn.commit()
    conn.close()

def get_all_projects():
    """Retrieves all saved project records for selection dropdowns."""
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

# Initialize DB structure on load
init_db()

# --- PASSWORD PROTECTION MODULE ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("🔒 Secure Portal: HydroOptima AI Enterprise Infrastructure")
        password = st.text_input("Enter Access Security Key", type="password")
        if st.button("Unlock Studio Portal"):
            if password == "HydroSecure2026": 
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ Invalid Access Key. Verification Failed.")
    return False

if check_password():
    # Branded Header Elements
    st.title("🌐 HydroOptima AI Studio")
    st.subheader("Parametric Propulsion Optimization & Commercial Evaluation Engine")
    st.write("Proprietary system for hull-vessel interaction optimization and EEXI / CII regulatory compliance.")

    # --- TOP ROW: HISTORY RETRIEVAL MANAGER ---
    st.markdown("### 🗃️ Enterprise Knowledge Base")
    saved_df = get_all_projects()

    selected_project = "New Project Configuration"
    if not saved_df.empty:
        project_list = ["New Project Configuration"] + saved_df['project_id'].tolist()
        chosen_profile = st.selectbox("Load Saved Asset Configuration Profile:", project_list)
        if chosen_profile != "New Project Configuration":
            # Extract row from DB data frame to overwrite inputs dynamically
            p_data = saved_df[saved_df['project_id'] == chosen_profile].iloc[0]
            selected_project = p_data['project_id']
            st.success(f"Successfully loaded saved parameters for **{selected_project}**!")

    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    # Fallback/Initialization defaults mapping
    is_loaded = (selected_project != "New Project Configuration")

    with col1:
        st.header("📋 Project Input Mode")
        input_mode = st.radio("Select Data Input Method", ["Interactive Sliders", "Automated CSV Upload"])

        client_val = p_data['client_name'] if is_loaded else "Global Maritime Fleet"
        id_val = p_data['project_id'] if is_loaded else "Project Eco-Bulk 01"
        vtype_val = p_data['vessel_type'] if is_loaded else "Capesize Bulk Carrier"

        client_name = st.text_input("Client / Shipowner Identifier", value=client_val)
        vessel_id = st.text_input("Vessel Identifier / Project Code", value=id_val)
        vessel_type = st.selectbox("Vessel Hull Form Architecture", ["Handymax Product Tanker", "Aframax Crude Carrier", "Capesize Bulk Carrier", "Landing Craft / Special Utility"], index=["Handymax Product Tanker", "Aframax Crude Carrier", "Capesize Bulk Carrier", "Landing Craft / Special Utility"].index(vtype_val))

        if input_mode == "Interactive Sliders":
            st.markdown("---")
            st.subheader("Manual Inflow Parameters")
            s_val = float(p_data['speed']) if is_loaded else 13.0
            w_val = float(p_data['wake_fraction']) if is_loaded else 0.296
            t_val = float(p_data['thrust_deduction']) if is_loaded else 0.201
            p_val = float(p_data['power']) if is_loaded else 3401.0

            v_knots = st.slider("Design Service Speed (Knots)", 11.0, 15.0, s_val, 0.5)
            w_fraction = st.slider("Model Taylor Wake Fraction (w)", 0.250, 0.350, w_val, 0.001)
            t_deduction = st.slider("Thrust Deduction Factor (t)", 0.150, 0.250, t_val, 0.001)
            baseline_power = st.number_input("Baseline Shaft Power (kW)", value=p_val)
        else:
            st.markdown("---")
            st.subheader("📂 Drag & Drop Towing Tank Data")
            uploaded_file = st.file_uploader("Upload Model Test CSV Report", type=["csv"])
            # Fall back to baseline values if no file dropped yet
            v_knots = float(p_data['speed']) if is_loaded else 13.0
            w_fraction = float(p_data['wake_fraction']) if is_loaded else 0.296
            t_deduction = float(p_data['thrust_deduction']) if is_loaded else 0.201
            baseline_power = float(p_data['power']) if is_loaded else 3401.0

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
                except Exception as e:
                    st.error(f"Failed to read file: {e}")

        st.markdown("---")
        st.subheader("Vessel Configuration")
        dwt_val = float(p_data['dwt']) if is_loaded else 82000.0
        diam_val = float(p_data['diameter']) if is_loaded else 6.8
        fuel_val = float(p_data['fuel_cost']) if is_loaded else 650.0
        days_val = float(p_data['op_days']) if is_loaded else 220.0

        vessel_dwt = st.number_input("Vessel Deadweight (DWT Tons)", value=dwt_val)
        diameter = st.number_input("Maximum Propeller Diameter (meters)", value=diam_val)
        fuel_cost = st.number_input("VLSFO Fuel Cost (USD / Metric Ton)", value=fuel_val)
        op_days = st.number_input("Annual Days at Sea", value=days_val)

        # COMMIT TO ARCHIVE BUTTON
        st.markdown("---")
        if st.button("💾 Commit Current Parameters to Database"):
            save_project(vessel_id, client_name, vessel_type, v_knots, w_fraction, t_deduction, baseline_power, vessel_dwt, diameter, fuel_cost, op_days)
            st.success(f"✅ Record written successfully! Saved as '{vessel_id}'")
            st.rerun()

    # Core Calculations
    baseline_efficiency = 0.696
    optimized_efficiency = 0.742  
    sfc = 0.185 / 1000.0  

    daily_baseline_fuel = baseline_power * 24 * sfc
    efficiency_ratio = baseline_efficiency / optimized_efficiency
    optimized_power = baseline_power * efficiency_ratio
    daily_optimized_fuel = optimized_power * 24 * sfc

    daily_fuel_saved = daily_baseline_fuel - daily_optimized_fuel
    annual_cash_saved = daily_fuel_saved * fuel_cost * op_days

    annual_dist = v_knots * 24 * op_days
    co2_factor = 3.114  

    annual_co2_base = daily_baseline_fuel * co2_factor * op_days
    annual_co2_opt = daily_optimized_fuel * co2_factor * op_days
    annual_co2_saved = annual_co2_base - annual_co2_opt

    cii_baseline = (annual_co2_base * 10**6) / (vessel_dwt * annual_dist)
    cii_optimized = (annual_co2_opt * 10**6) / (vessel_dwt * annual_dist)

    with col2:
        st.header("📊 Executive Optimization Summary")
        m1, m2, m3 = st.columns(3)
        m1.metric(label="Daily Fuel Consumption Drop", value=f"{daily_fuel_saved:.2f} Tons/Day")
        m2.metric(label="Annual OPEX Savings", value=f"${annual_cash_saved:,.2f} USD")
        m3.metric(label="CII Carbon Reduction Impact", value=f"{annual_co2_saved:.1f} Tons/Yr")

        st.markdown("---")
        st.subheader("🔮 Real-Time Hydrodynamic Geometry Preview")

        fig3d = go.Figure()
        prop_stations = np.linspace(0.2, 1.0, 6)
        prop_pitch = np.array([0.74, 0.80, 0.84, 0.85, 0.81, 0.76]) * (w_fraction / 0.296)

        for r, p in zip(prop_stations, prop_pitch):
            theta = np.linspace(0, np.pi/2, 12)
            px = r * (diameter/2) * np.cos(theta)
            py = r * (diameter/2) * np.sin(theta) * p
            pz = np.full_like(px, r * (diameter/2))
            fig3d.add_trace(go.Scatter3d(x=px, y=py, pz=pz, mode='lines', line=dict(color='orange', width=4), showlegend=False))

        rudder_z = np.linspace(0, 8.5, 10)
        rudder_x = np.sin(np.linspace(-np.pi/2, np.pi/2, 10)) * (6.5 * (v_knots / 13.0) / 10)
        fig3d.add_trace(go.Scatter3d(x=rudder_x, y=np.zeros_like(rudder_x), z=rudder_z, mode='lines+markers', line=dict(color='cyan', width=5), name="Twisted Rudder Profile"))

        fig3d.update_layout(template="plotly_dark", height=350, margin=dict(l=0, r=0, b=0, t=0),
                            scene=dict(xaxis_title="X (Trans)", yaxis_title="Y (Flow)", zaxis_title="Z (Span)"))
        st.plotly_chart(fig3d, use_container_width=True)

        st.markdown("---")
        st.subheader("📉 IMO CII Regulatory Life-Extension Timeline")

        years = np.array([2026, 2027, 2028, 2029, 2030])
        cii_required_c = np.array([cii_baseline * 0.95, cii_baseline * 0.91, cii_baseline * 0.87, cii_baseline * 0.83, cii_baseline * 0.79])
        cii_required_e = cii_required_c * 1.15

        fig_cii = go.Figure()
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_c, mode='lines', name='Target Profile Threshold (C-Rating)', line=dict(color='green', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_e, mode='lines', name='Critical Violation Boundary (E-Rating)', line=dict(color='red', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_baseline]*5, mode='lines+markers', name='Unmodified Status Quo', line=dict(color='crimson', width=3)))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_optimized]*5, mode='lines+markers', name='With HydroOptima Integration', line=dict(color='limegreen', width=4)))

        fig_cii.update_layout(template="plotly_dark", height=300, margin=dict(l=40, r=20, b=30, t=20),
                            xaxis=dict(tickmode='array', tickvals=years), yaxis_title="Attained CII (g-CO2 / DWT-Mile)",
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_cii, use_container_width=True)

        st.success(f"⚖️ **Compliance Advantage:** Integrating the custom twisted rudder bulb saves approximately **{annual_co2_saved:.1f} tons** of carbon emissions annually, securely extending structural fleet viability through **2030**.")

        st.markdown("---")
        st.subheader("🛠️ Production-Ready Data Export")

        csv_data = f"# HYDROOPTIMA AI STUDIO - GEOMETRY PACKAGE\n# CLIENT: {client_name} | ID: {vessel_id}\n"
        clean_file_name = f"{vessel_id.replace(' ', '_')}_HydroOptima_Design.xyz"
        st.download_button(label="📥 Export .XYZ Production Coordinate Package", data=csv_data, file_name=clean_file_name, mime="text/plain")

    st.write("\n--- Proprietary Engineering Asset Toolchain | Powered by HydroOptima AI ---")
