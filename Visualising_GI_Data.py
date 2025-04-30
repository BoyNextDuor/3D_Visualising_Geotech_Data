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

if uploaded_file:
    # Define sheet names
    point_sheet = "POINT"
    
    # Read point data (shared between functions)
    df_points = pd.read_excel(uploaded_file, sheet_name=point_sheet)
    df_points = df_points[["PointID", "East", "North", "Elevation"]]

    # --- Moisture Content Heatmap ---
    def plot_moisture_heatmap(uploaded_file, df_points):
        moisture_sheet = "Moisture Content"
        df_moisture = pd.read_excel(uploaded_file, sheet_name=moisture_sheet)
        df_moisture = df_moisture[["ID", "Origin", "From (m)", "To (m)", "Elevation (m)", "Moisture Content (%)"]]

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
                text=df_moisture_merged.apply(lambda row: f"ID: {row['ID']} ({row['From (m)']} - {row['To (m)']}m)<br>Moisture Content: {row['Moisture Content (%)']}%<br>Geology Unit: {row['Origin']}", axis=1),
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

    # --- Borehole Stratigraphy ---
    def plot_borehole_stratigraphy(uploaded_file, df_points):
        strata_sheet = "GEOLOGY_UNIT_1"
        df_strata = pd.read_excel(uploaded_file, sheet_name=strata_sheet)
        df_strata = df_strata[["PointID", "Depth", "Bottom", "Geology_Unit"]]

        df_strata_merged = df_strata.merge(df_points, on="PointID")
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

                show_legend = unit not in added_to_legend
                if show_legend:
                    added_to_legend.add(unit)

                trace = go.Scatter3d(
                    x=[x, x], y=[y, y], z=z, mode='lines',
                    text=f"PointID: {row['PointID']}<br>Depth: {row['Depth']}m<br>Bottom: {row['Bottom']}m<br>Geology Unit: {unit}",
                    hoverinfo='text',
                    line=dict(color=color, width=5),
                    name=unit,
                    showlegend=show_legend
                )
                traces.append(trace)

                # Add label on top
                traces.append(go.Scatter3d(
                    x=[x], y=[y], z=[row["Top_Elev"]],
                    mode='text',
                    text=[row["PointID"]],
                    textposition='top center',
                    showlegend=False
                ))

            fig = go.Figure(data=traces)
            fig.update_layout(
                title="Interactive 3D Borehole Stratigraphy",
                scene=dict(
                    xaxis=dict(title="East", tickformat=".0f"),
                    yaxis=dict(title="North", tickformat=".0f"),
                    zaxis=dict(title="Elevation (m AHD)", tickformat=".0f"),
                ),
                margin=dict(l=0, r=0, b=0, t=40)
            )

            st.plotly_chart(fig)

    # Run selected plot
    if vis_option == "Moisture Content Heatmap":
        plot_moisture_heatmap(uploaded_file, df_points)
    elif vis_option == "Borehole Stratigraphy":
        plot_borehole_stratigraphy(uploaded_file, df_points)

