# -*- coding: utf-8 -*-
"""
Created on Tue Jun 17 16:00:33 2025

@author: ZH16329
"""

import streamlit as st
import numpy as np
import pandas as pd
import math
import plotly.graph_objects as go
import plotly.express as px


def plot_psd_for_unit(df_psd, selected_unit):
    
    meta_columns = ['ID', 'From (m)', 'To (m)', 'Geology Unit']
    sieve_sizes_psd = df_psd.columns.difference(meta_columns).astype(float)
    sieve_sizes_psd = sorted(sieve_sizes_psd, reverse=True)  # Largest to smallest

    # Ranges
    gravel_range = (2.36, 63)
    sand_range = (0.075, 2.36)
    fines_range = (0.001, 0.075)

    # Filter data for selected unit
    df_selected = df_psd[df_psd["Geology Unit"] == selected_unit]
    grouped = df_selected.groupby('ID')[sieve_sizes_psd].mean().T

    fig = go.Figure()
    color_list = px.colors.qualitative.Dark24
    
    for i, (idx, row) in enumerate(df_selected.iterrows()):
        y = row[sieve_sizes_psd].values.astype(float)
        fig.add_trace(go.Scatter(
            x=sieve_sizes_psd,
            y=y,
            mode='lines+markers',
            name=f"{row['ID']}@{row['From (m)']}m",
            line=dict(color=color_list[i % len(color_list)])
        ))



    def add_range_box(fig, x_range, label, color, y0=0, y1=10):
        fig.add_shape(type="rect",
            x0=x_range[0], x1=x_range[1],
            y0=y0, y1=y1,
            line=dict(color='black', width=1),
            fillcolor=color,
            opacity=0.3,
            layer="below"
        )
        fig.add_annotation(
            x=(math.log10(x_range[1]) + math.log10(x_range[0]))*0.5,
            y=(y0 + y1) / 2,
            text=label,
            showarrow=False,
            font=dict(color='black', size=10),
            # bgcolor="white"
        )

    def calculate_contents_psd(sample):
        try:
            gravel = 100 - sample[2.36]
            sand = sample[2.36] - sample[0.075]
            fines = sample[0.075]
            return pd.Series([gravel, sand, fines], index=['Gravel Content', 'Sand Content', 'Fines Content'])
        except:
            return pd.Series([None, None, None], index=['Gravel Content', 'Sand Content', 'Fines Content'])


    # Add sand/gravel/fines classification
    add_range_box(fig, gravel_range, "Gravel (2.36-63mm)", "lightgray")
    add_range_box(fig, sand_range, "Sand (0.075-2.36mm)", "lightyellow")
    add_range_box(fig, fines_range, "Fines(<0.075mm)", "lightblue")


    fig.update_layout(
        title=dict(
            text=f"Particle Size Distribution (PSD) Curves for {selected_unit}",
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title='Particle Size (mm)',
            type='log',
            range=[-3, 2],  # Extends to include 0.001 on log scale
            tickvals=[0.001, 0.01, 0.1, 1, 10, 100],
            ticktext=['0.001', '0.01', '0.1', '1', '10', '100'],
            showgrid=True,
            zeroline=False,
            mirror=True,
            showline=True,
            linecolor='black',
            linewidth=1,
        ),
        yaxis=dict(
            title='Percentage Passing (%)',
            range=[0, 100],
            showgrid=True,
            zeroline=False,
            mirror=True,
            showline=True,
            linecolor='black',
            linewidth=1
        ),
        legend=dict(
            title='Borehole ID',
            traceorder="normal",
            orientation="h",
            y=-0.15,
            yanchor="top",
            # itemsizing='constant',
            font=dict(size=12),
            bgcolor='rgba(255,255,255,0.5)',
            # bordercolor='black',
            # borderwidth=1
        ),
        margin=dict(l=80, r=80, t=60, b=100),
        showlegend=True,

        template="plotly_white"
    )

    # Add crossing axes at x=0.001 and y=0
    # fig.add_shape(type="line",
    #               x0=0.001, x1=0.001,
    #               y0=0, y1=100,
    #               line=dict(color="black", width=1))
    # fig.add_shape(type="line",
    #               x0=0.001, x1=100,
    #               y0=0, y1=0,
    #               line=dict(color="black", width=1))
    # Simulate minor gridlines on log x-axis
    minor_ticks = [  # log-spaced between 0.001 and 100
        0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009,
        0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09,
        0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
        2, 3, 4, 5, 6, 7, 8, 9,
        20, 30, 40, 50, 60, 70, 80, 90
    ]

    for tick in minor_ticks:
        fig.add_shape(
            type="line",
            x0=tick, x1=tick,
            y0=0, y1=100,
            line=dict(color="lightgray", width=0.5, dash="dot"),
            layer="below"
        )



    
    
        # Compute gravel, sand, and fines content for each sample
    df_selected_content = df_selected.copy()
    df_selected_content[['Gravel Content', 'Sand Content', 'Fines Content']] = df_selected.apply(calculate_contents_psd, axis=1)
    
    # Select and rename columns for display
    display_columns = ['ID', 'From (m)', 'To (m)', 'Gravel Content', 'Sand Content', 'Fines Content']
    df_display = df_selected_content[display_columns].copy()
    df_display.columns = ['ID', 'From (m)', 'To (m)', 'Gravel (%)', 'Sand (%)', 'Fines (%)']
    
    st.markdown("### PSD Table")
    st.dataframe(df_display.style.format({
        'Gravel (%)': '{:.1f}',
        'Sand (%)': '{:.1f}',
        'Fines (%)': '{:.1f}'
    }), use_container_width=True)


    # Button to calculate and display full content table
    if st.button("Calculate Contents for All Samples"):
        df_all_content = df_psd.copy()
        df_all_content[['Gravel Content', 'Sand Content', 'Fines Content']] = df_all_content.apply(calculate_contents_psd, axis=1)
    
        # Select relevant columns for display
        display_columns = ['ID', 'From (m)', 'To (m)', 'Gravel Content', 'Sand Content', 'Fines Content']
        df_display = df_all_content[display_columns].copy()
        df_display.columns = ['ID', 'From (m)', 'To (m)', 'Gravel (%)', 'Sand (%)', 'Fines (%)']
    
        st.markdown("### Gravel, Sand, and Fines Content for All Samples")
        st.dataframe(df_display.style.format({
            'Gravel (%)': '{:.1f}',
            'Sand (%)': '{:.1f}',
            'Fines (%)': '{:.1f}'
        }), use_container_width=True)

    return fig


def plot_atterberg_limits_chart_plotly(df_atterberg):
    # Convert columns to numeric
    df_atterberg['LL'] = pd.to_numeric(df_atterberg['LL'], errors='coerce')
    df_atterberg['PI'] = pd.to_numeric(df_atterberg['PI'], errors='coerce')

    # Drop rows with missing LL, PI, or Geology Unit
    df_atterberg = df_atterberg.dropna(subset=['ID','From (m)', 'LL', 'PI', 'Geology Unit'])

    # Get list of unique geology units
    units = df_atterberg['Geology Unit'].unique()
    selected_units = st.multiselect("Select Geology Unit(s) to Display", sorted(units), default=units)

    # Filter based on selection
    df_filtered = df_atterberg[df_atterberg['Geology Unit'].isin(selected_units)]

    # A-line and U-line functions
    def a_line(ll): return 0.73 * (ll - 20)
    def u_line(ll): return 0.9 * (ll - 8)

    # A-line and U-line values
    A_ll_vals = np.linspace((4 / 0.73) + 20, 100, 200)
    U_ll_vals = np.linspace((7.5 / 0.9) + 8, 100, 200)
    a_line_vals = a_line(A_ll_vals)
    u_line_vals = u_line(U_ll_vals)

    fig = go.Figure()

    # Plot filtered data
    for unit in selected_units:
        unit_data = df_filtered[df_filtered['Geology Unit'] == unit]
        fig.add_trace(go.Scatter(
            x=unit_data['LL'],
            y=unit_data['PI'],
            mode='markers',
            name=unit,
            text=unit_data['ID'],  # This will show ID on hover
            hovertemplate='<b>ID:</b> %{text}<br>LL: %{x:.1f}<br>PI: %{y:.1f}<extra></extra>',
            opacity=0.6
        ))

    # A-line and U-line
    fig.add_trace(go.Scatter(x=A_ll_vals, y=a_line_vals, mode='lines', name='A-line', line=dict(color='black')))
    fig.add_trace(go.Scatter(x=U_ll_vals, y=u_line_vals, mode='lines', name='U-line', line=dict(color='black', dash='dot')))

    # Horizontal CL & ML lines
    a_line_cl_x = (7.5 / 0.73) + 20
    a_line_ml_x = (4 / 0.73) + 20
    fig.add_trace(go.Scatter(x=[0, a_line_cl_x], y=[7.5, 7.5], mode='lines', name='PI = 7.5', line=dict(color='black', dash='dot')))
    fig.add_trace(go.Scatter(x=[0, a_line_ml_x], y=[4, 4], mode='lines', name='PI = 4', line=dict(color='black', dash='dot')))

    # Vertical LL markers
    fig.add_shape(type='line', x0=35, x1=35, y0=a_line(35), y1=u_line(35), line=dict(color='black'))
    fig.add_shape(type='line', x0=50, x1=50, y0=0, y1=u_line(50), line=dict(color='black'))

    # Annotations
    annotations = [
        dict(x=70, y=45, text="MH or OH", showarrow=False),
        dict(x=80, y=20, text="CH or OH", showarrow=False),
        dict(x=43, y=24, text="CI or OI", showarrow=False),
        dict(x=29, y=14, text="CL or OL", showarrow=False),
        dict(x=40, y=5, text="CL - ML", showarrow=False),
        dict(x=17, y=6, text="ML or OL", showarrow=False),
        dict(x=90, y=a_line(90)-2, text="A-line", showarrow=False, textangle=-42.5),
        dict(x=60, y=u_line(60)+2, text="U-line", showarrow=False, textangle=-45.5),
    ]
    fig.update_layout(annotations=annotations)

    # Axes and layout
    fig.update_layout(
        title=dict(text=f"Casagrande Plasticity Chart - {unit}", x=0.5,xanchor="center"),
        xaxis=dict(title="Liquid Limit (%)", range=[0, 100], showgrid=True, dtick=10, showline=True, mirror=True),
        yaxis=dict(title="Plasticity Index (%)", range=[0, 80], showgrid=True, showline=True, mirror=True),
        legend=dict(yanchor="bottom", y=-0.35, orientation="h", bgcolor='rgba(255,255,255,0.7)', borderwidth=1),
        margin=dict(t=40, b=40, l=40, r=40),
        height=600
    )

    st.plotly_chart(fig, use_container_width=True)

def plot_moisture_content_by_unit(df):
    # # Ensure required columns are present
    required_cols = ['Geology Unit', 'ID', 'Elevation (m)', 'Moisture Content (%)']
    # if not all(col in df.columns for col in required_cols):
    #     st.error("Missing required columns in the data.")
    #     return

    # Drop rows with missing key values
    df = df.dropna(subset=required_cols)

    # Convert to numeric if needed
    df['Elevation (m)'] = pd.to_numeric(df['Elevation (m)'], errors='coerce')
    df['Moisture Content (%)'] = pd.to_numeric(df['Moisture Content (%)'], errors='coerce')

    # Let user select units
    unique_units = df["Geology Unit"].dropna().unique()
    selected_units = st.multiselect("Select Geology Unit(s)", sorted(unique_units), default=unique_units)

    for unit in selected_units:
        df_unit = df[df["Geology Unit"] == unit].copy()

        fig = go.Figure()

        for bh_id in df_unit['ID'].unique():
            bh_data = df_unit[df_unit['ID'] == bh_id]
            fig.add_trace(go.Scatter(
                x=bh_data['Moisture Content (%)'],
                y=bh_data['Elevation (m)'],
                mode='markers',
                name=str(bh_id),
                marker=dict(size=6),
                line=dict(width=1),
                opacity=0.8
            ))

        fig.update_layout(
            title=dict(text=f"Elevation vs Moisture Content – {unit}", x=0.5, xanchor="center"),
            xaxis=dict(title="Moisture Content (%)", range=[0, 100], dtick=10),
            yaxis=dict(title="Elevation (m)", autorange=True),
            height=600,
            width=800,
            legend=dict(yanchor="bottom",y=-0.3, orientation="h"),
            margin=dict(t=40, b=40, l=40, r=40),
        )

        st.plotly_chart(fig, use_container_width=True)


def plot_elevation_vs_pli(file_path, geology_unit):
    # Load data
    df = pd.read_excel(file_path, sheet_name="Rock Results")

    # Drop rows with missing required columns
    df = df.dropna(subset=["Elevation (m)", "Is(50) corrected (MPa)", "Geology Unit"])

    # Filter by geology unit
    filtered_df = df[df["Geology Unit"] == geology_unit]

    if filtered_df.empty:
        st.warning(f"No data found for geology unit '{geology_unit}'.")
        return

    # Get elevation bounds
    min_elev = filtered_df["Elevation (m)"].min() - 5
    max_elev = filtered_df["Elevation (m)"].max() + 5

    # Create plot
    fig = go.Figure()

    # Add data points
    for _, row in filtered_df.iterrows():
        label = f"{row['ID']}: {row['From (m)']} - {row['To (m)']}m"
        fig.add_trace(go.Scatter(
            x=[row["Is(50) corrected (MPa)"]],
            y=[row["Elevation (m)"]],
            mode='markers',
            marker=dict(symbol='circle', size=8),
            name=label,
            showlegend=False
        ))

    # Add strength lines
    strength_lines = [0.03, 0.1, 0.3, 1, 3, 10]
    strength_labels = ["VL", "L", "M", "H", "VH", "EH"]

    for val, label in zip(strength_lines, strength_labels):
        fig.add_trace(go.Scatter(
            x=[val, val],
            y=[min_elev, max_elev],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name=f"{label} ({val} MPa)",
            showlegend=False
        ))

        fig.update_layout(
            margin=dict(l=80, r=80, t=60, b=60),

            title=dict(
                text=f"Elevation vs Is50: {geology_unit}",
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(family='Arial', size=20)
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "Is50 (MPa)",
                    font = dict(family="Arial")
                ),
                tickfont=dict(family='Arial')
            ),
            yaxis=dict(
                autorange=True,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "Elevation (m AHD)",
                    font = dict(
                        family="Arial"
                    )
                ),
                tickfont=dict(family='Arial')
            ),
            font=dict(family='Arial'),  # General font setting (legend, annotations, etc.)
            height=600,
            width=800,
            template="simple_white"
        )



    # Show plot
    st.plotly_chart(fig, use_container_width=True)

   

def plot_elevation_vs_ucs(file_path, geology_unit):
    # Load data
    df = pd.read_excel(file_path, sheet_name="Rock Results")

    # Drop rows with missing required columns
    df = df.dropna(subset=["Elevation (m)", "UCS (MPa)", "Geology Unit"])

    # Filter by geology unit
    filtered_df = df[df["Geology Unit"] == geology_unit]

    if filtered_df.empty:
        st.warning(f"No data found for geology unit '{geology_unit}'.")
        return

    # Get elevation bounds
    min_elev = filtered_df["Elevation (m)"].min() - 5
    max_elev = filtered_df["Elevation (m)"].max() + 5

    # Create plot
    fig = go.Figure()

    # Add data points
    for _, row in filtered_df.iterrows():
        label = f"{row['ID']}: {row['From (m)']} - {row['To (m)']}m"
        fig.add_trace(go.Scatter(
            x=[row["UCS (MPa)"]],
            y=[row["Elevation (m)"]],
            mode='markers',
            marker=dict(symbol='circle', size=8),
            name=label,
            showlegend=True
        ))

    # Add strength lines
    strength_lines = [0.6, 2, 6, 20, 60, 200]
    strength_labels = ["VL", "L", "M", "H", "VH", "EH"]

    for val, label in zip(strength_lines, strength_labels):
        fig.add_trace(go.Scatter(
            x=[val, val],
            y=[min_elev, max_elev],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name=f"{label} ({val} MPa)",
            showlegend=False
        ))

        fig.update_layout(
            margin=dict(l=80, r=80, t=60, b=60),

            title=dict(
                text=f"Elevation vs UCS: {geology_unit}",
                x=0.5,
                xanchor='center',
                yanchor='top',
                font=dict(family='Arial', size=20)
            ),
            xaxis=dict(
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "UCS (MPa)",
                    font = dict(
                        family="Arial"
                    )
                ),
                tickfont=dict(family='Arial')
            ),
            yaxis=dict(
                
                autorange=True,
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "Elevation (m AHD)",
                    font = dict(
                        family="Arial"
                    )
                ),
                tickfont=dict(family='Arial')
            ),
            font=dict(family='Arial'),  # General font setting (legend, annotations, etc.)
            height=600,
            width=800,
            template="simple_white"
        )



    # Show plot
    st.plotly_chart(fig, use_container_width=True)

    # Optional save
    save_path = "elevation_vs_pli.html"
    fig.write_html(save_path)
    st.success(f"Plot saved to {save_path}")


def generate_pli_figure(df, geology_unit):
    filtered_df = df[df["Geology Unit"] == geology_unit].dropna(subset=["Elevation (m)", "Is(50) corrected (MPa)"])

    min_elev = filtered_df["Elevation (m)"].min() - 5
    max_elev = filtered_df["Elevation (m)"].max() + 5

    fig = go.Figure()

    for _, row in filtered_df.iterrows():
        label = f"{row['ID']}: {row['From (m)']} - {row['To (m)']}m"
        fig.add_trace(go.Scatter(
            x=[row["Is(50) corrected (MPa)"]],
            y=[row["Elevation (m)"]],
            mode='markers',
            marker=dict(symbol='circle', size=8),
            name=label,
            showlegend=False
        ))

    # Add strength lines
    strength_lines = [0.03, 0.1, 0.3, 1, 3, 10]
    strength_labels = ["VL", "L", "M", "H", "VH", "EH"]

    for val, label in zip(strength_lines, strength_labels):
        fig.add_trace(go.Scatter(
            x=[val, val],
            #y=[min_elev, max_elev],
            y=[250,305],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name=f"{label} ({val} MPa)",
            showlegend=False
        ))

        fig.update_layout(
            margin=dict(l=80, r=80, t=60, b=60),

            title=dict(
                text=f"Elevation vs Is50: {geology_unit}",
                x=0.5,
                xanchor='center',
                font=dict(family='Arial', size=20)
            ),
            xaxis=dict(
                
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "Is50 (MPa)",
                    font = dict(
                        family="Arial"
                    )
                ),
                tickfont=dict(family='Arial')
            ),
            yaxis=dict(
                
                #autorange=True,
                autorange=False,
                range=[250,305],
                showgrid=True,
                gridcolor='lightgray',
                gridwidth=1,
                showline=True,
                linewidth=1,
                linecolor='black',
                mirror=True,
                title=dict(
                    text = "Elevation (m AHD)",
                    font = dict(
                        family="Arial"
                    )
                ),
                tickfont=dict(family='Arial')
            ),
            font=dict(family='Arial'),
            height=600,
            width=800,
            template="simple_white"
        )

    return fig


def generate_ucs_figure(df, geology_unit):
    filtered_df = df[df["Geology Unit"] == geology_unit].dropna(subset=["Elevation (m)", "UCS (MPa)"])

    min_elev = filtered_df["Elevation (m)"].min() - 5
    max_elev = filtered_df["Elevation (m)"].max() + 5

    fig = go.Figure()

    for _, row in filtered_df.iterrows():
        label = f"{row['ID']}: {row['From (m)']} - {row['To (m)']}m"
        fig.add_trace(go.Scatter(
            x=[row["UCS (MPa)"]],
            y=[row["Elevation (m)"]],
            mode='markers',
            marker=dict(symbol='circle', size=8),
            name=label,
            showlegend=True
        ))

    # Strength lines (no legend)
    strength_lines = [0.6, 2, 6, 20, 60, 200] 
    strength_labels = ["VL", "L", "M", "H", "VH", "EH"]

    for val, label in zip(strength_lines, strength_labels):
        fig.add_trace(go.Scatter(
            x=[val, val],
            #y=[min_elev, max_elev],
            y=[250,305],
            mode='lines',
            line=dict(dash='dash', color='red'),
            name=f"{label} ({val} MPa)",
            showlegend=False
        ))

    fig.update_layout(
        margin=dict(l=80, r=80, t=60, b=60),

        title=dict(
            text=f"Elevation vs UCS: {geology_unit}",
            x=0.5,
            xanchor='center',
            font=dict(family='Arial', size=20)
        ),
        xaxis=dict(
            
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True,
            title=dict(
                text = "UCS (MPa)",
                font = dict(
                    family="Arial"
                )
            ),
            tickfont=dict(family='Arial')
        ),
        yaxis=dict(
            
            #autorange=True,
            autorange=False,
            range=[250,305],
            showgrid=True,
            gridcolor='lightgray',
            gridwidth=1,
            showline=True,
            linewidth=1,
            linecolor='black',
            mirror=True,
            title=dict(
                text = "Elevation (m AHD)",
                font = dict(
                    family="Arial"
                )
            ),
            tickfont=dict(family='Arial')
        ),
        font=dict(family='Arial'),
        height=600,
        width=800,
        template="simple_white"
    )

    return fig

def plot_factored_pli_ucs(df, geology_unit,factors):
    filtered_df = df[df["Geology Unit"] == geology_unit]
    y = filtered_df["Elevation (m)"]
    pli = filtered_df["Factored PLI"]
    ucs = filtered_df["UCS (MPa)"]

    fig = go.Figure()

    # Plot factored PLI
    fig.add_trace(go.Scatter(
        x=pli, y=y,
        mode='markers',
        name=f"{factors} x PLI",
        marker=dict(color='blue', symbol='circle', size=8)
    ))

    # Plot UCS
    fig.add_trace(go.Scatter(
        x=ucs, y=y,
        mode='markers',
        name="UCS",
        marker=dict(color='green', symbol='square', size=8)
    ))

    # Consistency lines
    consistency_lines = [0.6, 2, 6, 20, 60, 200]
    consistency_labels = ["VL", "L", "M", "H", "VH", "EH"]
    min_y, max_y = y.min() - 5, y.max() + 5

    for val, label in zip(consistency_lines, consistency_labels):
        fig.add_trace(go.Scatter(
            x=[val, val], y=[min_y, max_y],
            mode="lines",
            line=dict(dash="dash", color="red"),
            name=label,
            showlegend=False
        ))

    fig.update_layout(
        title=dict(text=f"{factors} x PLI × UCS vs Elevation - {geology_unit}", x=0.5, xanchor='center'),
        xaxis=dict(
            title=dict(text="Strength (MPa)", font=dict(family="Arial", size=14)),
            tickfont=dict(family="Arial", size=12),
            showgrid=True, gridcolor='lightgray',
            showline=True, linecolor='black', mirror=True
            
        ),
        yaxis=dict(
            title=dict(text="Elevation (m AHD)", font=dict(family="Arial", size=14)),
            tickfont=dict(family="Arial", size=12),
            autorange=True,
            showgrid=True, gridcolor='lightgray',
            showline=True, linecolor='black', mirror=True
        ),
        font=dict(family="Arial"),
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02),
        margin=dict(l=60, r=160, t=60, b=40)
    )

    return fig





def main():
    st.title("Lab Results Plotter - Soil and Rock")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx","xls","xlsm"])
    
    plot_type = st.selectbox("Select plot type:", ["PSD", "Moisture Content","Atterberg Limits","PLI","UCS","Factored PLI and UCS"])


    if uploaded_file:
        try:
            df_psd = pd.read_excel(uploaded_file, sheet_name="PSD")
            df_atterberg = pd.read_excel(uploaded_file, sheet_name='Atterberg Limits')
            df_mc = pd.read_excel(uploaded_file, sheet_name='Moisture Content')
            df_rock = pd.read_excel(uploaded_file, sheet_name="Rock Results")
            
                       
            if plot_type == "PSD":
                
                geology_units = sorted(df_psd["Geology Unit"].dropna().unique())
                selected_unit = st.selectbox("Select Geology Unit", geology_units)
                fig = plot_psd_for_unit(df_psd, selected_unit)
                st.plotly_chart(fig, use_container_width=True)
            elif plot_type =="Atterberg Limits":
                
                st.subheader("Cassagrande Chart")
                plot_atterberg_limits_chart_plotly(df_atterberg)
            elif plot_type=="Moisture Content":
               
                st.subheader("Moisture Content Chart")
                plot_moisture_content_by_unit(df_mc)
            elif plot_type =="PLI" and st.button("Plot"):
                geology_units = df_rock["Geology Unit"].dropna().unique()
                selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
                plot_elevation_vs_pli(uploaded_file, selected_unit)
            elif plot_type=="PLI" and st.button("Plot All"):
                geology_units = df_rock["Geology Unit"].dropna().unique()
                selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
                st.info(f"Generating plots for {len(geology_units)} geology units...")
                
                for unit in geology_units:
                    st.subheader(f"Elevation vs PLI - {unit}")
                    fig = generate_pli_figure(df_rock, unit)
                    st.plotly_chart(fig, use_container_width=True)
            elif plot_type=="UCS" and st.button("Plot"):
                
                geology_units = df_rock["Geology Unit"].dropna().unique()
                selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
                plot_elevation_vs_ucs(uploaded_file, selected_unit)
            elif plot_type=="UCS" and st.button("Plot All"):
                
                geology_units = df_rock["Geology Unit"].dropna().unique()
                selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
                st.info(f"Generating plots for {len(geology_units)} geology units...")
                for unit in geology_units:
                    st.subheader(f"Elevation vs UCS - {unit}")
                    fig = generate_ucs_figure(df_rock, unit)
                    st.plotly_chart(fig, use_container_width=True)
            elif plot_type=="Factored PLI and UCS": 
                
                geology_units = df_rock["Geology Unit"].dropna().unique()
               # selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
                st.write("### Enter a factor for each geology unit")
                factors = {}
                for unit in sorted(geology_units):
                    factor = st.number_input(f"Factor for {unit}", min_value=0.0, value=1.0, step=0.1, key=unit)
                    factors[unit] = factor

                if st.button("Plot"):
                    for unit in geology_units:
                        unit_df = df_rock[df_rock["Geology Unit"] == unit].copy()
                        unit_df["Factored PLI"] = unit_df["Is(50) corrected (MPa)"] * factors[unit]

                        st.subheader(f"{factors[unit]} x PLI & UCS - {unit}")
                        fig = plot_factored_pli_ucs(unit_df, unit, factors[unit])
                        st.plotly_chart(fig, use_container_width=True)
                
            
            
            
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    



if __name__ == "__main__":
    main()
