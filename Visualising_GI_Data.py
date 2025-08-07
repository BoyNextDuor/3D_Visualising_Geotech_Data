# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 17:43:54 2025

@author: ZH16329
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide")

# Initialize session state for refresh control
if "refresh_stratigraphy" not in st.session_state:
    st.session_state.refresh_stratigraphy = False

st.title("3D Geotechnical Visualization")

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xls", "xlsx", "xlsm"])

# Visualization options
vis_option = st.selectbox("Choose visualization type", ["Borehole Stratigraphy", "Moisture Content Heatmap"])
data_option = st.selectbox("Choose data source",["GEOLOGY_UNIT_1", "GEOLOGY_UNIT_2"] )

# Function to transform secondary component names to adjectives
def transform_to_adjective(name):
    if isinstance(name, str):
        if name.lower() == 'sand':
            return 'Sandy'
        elif name.lower() == 'clay':
            return 'Clayey'
        elif name.lower() == 'gravel':
            return 'Gravelly'
        elif name.lower() == 'silt':
            return 'Silty'
    return name

# Function to get soil classification data and compile soil descriptions
def get_soil_classification_data(uploaded_file):
    """
    Read soil classification data and compile soil descriptions
    """
    try:
        soil_sheet = "STRATA_SOIL_AS"
        df_soil = pd.read_excel(uploaded_file, sheet_name=soil_sheet)
        
        # Select required columns
        df_soil = df_soil[["PointID", "Depth", "Bottom", "Soil_Name", "Secondary_Component_1_Name"]]
        
        # Compile soil description
        df_soil['Compiled_Soil_Description'] = (
            df_soil['Secondary_Component_1_Name'].fillna('').apply(transform_to_adjective) + ' ' +
            df_soil['Soil_Name'].fillna('').str.upper()
        ).str.strip()
        
        # Remove extra spaces
        df_soil['Compiled_Soil_Description'] = df_soil['Compiled_Soil_Description'].str.replace(r'\s+', ' ', regex=True)
        
        return df_soil
    except Exception as e:
        st.error(f"Error reading soil classification data: {e}")
        return None

# Function to match soil data with geological strata
def match_soil_with_strata(df_strata, df_soil):
    """
    Match soil classification data with geological strata based on depth intervals
    """
    if df_soil is None:
        return df_strata
    
    # Create a copy of strata data to avoid modifying original
    df_matched = df_strata.copy()
    df_matched['Soil_Description'] = ''
    
    # For each strata record, find overlapping soil classifications
    for idx, strata_row in df_matched.iterrows():
        point_id = strata_row['PointID']
        strata_top = strata_row['Depth']
        strata_bottom = strata_row['Bottom']
        
        # Find soil records for the same borehole that overlap with this stratum
        soil_records = df_soil[
            (df_soil['PointID'] == point_id) &
            (df_soil['Depth'] < strata_bottom) &  # Soil starts before stratum ends
            (df_soil['Bottom'] > strata_top)      # Soil ends after stratum starts
        ]
        
        # Compile all soil descriptions for this stratum
        if not soil_records.empty:
            soil_descriptions = soil_records['Compiled_Soil_Description'].dropna().unique()
            # Remove empty descriptions
            soil_descriptions = [desc for desc in soil_descriptions if desc.strip()]
            df_matched.at[idx, 'Soil_Description'] = ' | '.join(soil_descriptions)
    
    return df_matched

if uploaded_file:
    # Define sheet names
    point_sheet = "POINT"
    material_sheet = "STRATA_MAIN"
    
    # Read point data (shared between functions)
    df_points = pd.read_excel(uploaded_file, sheet_name=point_sheet)
    df_points = df_points[["PointID", "East", "North", "Elevation"]]

    # Read soil classification data
    df_soil = get_soil_classification_data(uploaded_file)

    # --- Moisture Content Heatmap ---
    def plot_moisture_heatmap(uploaded_file, df_points):
        moisture_sheet = "Moisture Content"
        df_moisture = pd.read_excel(uploaded_file, sheet_name=moisture_sheet)
        df_moisture = df_moisture[["ID", "Geology Unit", "From (m)", "To (m)", "Elevation (m)", "Moisture Content (%)"]]

        df_moisture_merged = df_moisture.merge(df_points, left_on="ID", right_on="PointID")
        df_moisture_merged.rename(columns={"Elevation (m)": "Sample_Elevation"}, inplace=True)

        fig = go.Figure(
            data=go.Scatter3d(
                x=df_moisture_merged["East"],
                y=df_moisture_merged["North"],
                z=df_moisture_merged["Sample_Elevation"],
                mode='markers',
                marker=dict(
                    size=6,
                    color=df_moisture_merged["Moisture Content (%)"],
                    colorscale='Viridis',
                    colorbar=dict(title="Moisture Content (%)")
                ),
                text=df_moisture_merged.apply(lambda row: f"ID: {row['ID']} ({row['From (m)']} - {row['To (m)']}m)<br>Moisture Content: {row['Moisture Content (%)']}%<br>Geology Unit: {row['Geology Unit']}", axis=1),
                hoverinfo='text'
            )
        )

        fig.update_layout(
            title="3D Heat Map of Moisture Content",
            scene=dict(
                xaxis=dict(title="East", tickformat=".0f"),
                yaxis=dict(title="North", tickformat=".0f"),
                zaxis=dict(title="Elevation (m AHD)")
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        st.plotly_chart(fig)

    # --- Enhanced Borehole Stratigraphy with Soil Classification ---
    def plot_borehole_stratigraphy(uploaded_file, df_points, data_source):
        strata_sheet = data_source
        df_strata = pd.read_excel(uploaded_file, sheet_name=strata_sheet)
        df_strata = df_strata[["PointID", "Depth", "Bottom", "Geology_Unit"]]

        # Match soil classification with geological strata
        df_strata_with_soil = match_soil_with_strata(df_strata, df_soil)

        df_strata_merged = df_strata_with_soil.merge(df_points, on="PointID")
        df_strata_merged["Bottom_Elev"] = df_strata_merged["Elevation"] - df_strata_merged["Bottom"]
        df_strata_merged["Top_Elev"] = df_strata_merged["Elevation"] - df_strata_merged["Depth"]
        df_strata_merged["Geology_Unit"] = df_strata_merged["Geology_Unit"].astype(str)

        # Sidebar: Color picker
        with st.sidebar.expander("Choose Colors for Geology Units", expanded=False):
            colors = {}
            unique_units = sorted(df_strata_merged["Geology_Unit"].unique())
            for unit in unique_units:
                if f"color_{unit}" not in st.session_state:
                    st.session_state[f"color_{unit}"] = "#%06x" % (hash(unit) % 0xFFFFFF)
                colors[unit] = st.color_picker(f"Color for {unit}", st.session_state[f"color_{unit}"])
                st.session_state[f"color_{unit}"] = colors[unit]

        # Sidebar: Borehole selector
        with st.sidebar.expander("Test Locations", expanded=True):
            select_all = st.checkbox("Select All Boreholes", value=True)
            available_boreholes = sorted(df_strata_merged["PointID"].unique())
            borehole_visibility = {
                borehole: st.checkbox(f"{borehole}", value=select_all)
                for borehole in available_boreholes
            }

        # Control refresh
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Refresh Borehole Plot"):
                st.session_state.refresh_stratigraphy = True
        with col2:
            if st.button("Clear Plot"):
                st.session_state.refresh_stratigraphy = False

        if st.session_state.refresh_stratigraphy:
            selected_boreholes = [bh for bh, visible in borehole_visibility.items() if visible]
            df_filtered = df_strata_merged[df_strata_merged["PointID"].isin(selected_boreholes)]

            traces = []
            added_to_legend = set()

            for _, row in df_filtered.iterrows():
                x, y = row["East"], row["North"]
                z = [row["Top_Elev"], row["Bottom_Elev"]]
                unit = row["Geology_Unit"]
                color = colors[unit]
                
                # Enhanced hover text with soil classification
                soil_desc = row.get("Soil_Description", "")
                hover_text = f"PointID: {row['PointID']}<br>Depth: {row['Depth']}m<br>Bottom: {row['Bottom']}m<br>Geology Unit: {unit}"
                
                if soil_desc:
                    hover_text += f"<br>Soil Type: {soil_desc}"

                show_legend = unit not in added_to_legend
                if show_legend:
                    added_to_legend.add(unit)

                trace = go.Scatter3d(
                    x=[x, x], y=[y, y], z=z, mode='lines',
                    text=hover_text,
                    hoverinfo='text',
                    line=dict(color=color, width=5),
                    name=unit,
                    showlegend=show_legend
                )
                traces.append(trace)

            # Use elevation from POINT sheet and offset label slightly above it
            label_coords = df_points[df_points["PointID"].isin(selected_boreholes)].copy()
            label_coords["Label_Z"] = label_coords["Elevation"] + 0.5  # Add offset above surface
            
            for _, row in label_coords.iterrows():
                traces.append(go.Scatter3d(
                    x=[row["East"]],
                    y=[row["North"]],
                    z=[row["Label_Z"]],
                    mode='text',
                    text=[row["PointID"]],
                    textfont=dict(size=10),
                    showlegend=False
                ))

            fig = go.Figure(data=traces)
            fig.update_layout(
                title="Interactive 3D Borehole Stratigraphy with Soil Classification",
                scene=dict(
                    xaxis=dict(title="East", tickformat=".0f"),
                    yaxis=dict(title="North", tickformat=".0f"),
                    zaxis=dict(title="Elevation (m AHD)", tickformat=".0f"),
                ),
                margin=dict(l=0, r=0, b=0, t=40)
            )

            st.plotly_chart(fig)

            # Display soil classification summary
            if df_soil is not None:
                st.subheader("Soil Type Summary")
                summary_data = df_filtered[df_filtered['Soil_Description'] != ''][['PointID',  'Depth', 'Bottom','Geology_Unit', 'Soil_Description']].copy()
                if not summary_data.empty:
                    st.dataframe(summary_data, use_container_width=True)
                else:
                    st.info("No soil classification data available for selected boreholes.")

    # Run selected plot
    if vis_option == "Moisture Content Heatmap":
        plot_moisture_heatmap(uploaded_file, df_points)
    elif vis_option == "Borehole Stratigraphy":
        plot_borehole_stratigraphy(uploaded_file, df_points, data_option)
