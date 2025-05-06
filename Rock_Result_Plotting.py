# -*- coding: utf-8 -*-
"""
Created on Thu May  1 11:46:25 2025

@author: ZH16329
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def plot_elevation_vs_pli(file_path, geology_unit):
    # Load data
    df = pd.read_excel(file_path, sheet_name="Rock Results_reduced")

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

    # Optional save
    save_path = "elevation_vs_pli.html"
    fig.write_html(save_path)
    st.success(f"Plot saved to {save_path}")

def plot_elevation_vs_ucs(file_path, geology_unit):
    # Load data
    df = pd.read_excel(file_path, sheet_name="Rock Results_reduced")

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

def plot_factored_pli_ucs(df, geology_unit,pli_factor):
    filtered_df = df[df["Geology Unit"] == geology_unit]
    y = filtered_df["Elevation (m)"]
    pli = filtered_df["Factored PLI"]
    ucs = filtered_df["UCS (MPa)"]

    fig = go.Figure()

    # Plot factored PLI
    fig.add_trace(go.Scatter(
        x=pli, y=y,
        mode='markers',
        name=f"{pli_factor} x PLI",
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
        title=dict(text=f"{pli_factor} x PLI & UCS - {geology_unit}", x=0.5, xanchor='center'),
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



# Streamlit UI
def main():
    st.title("Rock Results Plotter")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx","xls","xlsm"])
    
    plot_type = st.selectbox("Select plot type:", ["PLI", "UCS","Factored PLI and UCS"])


    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, sheet_name="Rock Results_reduced")
            geology_units = df["Geology Unit"].dropna().unique()
            selected_unit = st.selectbox("Select Geology Unit", sorted(geology_units))
            if plot_type=="PLI" and st.button("Plot"):
                plot_elevation_vs_pli(uploaded_file, selected_unit)
            elif plot_type=="PLI" and st.button("Plot All"):
                st.info(f"Generating plots for {len(geology_units)} geology units...")
                for unit in geology_units:
                    st.subheader(f"Elevation vs PLI - {unit}")
                    fig = generate_pli_figure(df, unit)
                    st.plotly_chart(fig, use_container_width=True)
            elif plot_type=="UCS" and st.button("Plot"):
                plot_elevation_vs_ucs(uploaded_file, selected_unit)
            elif plot_type=="UCS" and st.button("Plot All"):
                st.info(f"Generating plots for {len(geology_units)} geology units...")
                for unit in geology_units:
                    st.subheader(f"Elevation vs UCS - {unit}")
                    fig = generate_ucs_figure(df, unit)
                    st.plotly_chart(fig, use_container_width=True)
            elif plot_type=="Factored PLI and UCS": 
                st.write("### Enter a factor for each geology unit")
                factors = {}
                for unit in sorted(geology_units):
                    factor = st.number_input(f"Factor for {unit}", min_value=0.0, value=1.0, step=0.1, key=unit)
                    factors[unit] = factor

                if st.button("Plot"):
                    for unit in geology_units:
                        unit_df = df[df["Geology Unit"] == unit].copy()
                        unit_df["Factored PLI"] = unit_df["Is(50) corrected (MPa)"] * factors[unit]

                        st.subheader(f"Factored PLI & UCS - {unit}")
                        fig = plot_factored_pli_ucs(unit_df, unit,factors[unit])
                        st.plotly_chart(fig, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    



if __name__ == "__main__":
    main()
