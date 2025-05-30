# -*- coding: utf-8 -*-
"""
Created on Wed Apr  2 17:43:54 2025

@author: ZH16329
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Streamlit UI
st.title("3D Geotechnical Visualization")

# File uploader
uploaded_file = st.file_uploader("Upload an Excel file", type=["xls", "xlsx", "xlsm"])

# Visualization options
vis_option = st.selectbox("Choose visualization type", [ "Borehole Stratigraphy", "Moisture Content Heatmap"])

if uploaded_file:
    # Define sheet names
    point_sheet = "POINT"
    
    # Read point data (this will be shared between both functions)
    df_points = pd.read_excel(uploaded_file, sheet_name=point_sheet)
    df_points = df_points[["PointID", "East", "North", "Elevation"]]
    
    # Function to plot moisture content heatmap
    def plot_moisture_heatmap(uploaded_file, df_points):
        moisture_sheet = "Moisture Content"
        df_moisture = pd.read_excel(uploaded_file, sheet_name=moisture_sheet)
        df_moisture = df_moisture[["ID", "Origin", "From (m)", "To (m)", "Elevation (m)", "Moisture Content (%)"]]
        
        # Merge moisture data with point locations
        df_moisture_merged = df_moisture.merge(df_points, left_on="ID", right_on="PointID")
        df_moisture_merged.rename(columns={"Elevation (m)": "Sample_Elevation"}, inplace=True)

        # Create scatter plot with color-coded moisture content
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

        # Update layout
        fig.update_layout(
            title="3D Heat Map of Moisture Content",
            scene=dict(
                xaxis=dict(title="East", tickformat=".0f"),
                yaxis=dict(title="North", tickformat=".0f"),
                zaxis_title="Elevation (m AHD)",
            ),
            margin=dict(l=0, r=0, b=0, t=40)
        )

        # Display in Streamlit
        st.plotly_chart(fig)

    # Function to plot borehole stratigraphy
    def plot_borehole_stratigraphy(uploaded_file, df_points):
        strata_sheet = "STRATA_MAIN"
        
        df_strata = pd.read_excel(uploaded_file, sheet_name=strata_sheet)

        # Identify main and sub-layers
        main_layers = df_strata[df_strata["Sub_Layer"].isna() | (df_strata["Sub_Layer"].astype(str).str.upper() != "TRUE")].copy()
        sub_layers = df_strata[df_strata["Sub_Layer"].astype(str).str.upper() == "TRUE"].copy()
        
        # For each sub-layer, remove overlapping main-layer intervals
        filtered_main_layers = []
        for point_id in main_layers["PointID"].unique():
            borehole_main = main_layers[main_layers["PointID"] == point_id].copy()
            borehole_sub = sub_layers[sub_layers["PointID"] == point_id].copy()
            
            if not borehole_sub.empty:
                for _, sub_row in borehole_sub.iterrows():
                    sub_top, sub_bottom = sub_row["Depth"], sub_row["Bottom"]
                    # Drop main layer intervals fully within sub-layer range
                    borehole_main = borehole_main[~(
                        (borehole_main["Depth"] >= sub_top) &
                        (borehole_main["Bottom"] <= sub_bottom)
                    )]
            
            filtered_main_layers.append(borehole_main)
        
        # Combine cleaned main layers + sub-layers
        cleaned_main = pd.concat(filtered_main_layers, ignore_index=True)
        df_strata_combined = pd.concat([cleaned_main, sub_layers], ignore_index=True)
        
        # Keep only required columns
        df_strata_combined = df_strata_combined[["PointID", "Depth", "Bottom", "Geology_Unit_1"]]

        
        df_strata_merged = df_strata_combined.merge(df_points, on="PointID")


        # Adjust depths to elevation reference
        df_strata_merged["Bottom_Elev"] = df_strata_merged["Elevation"] - df_strata_merged["Bottom"]
        df_strata_merged["Top_Elev"] = df_strata_merged["Elevation"] - df_strata_merged["Depth"]

        # Ensure Geology_Unit_1 is of string type
        df_strata_merged["Geology_Unit_1"] = df_strata_merged["Geology_Unit_1"].astype(str)

        # Define colors for different geological units with Streamlit color picker
        unique_units = sorted(df_strata_merged["Geology_Unit_1"].unique())  # Sort the units
        
        # Define colors for different geological units with Streamlit color picker
        # Sidebar: Collapsible Color Selection
        with st.sidebar.expander("Choose Colors for Geology Units", expanded=False):
            # Define colors for different geological units with Streamlit color picker
            colors = {}
            for unit in unique_units:
                colors[unit] = st.color_picker(f"Color for {unit}", "#%06x" % (hash(unit) % 0xFFFFFF))

        

        # Sidebar: Collapsible Borehole Selection
        with st.sidebar.expander("Test Locations", expanded=True):
            # "Select All" checkbox
            select_all = st.checkbox("Select All Boreholes", value=True)
        
            # Get list of available boreholes
            available_boreholes = sorted(df_strata_merged["PointID"].unique())
        
            # Create checkboxes for individual boreholes
            borehole_visibility = {
                borehole: st.checkbox(f"{borehole}", value=select_all)
                for borehole in available_boreholes
            }
        
        # Filter boreholes based on selection
        selected_boreholes = [bh for bh, visible in borehole_visibility.items() if visible]
        df_strata_filtered = df_strata_merged[df_strata_merged["PointID"].isin(selected_boreholes)]
        
        # Create traces for selected boreholes
        traces = []
        added_to_legend = set()
        for _, row in df_strata_filtered.iterrows():
            x, y = row["East"], row["North"]
            z = [row["Top_Elev"], row["Bottom_Elev"]]
            unit = row["Geology_Unit_1"]
            color = colors[unit]
        
            show_legend = unit not in added_to_legend
            if show_legend:
                added_to_legend.add(unit)
        
            trace = go.Scatter3d(
                x=[x, x], y=[y, y], z=z, mode='lines',
                text=f"PointID: {row['PointID']}<br>Depth: {row['Depth']}m<br>Bottom: {row['Bottom']}m<br>Geology Unit: {unit}",
                hoverinfo='text',
                line=dict(color=color, width=7),
                name=unit, showlegend=show_legend
            )
            traces.append(trace)
        
        # Create interactive plot
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
        
        # Display in Streamlit
        st.plotly_chart(fig)



    # Execute selected visualization
    if vis_option == "Moisture Content Heatmap":
        plot_moisture_heatmap(uploaded_file, df_points)
    elif vis_option == "Borehole Stratigraphy":
        plot_borehole_stratigraphy(uploaded_file, df_points)
