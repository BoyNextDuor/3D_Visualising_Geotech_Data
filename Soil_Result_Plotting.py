# -*- coding: utf-8 -*-
"""
Created on Mon May  5 13:47:40 2025

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

    for i, column in enumerate(grouped.columns):
        fig.add_trace(go.Scatter(
            x=grouped.index.astype(float),
            y=grouped[column],
            mode='lines+markers',
            name=column,
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
            gravel = 100 - sample[4.75]
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

    # A-line and U-line functions
    def a_line(ll): return 0.73 * (ll - 20)
    def u_line(ll): return 0.9 * (ll - 8)

    # Calculate points
    A_ll_vals = np.linspace((4 / 0.73) + 20, 100, 200)
    U_ll_vals = np.linspace((7.5 / 0.9) + 8, 100, 200)
    a_line_vals = a_line(A_ll_vals)
    u_line_vals = u_line(U_ll_vals)

    fig = go.Figure()

    # Scatter plot for data points
    fig.add_trace(go.Scatter(
        x=df_atterberg['LL'],
        y=df_atterberg['PI'],
        mode='markers',
        name='Samples',
        marker=dict(color='red', size=8, opacity=0.6)
    ))

    # A-line
    fig.add_trace(go.Scatter(
        x=A_ll_vals, y=a_line_vals,
        mode='lines',
        name='A-line (PI = 0.73(LL - 20))',
        line=dict(color='black')
    ))

    # U-line
    fig.add_trace(go.Scatter(
        x=U_ll_vals, y=u_line_vals,
        mode='lines',
        name='U-line (PI = 0.9(LL - 8))',
        line=dict(color='black', dash='dot')
    ))

    # Horizontal lines for CL and ML
    a_line_cl_x = (7.5 / 0.73) + 20
    a_line_ml_x = (4 / 0.73) + 20
    fig.add_trace(go.Scatter(
        x=[0, a_line_cl_x], y=[7.5, 7.5],
        mode='lines',
        name='CL line (PI=7.5)',
        line=dict(color='black', dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=[0, a_line_ml_x], y=[4, 4],
        mode='lines',
        name='ML line (PI=4)',
        line=dict(color='black', dash='dot')
    ))

    # Vertical lines at LL=35 and LL=50
    fig.add_shape(type='line', x0=35, x1=35,
                  y0=a_line(35), y1=u_line(35),
                  line=dict(color='black'))
    fig.add_shape(type='line', x0=50, x1=50,
                  y0=0, y1=u_line(50),
                  line=dict(color='black'))

    # Text annotations (soil types)
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

    # Axes, layout
    fig.update_layout(
        title=dict(text="Casagrande Plasticity Chart", x=0.5, xanchor='center'),
        xaxis=dict(title="Liquid Limit (%)", range=[0, 100], showgrid=True, mirror=True, showline= True, dtick=10),
        yaxis=dict(title="Plasticity Index (%)", range=[0, 60], showgrid=True, mirror=True, showline= True),
        legend=dict(yanchor="bottom", y=-0.25, orientation="h", bgcolor='rgba(255,255,255,0.7)', borderwidth=1),
        margin=dict(t=40, b=40, l=40, r=40),
        height=600,
        width=800
    )

    st.plotly_chart(fig, use_container_width=True)


def main():
    st.title("Soil Results Plotter")

    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx","xls","xlsm"])
    
    plot_type = st.selectbox("Select plot type:", ["PSD", "Moisture Content","Atterberg Limits"])


    if uploaded_file:
        try:
            if plot_type == "PSD":
                df_psd = pd.read_excel(uploaded_file, sheet_name="PSD")
                geology_units = sorted(df_psd["Geology Unit"].dropna().unique())
                selected_unit = st.selectbox("Select Geology Unit", geology_units)
                fig = plot_psd_for_unit(df_psd, selected_unit)
                st.plotly_chart(fig, use_container_width=True)
            elif plot_type =="Atterberg Limits":
                df_atterberg = pd.read_excel(uploaded_file, sheet_name='Atterberg Limits')
                st.subheader("Cassagrande Chart")
                plot_atterberg_limits_chart_plotly(df_atterberg)
            
            
        except Exception as e:
            st.error(f"Error reading file: {e}")
    
    



if __name__ == "__main__":
    main()







    

