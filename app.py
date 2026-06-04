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

def get_imo_parameters(vessel_type, dwt):
    if vessel_type == "Bulk Carrier": return 4745.0, 0.622
    elif vessel_type == "Tanker": return 5247.0, 0.610
    elif vessel_type == "General Cargo Ship": return (31948.0, 0.792) if dwt >= 20000 else (588.0, 0.3885)
    return 4745.0, 0.622

# --- NEW ADVANCED SOLID-SURFACE GENERATIVE ENGINES ---
def get_solid_propeller(diameter, hub_ratio, blades, pitch_law, wake_fraction):
    R = diameter / 2.0
    r_hub = R * hub_ratio

    x, y, z = [], [], []
    i_indices, j_indices, k_indices = [], [], []
    v_count = 0

    # 1. Generate a solid Hub Cylinder
    z_hub_steps = np.linspace(-0.5, 0.5, 5)
    theta_steps = np.linspace(0, 2*np.pi, 20)

    hub_v_start = v_count
    for zh in z_hub_steps:
        for th in theta_steps:
            x.append(r_hub * np.cos(th))
            y.append(r_hub * np.sin(th))
            z.append(zh)
            v_count += 1

    # Build hub surface triangles
    for h in range(len(z_hub_steps) - 1):
        for t in range(len(theta_steps) - 1):
            p1 = hub_v_start + h * len(theta_steps) + t
            p2 = p1 + 1
            p3 = p1 + len(theta_steps)
            p4 = p3 + 1
            i_indices.extend([p1, p2])
            j_indices.extend([p3, p3])
            k_indices.extend([p2, p4])

    # 2. Generate Solid, Shaded Aero-foil Blades
    for b in range(blades):
        blade_offset = (2 * np.pi / blades) * b
        r_vals = np.linspace(r_hub, R, 8)
        c_vals = np.linspace(-0.2 * R, 0.2 * R, 8)

        blade_v_start = v_count
        grid_shape = (len(r_vals), len(c_vals))

        # Calculate pitch twist coordinates
        for r_idx, r in enumerate(r_vals):
            norm_r = r / R
            pitch_angle = (0.5 - 0.2 * norm_r) * (1.0 - wake_fraction)
            if pitch_law == "Parabolic (Reduced Tip & Hub Loading)":
                pitch_angle *= (1.0 - 0.15 * (norm_r - 0.7)**2)

            for c_idx, c in enumerate(c_vals):
                # Upper Face section
                pos_x = (c + 0.2*R) / (0.4*R)
                thick = 0.1 * R * (1.0 - norm_r) * np.sin(pos_x * np.pi)

                rot_x = r * np.cos(blade_offset) - c * np.sin(blade_offset)
                rot_y = r * np.sin(blade_offset) + c * np.cos(blade_offset)
                rot_z = c * pitch_angle + thick

                x.append(rot_x); y.append(rot_y); z.append(rot_z)
                v_count += 1

        # Build blade surface triangles mesh
        for r_i in range(grid_shape[0] - 1):
            for c_j in range(grid_shape[1] - 1):
                p1 = blade_v_start + r_i * grid_shape[1] + c_j
                p2 = p1 + 1
                p3 = p1 + grid_shape[1]
                p4 = p3 + 1
                i_indices.extend([p1, p2])
                j_indices.extend([p3, p3])
                k_indices.extend([p2, p4])

    return x, y, z, i_indices, j_indices, k_indices

def get_solid_rudder(rudder_type, span, chord, thick_ratio):
    x, y, z = [], [], []
    i_indices, j_indices, k_indices = [], [], []
    v_count = 0

    z_steps = np.linspace(0, span, 10)
    x_steps = np.linspace(0, chord, 10)
    grid_shape = (len(z_steps), len(x_steps))

    rudder_v_start = v_count

    # Generate NACA-profile 3D thickness wrapper shell
    for z_idx, z_val in enumerate(z_steps):
        twist = 0.12 * chord * np.sin((z_val / span) * np.pi * 2) if rudder_type == "Asymmetric Twisted Leading-Edge" else 0.0
        for x_idx, x_val in enumerate(x_steps):
            pos_x = x_val / chord
            # Standard structural wing thickness equation profile
            y_thick = (thick_ratio / 0.2) * chord * (
                0.2969 * np.sqrt(pos_x) - 0.1260 * pos_x - 0.3516 * (pos_x**2) + 0.2843 * (pos_x**3) - 0.1015 * (pos_x**4)
            )
            if rudder_type == "Schilling / Flapped High-Lift" and pos_x > 0.85:
                y_thick += (pos_x - 0.85) * chord * 0.2

            x.append(x_val + twist)
            y.append(y_thick)
            z.append(z_val - (span / 2.0)) # Position directly behind center line hub axis
            v_count += 1

    # Connect mesh face shell triangles
    for z_i in range(grid_shape[0] - 1):
        for x_j in range(grid_shape[1] - 1):
            p1 = rudder_v_start + z_i * grid_shape[1] + x_j
            p2 = p1 + 1
            p3 = p1 + grid_shape[1]
            p4 = p3 + 1
            i_indices.extend([p1, p2])
            j_indices.extend([p3, p3])
            k_indices.extend([p2, p4])

    return x, y, z, i_indices, j_indices, k_indices

# --- SECURITY GATEWAY ---
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

    # --- SYNCHRONIZED APP STORAGE APP CACHE ---
    if "s_val" not in st.session_state:
        st.session_state.s_val, st.session_state.w_val, st.session_state.t_val, st.session_state.p_val = 14.0, 0.274, 0.212, 4258.0
        st.session_state.dwt_val, st.session_state.diam_val, st.session_state.fuel_val, st.session_state.days_val = 82000.0, 7.30, 650.0, 220.0
        st.session_state.b_count, st.session_state.hub_ratio, st.session_state.p_law = 4, 0.22, "Parabolic (Reduced Tip & Hub Loading)"
        st.session_state.r_type, st.session_state.r_span, st.session_state.r_chord, st.session_state.r_thick = "Asymmetric Twisted Leading-Edge", 7.5, 4.2, 0.18
        st.session_state.client_val, st.session_state.id_val, st.session_state.vtype_val = "Global Maritime Fleet", "Project SM1751", "Bulk Carrier"
        st.session_state.sfoc_default = 185.0

    st.markdown("---")
    col1, col2 = st.columns([1, 2])

    with col1:
        st.header("📋 Universal Project Core")
        input_mode = st.radio("Select Data Input Method", ["Interactive Sliders", "Automated CSV Upload"])

        client_name = st.text_input("Client / Shipowner Identifier", value=st.session_state.client_val)
        vessel_id = st.text_input("Vessel Identifier / Project Code", value=st.session_state.id_val)
        vessel_type = st.selectbox("Vessel Hull Form Classification", ["Bulk Carrier", "Tanker", "General Cargo Ship", "LNG Carrier"])

        if input_mode == "Automated CSV Upload":
            st.markdown("---")
            st.subheader("📂 Drag & Drop Towing Tank Spreadsheet")
            uploaded_file = st.file_uploader("Upload Model Test CSV Profile", type=["csv"])
            if uploaded_file is not None:
                try:
                    csv_df = pd.read_csv(uploaded_file)
                    if 'Speed' in csv_df.columns: st.session_state.s_val = float(csv_df['Speed'].iloc[0])
                    if 'Wake' in csv_df.columns: st.session_state.w_val = float(csv_df['Wake'].iloc[0])
                    if 'Thrust_Deduction' in csv_df.columns: st.session_state.t_val = float(csv_df['Thrust_Deduction'].iloc[0])
                    if 'Power' in csv_df.columns: st.session_state.p_val = float(csv_df['Power'].iloc[0])
                    if 'DWT' in csv_df.columns: st.session_state.dwt_val = float(csv_df['DWT'].iloc[0])
                    if 'Diameter' in csv_df.columns: st.session_state.diam_val = float(csv_df['Diameter'].iloc[0])
                    if 'Blades' in csv_df.columns: st.session_state.b_count = int(csv_df['Blades'].iloc[0])
                    if 'SFOC' in csv_df.columns: st.session_state.sfoc_default = float(csv_df['SFOC'].iloc[0])
                    st.success("🎯 Spreadsheet variables configured loaded!")
                except Exception as e: st.error(f"Failed parsing file columns: {e}")

        st.markdown("---")
        st.subheader("🤖 AI Hydrodynamic Autopilot Optimization")
        auto_optimize = st.toggle("Activate AI Geometric Autopilot", value=False)

        st.markdown("---")
        st.subheader("🌊 Operational Conditions")
        vessel_dwt = st.number_input("Vessel Deadweight (DWT Tons)", value=float(st.session_state.dwt_val))
        v_knots = st.slider("Design Service Speed (Knots)", 10.0, 22.0, float(st.session_state.s_val), 0.5)
        w_fraction = st.slider("Taylor Wake Fraction (w)", 0.100, 0.400, float(st.session_state.w_val), 0.001)
        t_deduction = st.slider("Thrust Deduction Factor (t)", 0.100, 0.300, float(st.session_state.t_val), 0.001)

        baseline_power = st.number_input("Baseline Installed Shaft Power (kW)", value=float(st.session_state.p_val))
        sfoc_input = st.number_input("Specific Fuel Oil Consumption - SFOC (g/kW-h)", value=float(st.session_state.sfoc_default), step=1.0)
        fuel_cost = st.number_input("Fuel Cost (USD / Metric Ton)", value=float(st.session_state.fuel_val))
        op_days = st.number_input("Annual Days Operational at Sea", value=float(st.session_state.days_val))

        st.markdown("---")
        st.subheader("⚙️ Propeller & Rudder Criteria Control")

        if auto_optimize:
            st.info("⚡ Autopilot Active: Controls locked to mathematically optimized values.")
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

        # --- PICTORIAL RETROFIT ENGINEERING BLOCKS SIDEBAR EXPLANATION ---
        st.markdown("---")
        st.markdown("### 💡 Proposed Retrofit Engineering Explanations")
        st.markdown(
            """
            <div style="background-color: #1e2630; padding: 15px; border-radius: 8px; border-left: 5px solid #2196F3; margin-bottom: 15px;">
                <h4 style="color: #2196F3; margin-top: 0; margin-bottom: 5px; font-size: 15px;">⚙️ 1. Propeller Blade Solidity Upgrade</h4>
                <p style="font-size: 12px; color: #cccccc; margin: 0;">
                    <b>Existing Baseline:</b> Standard 4-Blade Hub (High concentrated tip loading).<br>
                    <b>Proposed Solution:</b> Parabolic Unloaded Skew Profile (High surface area balance).<br>
                    <span style="color: #4CAF50;"><b>🎨 Visual Benefit:</b> Spreads hydro-thrust loads evenly to completely eliminate sheet cavitation.</span>
                </p>
            </div>
            <div style="background-color: #1e2630; padding: 15px; border-radius: 8px; border-left: 5px solid #00BCD4; margin-bottom: 15px;">
                <h4 style="color: #00BCD4; margin-top: 0; margin-bottom: 5px; font-size: 15px;">🧬 2. Asymmetric Foil Alignment</h4>
                <p style="font-size: 12px; color: #cccccc; margin: 0;">
                    <b>Existing Baseline:</b> Symmetric Flat-Plate Rudder (Creates trailing fluid drag).<br>
                    <b>Proposed Solution:</b> Curved Leading-Edge Twisted Sections.<br>
                    <span style="color: #4CAF50;"><b>🎨 Visual Benefit:</b> Intercepts chaotic propeller vortex rotational fluid and turns it into forward thrust.</span>
                </p>
            </div>
            <div style="background-color: #1e2630; padding: 15px; border-radius: 8px; border-left: 5px solid #FF9800; margin-bottom: 5px;">
                <h4 style="color: #FF9800; margin-top: 0; margin-bottom: 5px; font-size: 15px;">🎯 3. Wake Equalization Hub Coupling</h4>
                <p style="font-size: 12px; color: #cccccc; margin: 0;">
                    <b>Existing Baseline:</b> Empty low-pressure pocket trailing behind boss cap.<br>
                    <b>Proposed Solution:</b> Hydro-Cooptimized Integrated Rudder Bulb.<br>
                    <span style="color: #4CAF50;"><b>🎨 Visual Benefit:</b> Streamlines the hub flow bypass to completely clear remaining core vortex resistance.</span>
                </p>
            </div>
            """, 
            unsafe_allow_html=True
        )

    # --- HYDRODYNAMIC MATHEMATICAL CALCULATIONS ---
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
        st.subheader("🔮 Real-Time Universal Shaded Production Preview")
        st.write("渲染出的实体曲面：客户端可以清晰看到高空化螺旋桨叶片与扭曲翼形舵体之间的物理空间位置。")

        # --- NEW SOLID-SURFACE RENDER CONVERTER BLOCK ---
        fig3d = go.Figure()

        # 1. Plot the Solid, Burnished Propeller and Cylinder Hub Unit
        px, py, pz, pi, pj, pk = get_solid_propeller(diameter, hub_ratio, blade_count, pitch_law, w_fraction)
        fig3d.add_trace(go.Mesh3d(
            x=px, y=py, z=pz, i=pi, j=pj, k=pk,
            name="Propeller Assembly",
            color='gold', opacity=0.90,
            flatshading=False,
            lighting=dict(ambient=0.45, diffuse=0.8, roughness=0.3, specular=0.6, fresnel=0.2),
            lightposition=dict(x=100, y=200, z=150)
        ))

        # 2. Plot the Solid, Textured Hydrofoil Rudder Unit (placed directly downstream at X offset)
        rx, ry, rz, ri, rj, rk = get_solid_rudder(rudder_type, rudder_span, rudder_chord, naca_thickness)
        # Shift the solid rudder assembly downstream behind the hub disk face boundary
        rx_shifted = np.array(rx) + (diameter * 0.55)
        fig3d.add_trace(go.Mesh3d(
            x=rx_shifted, y=ry, z=rz, i=ri, j=rj, k=rk,
            name="Optimized Foil Rudder",
            color='teal', opacity=0.85,
            flatshading=False,
            lighting=dict(ambient=0.50, diffuse=0.7, roughness=0.4, specular=0.4),
            lightposition=dict(x=100, y=200, z=150)
        ))

        fig3d.update_layout(
            template="plotly_dark", height=480, margin=dict(l=0, r=0, b=0, t=0),
            scene=dict(
                xaxis=dict(title="X (Aft Axis / Slipstream Flow)", range=[-diameter, diameter*2]),
                yaxis=dict(title="Y (Profile Thickness Profile)", range=[-diameter, diameter]),
                zaxis=dict(title="Z (Structural Span Vertical)", range=[-diameter, diameter]),
                aspectmode='manual',
                aspectratio=dict(x=1.5, y=1.0, z=1.0),
                camera=dict(eye=dict(x=1.4, y=1.4, z=0.9))
            )
        )
        st.plotly_chart(fig3d, use_container_width=True)

        # --- DYNAMIC BLADE-RPM CAVITATION COUPLING ENGINE ---
        st.markdown("### ⚠️ Hydrodynamic Stability & Cavitation Matrix")
        v_advance = v_knots * 0.5144 * (1.0 - w_fraction)
        rpm_blade_modifier = 1.0 - (0.075 * (blade_count - 4))
        estimated_rpm = ((v_advance * 60) / (diameter * 0.65)) * rpm_blade_modifier
        rps = estimated_rpm / 60.0
        tip_speed = np.pi * diameter * rps

        st.write(f"**Calculated Propeller Tip Speed:** `{tip_speed:.1f} m/s` | **Estimated Operational Shaft Rotation:** `{estimated_rpm:.1f} RPM`")
        st.info(f"🧬 **Current Active Rudder Net Efficiency Lift Coefficient:** `+{rudder_efficiency_gain*100:.2f}%` total propulsive benefit.")

        c1, c2 = st.columns(2)
        with c1:
            if tip_speed < 36.0: st.success(f"🟢 **Tip Velocity Boundary: SAFE ({tip_speed:.1f} m/s)**\n\nLocal shear velocities sit securely below cavitation limits.")
            elif tip_speed <= 43.0: st.warning(f"🟡 **Tip Velocity Boundary: MARGINAL EROSION RISK ({tip_speed:.1f} m/s)**\n\nTip velocities crossing into transition zone. Minor sheet cavitation likely.")
            else: st.error(f"🔴 **Tip Velocity Boundary: CAVITATION CRITICAL ({tip_speed:.1f} m/s)**\n\nSevere localized boiling threshold exceeded! Material erosion risk.")

        with c2:
            loading_index = (baseline_power) / (blade_count * (diameter**2))
            if loading_index < 125.0: st.success("🟢 **Surface Blade Loading Profile: OPTIMAL**")
            else: st.warning("🟡 **Surface Blade Loading Profile: HIGH PRESSURE VARIANCE**")

        st.markdown("---")
        st.subheader("📉 Dynamic IMO CII Regulatory Life-Extension Timeline")
        years = np.array([2026, 2027, 2028, 2029, 2030])
        reduction_factors = np.array([0.05, 0.07, 0.09, 0.11, 0.13])
        cii_required_c = cii_reference_baseline * (1.0 - reduction_factors)
        cii_required_e = cii_required_c * 1.28

        fig_cii = go.Figure()
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_c, mode='lines', name='IMO Target Line (C-Rating Threshold)', line=dict(color='orange', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=cii_required_e, mode='lines', name='IMO Boundary Line (Critical E-Violation)', line=dict(color='red', dash='dash')))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_baseline]*5, mode='lines+markers', name='Unmodified Status Quo', line=dict(color='crimson', width=3)))
        fig_cii.add_trace(go.Scatter(x=years, y=[cii_optimized]*5, mode='lines+markers', name='With Optimized Integration', line=dict(color='limegreen', width=4)))

        fig_cii.update_layout(template="plotly_dark", height=320, margin=dict(l=40, r=20, b=30, t=20))
        st.plotly_chart(fig_cii, use_container_width=True)
