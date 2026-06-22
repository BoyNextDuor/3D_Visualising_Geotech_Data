# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 15:55:25 2026

@author: ZH16329
"""

# fieldwork_planner_app_updated.py

import json
import os
from datetime import datetime, timedelta, date
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Optional mapping dependencies:
# pip install pyproj folium streamlit-folium
try:
    import folium
    from streamlit_folium import st_folium
    from pyproj import Transformer
    MAP_DEPENDENCIES_AVAILABLE = True
except Exception:
    MAP_DEPENDENCIES_AVAILABLE = False
    folium = None
    st_folium = None
    Transformer = None


# --------------------------------------------------
# Default tables
# --------------------------------------------------

def default_rates():
    return pd.DataFrame([
        {"Item": "Drilling", "Unit": "m", "Production_per_day": 20.0, "Daily_Rate": 2500.0},
        {"Item": "Excavator", "Unit": "day", "Production_per_day": 1.0, "Daily_Rate": 1200.0},
        {"Item": "Vacuum Truck", "Unit": "day", "Production_per_day": 1.0, "Daily_Rate": 1800.0},
        {"Item": "Traffic Control", "Unit": "day", "Production_per_day": 1.0, "Daily_Rate": 1500.0},
    ])


def default_subcontractors():
    return pd.DataFrame([
        {"Subcontractor_ID": "DRILLER01", "Subcontractor_Name": "Example Drilling Contractor", "Subcontractor_Type": "Driller", "Notes": "Replace with actual subcontractor."},
        {"Subcontractor_ID": "LAB01", "Subcontractor_Name": "Example Laboratory", "Subcontractor_Type": "Laboratory", "Notes": "Replace with actual laboratory."},
    ])


def default_subcontractor_rates():
    return pd.DataFrame([
        {"Subcontractor_ID": "DRILLER01", "Subcontractor_Name": "Example Drilling Contractor", "Subcontractor_Type": "Driller", "Item": "Drilling", "Unit": "m", "Production_per_day": 20.0, "Daily_Rate": 2500.0, "Unit_Rate": 0.0, "Rate_Type": "Daily", "Notes": "Used for borehole drilling duration/cost."},
        {"Subcontractor_ID": "DRILLER01", "Subcontractor_Name": "Example Drilling Contractor", "Subcontractor_Type": "Driller", "Item": "Traffic Control", "Unit": "day", "Production_per_day": 1.0, "Daily_Rate": 1500.0, "Unit_Rate": 0.0, "Rate_Type": "Daily", "Notes": "Example traffic control allowance."},
        {"Subcontractor_ID": "LAB01", "Subcontractor_Name": "Example Laboratory", "Subcontractor_Type": "Laboratory", "Item": "Moisture Content (AS 1289.2.1.1)", "Unit": "test", "Production_per_day": 0.0, "Daily_Rate": 0.0, "Unit_Rate": 25.0, "Rate_Type": "Unit", "Notes": "Example lab test rate."},
    ])


def default_soil_lab_tests():
    return pd.DataFrame([
        {"Selected": False, "Test": "Moisture Content (AS 1289.2.1.1)", "Rate": 25.0, "Turnaround_days": 3},
        {"Selected": False, "Test": "Liquid Limit (AS 1289.3.1.1)", "Rate": 90.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "Plastic Limit / Plasticity Index (AS 1289.3.2.1 / AS 1289.3.3.1)", "Rate": 90.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "Particle Size Distribution - Sieve (AS 1289.3.6.1)", "Rate": 160.0, "Turnaround_days": 7},
        {"Selected": False, "Test": "Particle Size Distribution - Hydrometer (AS 1289.3.6.3)", "Rate": 220.0, "Turnaround_days": 10},
        {"Selected": False, "Test": "Emerson Class (AS 1289.3.8.1)", "Rate": 90.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "pH Value (AS 1289.4.3.1)", "Rate": 60.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "Standard Compaction (AS 1289.5.1.1)", "Rate": 250.0, "Turnaround_days": 7},
        {"Selected": False, "Test": "CBR - Laboratory Soaked (AS 1289.6.1.1)", "Rate": 450.0, "Turnaround_days": 10},
        {"Selected": False, "Test": "Direct Shear Box (AS 1289.6.2.2)", "Rate": 450.0, "Turnaround_days": 10},
        {"Selected": False, "Test": "Consolidation / Oedometer (AS 1289.6.6.1)", "Rate": 700.0, "Turnaround_days": 14},
        {"Selected": False, "Test": "Shrink-Swell Index (AS 1289.7.1.1)", "Rate": 450.0, "Turnaround_days": 10},
    ])


def default_rock_lab_tests():
    return pd.DataFrame([
        {"Selected": False, "Test": "Point Load Strength Index Is50 (AS 4133)", "Rate": 80.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "Uniaxial Compressive Strength - UCS (AS 4133.4.2.2)", "Rate": 250.0, "Turnaround_days": 7},
        {"Selected": False, "Test": "UCS with Elastic Modulus and Poisson's Ratio (AS 4133)", "Rate": 450.0, "Turnaround_days": 10},
        {"Selected": False, "Test": "Brazilian Tensile Strength (AS 4133)", "Rate": 220.0, "Turnaround_days": 7},
        {"Selected": False, "Test": "Rock Density / Unit Weight (AS 4133)", "Rate": 120.0, "Turnaround_days": 5},
        {"Selected": False, "Test": "Porosity and Water Absorption (AS 4133)", "Rate": 180.0, "Turnaround_days": 7},
        {"Selected": False, "Test": "Slake Durability Index (AS 4133)", "Rate": 300.0, "Turnaround_days": 10},
        {"Selected": False, "Test": "Rock Direct Shear - Discontinuity (AS 4133)", "Rate": 900.0, "Turnaround_days": 14},
    ])


def default_tasks():
    return pd.DataFrame([
        {
            "Order": 1,
            "Task_ID": "PRE01",
            "Task_Type": "Preliminaries",
            "Location_ID": "",
            "Investigation_Type": "Project setup / permits / DBYD / access coordination",
            "Depth_m": 0.0,
            "Duration_days": 3,
            "Depends_On": "",
            "Assigned_Subcontractor": "",
            "Rate_Item": "",
            "Bar_Color": "gray",
            "Easting": 0.0,
            "Northing": 0.0,
            "Access_Notes": "",
        },
        {
            "Order": 2,
            "Task_ID": "BH01",
            "Task_Type": "Drilling",
            "Location_ID": "BH01",
            "Investigation_Type": "Borehole",
            "Depth_m": 20.0,
            "Duration_days": 0,
            "Depends_On": "PRE01",
            "Assigned_Subcontractor": "Example Drilling Contractor",
            "Rate_Item": "Drilling",
            "Bar_Color": "blue",
            "Easting": 0.0,
            "Northing": 0.0,
            "Access_Notes": "",
        },
        {
            "Order": 3,
            "Task_ID": "REP01",
            "Task_Type": "Reporting",
            "Location_ID": "",
            "Investigation_Type": "Factual reporting",
            "Depth_m": 0.0,
            "Duration_days": 5,
            "Depends_On": "BH01",
            "Assigned_Subcontractor": "",
            "Rate_Item": "",
            "Bar_Color": "green",
            "Easting": 0.0,
            "Northing": 0.0,
            "Access_Notes": "",
        },
    ])


NON_PRODUCTION_TASK_TYPES = [
    "Preliminaries",
    "Fieldwork",
    "Laboratory Testing",
    "Reporting",
    "Other",
]


def get_task_type_options(rates_df: pd.DataFrame) -> list[str]:
    """Task Type options are production items plus non-production task types."""
    production_items = []
    if rates_df is not None and not rates_df.empty and "Item" in rates_df.columns:
        production_items = rates_df["Item"].dropna().astype(str).unique().tolist()
    return NON_PRODUCTION_TASK_TYPES + production_items

INVESTIGATION_TYPE_OPTIONS = [
    "Project setup / permits / DBYD / access coordination",
    "Borehole",
    "CPT",
    "Test Pit",
    "DCP",
    "Monitoring Well",
    "Laboratory testing",
    "Factual reporting",
    "Interpretive reporting",
    "Other",
]

COLOR_OPTIONS = [
    "blue",
    "red",
    "green",
    "orange",
    "purple",
    "cyan",
    "magenta",
    "yellow",
    "brown",
    "pink",
    "gray",
    "black",
]


# --------------------------------------------------
# Data validation / normalisation
# --------------------------------------------------

def normalize_tasks_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure task dataframe has all required columns after upload/load/edit."""
    required_defaults = {
        "Order": None,
        "Task_ID": "",
        "Task_Type": "Fieldwork",
        "Location_ID": "",
        "Investigation_Type": "Borehole",
        "Depth_m": 0.0,
        "Duration_days": 0.0,
        "Depends_On": "",
        "Assigned_Subcontractor": "",
        "Rate_Item": "",
        "Bar_Color": "blue",
        "Easting": 0.0,
        "Northing": 0.0,
        "Access_Notes": "",
    }

    df = df.copy()
    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    if df["Order"].isna().any():
        df["Order"] = range(1, len(df) + 1)

    df["Order"] = pd.to_numeric(df["Order"], errors="coerce").fillna(9999).astype(int)
    df["Depth_m"] = pd.to_numeric(df["Depth_m"], errors="coerce").fillna(0.0)
    df["Duration_days"] = pd.to_numeric(df["Duration_days"], errors="coerce").fillna(0.0)
    df["Easting"] = pd.to_numeric(df["Easting"], errors="coerce").fillna(0.0)
    df["Northing"] = pd.to_numeric(df["Northing"], errors="coerce").fillna(0.0)
    if "Estimated_Cost" in df.columns:
        df["Estimated_Cost"] = pd.to_numeric(df["Estimated_Cost"], errors="coerce").fillna(0.0)

    for col in ["Task_ID", "Task_Type", "Location_ID", "Investigation_Type", "Depends_On", "Assigned_Subcontractor", "Rate_Item", "Bar_Color", "Access_Notes"]:
        df[col] = df[col].fillna("").astype(str)

    # Do not force Task_Type here because production items are user-editable in the rates table.
    df.loc[~df["Bar_Color"].isin(COLOR_OPTIONS), "Bar_Color"] = "blue"

    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols].sort_values("Order").reset_index(drop=True)


def normalize_rates_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure production rate table has production and cost columns."""
    if df is None or df.empty:
        df = default_rates()
    else:
        df = df.copy()

    required_defaults = {
        "Item": "",
        "Unit": "day",
        "Production_per_day": 1.0,
        "Daily_Rate": 0.0,
    }

    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    df["Item"] = df["Item"].fillna("").astype(str)
    df["Unit"] = df["Unit"].fillna("").astype(str)
    df["Production_per_day"] = pd.to_numeric(df["Production_per_day"], errors="coerce").fillna(0.0)
    df["Daily_Rate"] = pd.to_numeric(df["Daily_Rate"], errors="coerce").fillna(0.0)

    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols]


def normalize_lab_tests_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure lab test table has selection, rate and turnaround columns."""
    if df is None or df.empty:
        df = pd.DataFrame(columns=["Selected", "Test", "Rate", "Turnaround_days"])
    else:
        df = df.copy()

    required_defaults = {
        "Selected": False,
        "Test": "",
        "Rate": 0.0,
        "Turnaround_days": 0,
    }

    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    df["Selected"] = df["Selected"].fillna(False).astype(bool)
    df["Test"] = df["Test"].fillna("").astype(str)
    df["Rate"] = pd.to_numeric(df["Rate"], errors="coerce").fillna(0.0)
    df["Turnaround_days"] = pd.to_numeric(df["Turnaround_days"], errors="coerce").fillna(0).astype(int)

    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols]


def normalize_subcontractors_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure subcontractor table has consistent columns."""
    if df is None or df.empty:
        df = default_subcontractors()
    else:
        df = df.copy()

    required_defaults = {
        "Subcontractor_ID": "",
        "Subcontractor_Name": "",
        "Subcontractor_Type": "Driller",
        "Notes": "",
    }
    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    for col in required_defaults:
        df[col] = df[col].fillna("").astype(str)

    # Auto-create IDs where user only enters a name.
    for i, row in df.iterrows():
        if not str(row["Subcontractor_ID"]).strip():
            name = str(row["Subcontractor_Name"]).strip() or f"Subcontractor {i+1}"
            prefix = "".join(ch for ch in name.upper() if ch.isalnum())[:8] or "SUB"
            df.at[i, "Subcontractor_ID"] = f"{prefix}{i+1:02d}"
        if not str(row["Subcontractor_Name"]).strip():
            df.at[i, "Subcontractor_Name"] = df.at[i, "Subcontractor_ID"]

    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols].drop_duplicates(subset=["Subcontractor_ID"], keep="last").reset_index(drop=True)


def normalize_subcontractor_rates_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure subcontractor rate schedule has consistent columns."""
    if df is None or df.empty:
        df = default_subcontractor_rates()
    else:
        df = df.copy()

    required_defaults = {
        "Subcontractor_ID": "",
        "Subcontractor_Name": "",
        "Subcontractor_Type": "Driller",
        "Item": "",
        "Unit": "day",
        "Production_per_day": 0.0,
        "Daily_Rate": 0.0,
        "Unit_Rate": 0.0,
        "Rate_Type": "Daily",
        "Notes": "",
    }
    for col, default in required_defaults.items():
        if col not in df.columns:
            df[col] = default

    for col in ["Subcontractor_ID", "Subcontractor_Name", "Subcontractor_Type", "Item", "Unit", "Rate_Type", "Notes"]:
        df[col] = df[col].fillna("").astype(str)
    for col in ["Production_per_day", "Daily_Rate", "Unit_Rate"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    df.loc[~df["Rate_Type"].isin(["Daily", "Unit", "Allowance"]), "Rate_Type"] = "Daily"
    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols].reset_index(drop=True)


def sync_rates_from_subcontractor_rates(subcontractor_rates_df: pd.DataFrame) -> pd.DataFrame:
    """Create the production-rate table used for auto-duration from subcontractor rate items."""
    rates = normalize_subcontractor_rates_df(subcontractor_rates_df)
    production = rates[rates["Production_per_day"] > 0].copy()
    if production.empty:
        return default_rates()

    grouped = (
        production.groupby(["Item", "Unit"], dropna=False)
        .agg({"Production_per_day": "max", "Daily_Rate": "mean"})
        .reset_index()
    )
    return normalize_rates_df(grouped)


def get_subcontractor_options() -> list[str]:
    if "subcontractors_df" not in st.session_state:
        return [""]
    names = st.session_state.subcontractors_df.get("Subcontractor_Name", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    return [""] + names


def get_rate_item_options() -> list[str]:
    if "subcontractor_rates_df" not in st.session_state:
        return [""]
    items = st.session_state.subcontractor_rates_df.get("Item", pd.Series(dtype=str)).dropna().astype(str).unique().tolist()
    return [""] + items


# --------------------------------------------------
# Map helpers
# --------------------------------------------------

GDA2020_MGA_EPSG = {
    "Zone 49": "EPSG:7849",
    "Zone 50": "EPSG:7850",
    "Zone 51": "EPSG:7851",
    "Zone 52": "EPSG:7852",
    "Zone 53": "EPSG:7853",
    "Zone 54": "EPSG:7854",
    "Zone 55": "EPSG:7855",
    "Zone 56": "EPSG:7856",
}


def convert_gda2020_mga_to_latlon(tasks_df: pd.DataFrame, gda_zone: str) -> pd.DataFrame:
    """
    Convert GDA2020 MGA Easting/Northing coordinates to WGS84 latitude/longitude
    for web mapping.

    Input columns required:
    - Easting
    - Northing

    Output columns added:
    - Longitude
    - Latitude
    """
    if not MAP_DEPENDENCIES_AVAILABLE:
        raise ImportError("Mapping dependencies are not installed. Run: pip install pyproj folium streamlit-folium")

    if gda_zone not in GDA2020_MGA_EPSG:
        raise ValueError(f"Unsupported GDA2020 MGA zone: {gda_zone}")

    df = tasks_df.copy()
    df["Easting"] = pd.to_numeric(df.get("Easting", 0), errors="coerce")
    df["Northing"] = pd.to_numeric(df.get("Northing", 0), errors="coerce")
    df = df.dropna(subset=["Easting", "Northing"])

    # Treat 0,0 as not provided.
    df = df[(df["Easting"] != 0) & (df["Northing"] != 0)]

    if df.empty:
        return df

    transformer = Transformer.from_crs(
        GDA2020_MGA_EPSG[gda_zone],
        "EPSG:4326",
        always_xy=True,
    )

    lon_lat = df.apply(
        lambda r: transformer.transform(float(r["Easting"]), float(r["Northing"])),
        axis=1,
    )

    df["Longitude"] = [p[0] for p in lon_lat]
    df["Latitude"] = [p[1] for p in lon_lat]

    return df


def build_test_location_map(map_df: pd.DataFrame):
    """Build a Folium map for test locations."""
    centre_lat = map_df["Latitude"].mean()
    centre_lon = map_df["Longitude"].mean()

    m = folium.Map(
        location=[centre_lat, centre_lon],
        zoom_start=15,
        tiles="OpenStreetMap",
    )

    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Esri World Imagery",
        overlay=False,
        control=True,
    ).add_to(m)

    for _, row in map_df.iterrows():
        task_id = str(row.get("Task_ID", ""))
        location_id = str(row.get("Location_ID", ""))
        investigation_type = str(row.get("Investigation_Type", ""))
        depth = row.get("Depth_m", "")

        label = location_id if location_id else task_id
        popup_html = f"""
        <b>{label}</b><br>
        Task ID: {task_id}<br>
        Investigation: {investigation_type}<br>
        Depth / Qty: {depth}<br>
        Easting: {row.get("Easting", "")}<br>
        Northing: {row.get("Northing", "")}
        """

        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=label,
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# --------------------------------------------------
# Holiday helpers
# --------------------------------------------------

def _observed_date(d: date) -> date:
    """Return observed date when a fixed-date holiday falls on a weekend."""
    if d.weekday() == 5:      # Saturday -> following Monday
        return d + timedelta(days=2)
    if d.weekday() == 6:      # Sunday -> following Monday
        return d + timedelta(days=1)
    return d


def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return nth weekday in a month. Monday=0, Sunday=6."""
    d = date(year, month, 1)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d + timedelta(days=7 * (n - 1))


def _easter_sunday(year: int) -> date:
    """Calculate Easter Sunday using the Gregorian computus."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def fallback_au_public_holidays(year: int, state_code: str) -> dict:
    """
    Built-in fallback holidays so the chart still shades public holidays even
    when the optional `holidays` package is not installed.

    This includes common Australian national public holidays and a small set of
    common state holidays. For project-critical scheduling, install the
    `holidays` package or enter custom holidays manually.
    """
    state_code = (state_code or "VIC").upper()
    easter = _easter_sunday(year)

    h = {
        _observed_date(date(year, 1, 1)): "New Year's Day",
        _observed_date(date(year, 1, 26)): "Australia Day",
        easter - timedelta(days=2): "Good Friday",
        easter + timedelta(days=1): "Easter Monday",
        _observed_date(date(year, 4, 25)): "Anzac Day",
        _observed_date(date(year, 12, 25)): "Christmas Day",
        _observed_date(date(year, 12, 26)): "Boxing Day",
    }

    if state_code == "VIC":
        h[_nth_weekday(year, 3, 0, 2)] = "Labour Day"
        h[_nth_weekday(year, 6, 0, 2)] = "King's Birthday"
        h[_nth_weekday(year, 11, 1, 1)] = "Melbourne Cup Day"
    elif state_code == "NSW":
        h[_nth_weekday(year, 6, 0, 2)] = "King's Birthday"
        h[_nth_weekday(year, 10, 0, 1)] = "Labour Day"
    elif state_code == "QLD":
        h[_nth_weekday(year, 5, 0, 1)] = "Labour Day"
        h[_nth_weekday(year, 10, 0, 1)] = "King's Birthday"
    elif state_code == "SA":
        h[_nth_weekday(year, 3, 0, 2)] = "Adelaide Cup Day"
        h[_nth_weekday(year, 6, 0, 2)] = "King's Birthday"
        h[_nth_weekday(year, 10, 0, 1)] = "Labour Day"
    elif state_code == "WA":
        h[_nth_weekday(year, 3, 0, 1)] = "Labour Day"
        h[_nth_weekday(year, 9, 0, 4)] = "King's Birthday"
    elif state_code == "TAS":
        h[_nth_weekday(year, 3, 0, 2)] = "Eight Hours Day"
        h[_nth_weekday(year, 6, 0, 2)] = "King's Birthday"
    elif state_code in ["ACT", "NT"]:
        h[_nth_weekday(year, 3, 0, 2)] = "Canberra Day / Eight Hours Day"
        h[_nth_weekday(year, 6, 0, 2)] = "King's Birthday"

    return h


def parse_custom_holidays(custom_holidays_text: str) -> dict:
    """
    Parse user-entered public holidays.

    Accepted line formats:
    - 2026-12-25
    - 25/12/2026
    - 25/12/2026, Christmas Day
    - 2026-12-25, Christmas Day
    """
    holidays_dict = {}

    if not custom_holidays_text:
        return holidays_dict

    for raw_line in custom_holidays_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if "," in line:
            date_part, name_part = line.split(",", 1)
            holiday_name = name_part.strip() or "Public Holiday"
        else:
            date_part = line
            holiday_name = "Public Holiday"

        parsed_date = pd.to_datetime(date_part.strip(), dayfirst=True, errors="coerce")
        if pd.notna(parsed_date):
            holidays_dict[parsed_date.date()] = holiday_name

    return holidays_dict


def get_public_holidays(start_date, finish_date, state_code: str, custom_holidays_text: str) -> dict:
    """Return public holidays as {date: name}."""
    chart_start = pd.to_datetime(start_date).date()
    chart_finish = pd.to_datetime(finish_date).date()
    year_list = list(range(chart_start.year, chart_finish.year + 1))

    holidays_dict = {}

    try:
        import holidays  # optional dependency: pip install holidays
        au_holidays = holidays.AU(subdiv=state_code, years=year_list)
        for holiday_date, holiday_name in au_holidays.items():
            holidays_dict[holiday_date] = holiday_name
    except Exception:
        # Built-in fallback so red shading still works without installing holidays.
        for y in year_list:
            holidays_dict.update(fallback_au_public_holidays(y, state_code))

    # User-entered holidays override/add to the automatic list.
    holidays_dict.update(parse_custom_holidays(custom_holidays_text))

    return {
        h_date: h_name
        for h_date, h_name in holidays_dict.items()
        if chart_start <= h_date <= chart_finish
    }

# --------------------------------------------------
# Scheduling logic
# --------------------------------------------------

def is_working_day(current_date, work_weekends):
    return True if work_weekends else current_date.weekday() < 5


def next_working_day(current_date, work_weekends):
    while not is_working_day(current_date, work_weekends):
        current_date += timedelta(days=1)
    return current_date


def add_working_days(start_date, duration_days, work_weekends):
    current = start_date
    added = 0

    while added < duration_days:
        if is_working_day(current, work_weekends):
            added += 1
        if added < duration_days:
            current += timedelta(days=1)

    return current


def estimate_task_duration(task, rates_df):
    task_type = str(task.get("Task_Type", "")).strip()
    manual_duration = float(task.get("Duration_days", 0) or 0)

    # If user specifies duration, use it directly.
    if manual_duration > 0:
        return max(1, int(round(manual_duration)))

    # Non-production tasks, including "Fieldwork", must use a manual duration.
    if task_type in NON_PRODUCTION_TASK_TYPES:
        raise ValueError(
            f"{task['Task_ID']}: Duration_days must be specified for non-production task type '{task_type}'."
        )

    # If duration is blank/0, Task_Type must match a production item.
    depth = float(task.get("Depth_m", 0) or 0)

    if depth <= 0:
        raise ValueError(
            f"{task['Task_ID']}: Depth_m must be greater than 0 when Duration_days is blank or 0."
        )

    match = rates_df[rates_df["Item"].astype(str).str.lower() == task_type.lower()]

    if match.empty:
        raise ValueError(
            f"{task['Task_ID']}: Task_Type '{task_type}' is not a production item. "
            "Either select a production item from Task_Type or enter Duration_days manually."
        )

    production = float(match.iloc[0]["Production_per_day"])

    if production <= 0:
        raise ValueError(f"{task['Task_ID']}: Production_per_day must be greater than 0.")

    return max(1, int(round(depth / production + 0.499)))


def generate_program(tasks_df, rates_df, start_date, work_weekends):
    tasks = normalize_tasks_df(tasks_df)

    scheduled = {}
    rows = []

    for _, task in tasks.iterrows():
        task_id = str(task["Task_ID"]).strip()
        depends_on = str(task.get("Depends_On", "")).strip()

        if not task_id:
            raise ValueError("Every task must have a Task_ID.")

        if task_id in scheduled:
            raise ValueError(f"Duplicate Task_ID found: {task_id}.")

        duration = estimate_task_duration(task, rates_df)

        if depends_on and depends_on not in tasks["Task_ID"].astype(str).values:
            raise ValueError(f"{task_id}: Depends_On references unknown Task_ID '{depends_on}'.")

        if depends_on and depends_on in scheduled:
            earliest_start = scheduled[depends_on]["Finish_Actual"] + timedelta(days=1)
        elif depends_on and depends_on not in scheduled:
            raise ValueError(
                f"{task_id}: Depends_On '{depends_on}' has not been scheduled yet. "
                f"Move the dependent task below its prerequisite task."
            )
        else:
            earliest_start = start_date

        # Independent tasks start on the project start date.
        # Only tasks with Depends_On are delayed by their prerequisite.
        current_start = next_working_day(earliest_start, work_weekends)

        finish_actual = add_working_days(current_start, duration, work_weekends)
        finish_plot = finish_actual + timedelta(days=1)

        scheduled[task_id] = {
            "Start": current_start,
            "Finish_Actual": finish_actual,
            "Finish_Plot": finish_plot,
        }

        rows.append({
            "Order": int(task["Order"]),
            "Task_ID": task_id,
            "Task_Type": task["Task_Type"],
            "Location_ID": task["Location_ID"],
            "Investigation_Type": task["Investigation_Type"],
            "Depth_m": task["Depth_m"],
            "Duration_days": duration,
            "Depends_On": depends_on,
            "Assigned_Subcontractor": task.get("Assigned_Subcontractor", ""),
            "Rate_Item": task.get("Rate_Item", ""),
            "Start": current_start,
            "Finish": finish_plot,
            "Bar_Color": task.get("Bar_Color", "blue"),
            "Easting": task.get("Easting", 0.0),
            "Northing": task.get("Northing", 0.0),
            "Access_Notes": task["Access_Notes"],
        })

    return pd.DataFrame(rows)


# --------------------------------------------------
# Save/export helpers
# --------------------------------------------------

def dataframe_to_excel_bytes(dfs):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()


def estimate_program_cost(program_df: pd.DataFrame, rates_df: pd.DataFrame, soil_lab_df: pd.DataFrame, rock_lab_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Estimate costs using daily rates for scheduled production tasks and selected lab test rates.

    Fieldwork cost is calculated as Duration_days × Daily_Rate where Task_Type matches
    an item in the production rates table. Non-production task types will show zero
    unless the user adds a matching item to the production rates table.
    """
    rates = normalize_rates_df(rates_df)
    rate_lookup = {
        str(row["Item"]).strip().lower(): float(row.get("Daily_Rate", 0.0) or 0.0)
        for _, row in rates.iterrows()
    }

    program_rows = []
    if program_df is not None and not program_df.empty:
        for _, row in program_df.iterrows():
            task_type = str(row.get("Task_Type", "")).strip()
            duration = float(row.get("Duration_days", 0) or 0)
            daily_rate = rate_lookup.get(task_type.lower(), 0.0)
            total = duration * daily_rate
            program_rows.append({
                "Cost_Type": "Program Task",
                "Task_ID": row.get("Task_ID", ""),
                "Location_ID": row.get("Location_ID", ""),
                "Item": task_type,
                "Quantity": duration,
                "Unit": "day",
                "Rate": daily_rate,
                "Total_Cost": total,
            })

    lab_rows = []
    for lab_type, lab_df in [("Soil Lab", soil_lab_df), ("Rock Lab", rock_lab_df)]:
        lab = normalize_lab_tests_df(lab_df)
        selected = lab[lab["Selected"] == True].copy()
        for _, row in selected.iterrows():
            rate = float(row.get("Rate", 0.0) or 0.0)
            lab_rows.append({
                "Cost_Type": lab_type,
                "Task_ID": "",
                "Location_ID": "",
                "Item": row.get("Test", ""),
                "Quantity": 1,
                "Unit": "test",
                "Rate": rate,
                "Total_Cost": rate,
            })

    cost_df = pd.DataFrame(program_rows + lab_rows)
    if cost_df.empty:
        cost_df = pd.DataFrame(columns=["Cost_Type", "Task_ID", "Location_ID", "Item", "Quantity", "Unit", "Rate", "Total_Cost"])

    summary_df = (
        cost_df.groupby("Cost_Type", dropna=False)["Total_Cost"]
        .sum()
        .reset_index()
        .sort_values("Cost_Type")
    ) if not cost_df.empty else pd.DataFrame(columns=["Cost_Type", "Total_Cost"])

    return cost_df, summary_df


def save_project_json(project_data):
    return json.dumps(project_data, indent=2, default=str).encode("utf-8")


def load_project_json(uploaded_file):
    return json.load(uploaded_file)


def move_row(df, selected_task_id, direction):
    df = normalize_tasks_df(df)

    idx_list = df.index[df["Task_ID"] == selected_task_id].tolist()
    if not idx_list:
        return df

    idx = idx_list[0]
    new_idx = idx - 1 if direction == "up" else idx + 1

    if new_idx < 0 or new_idx >= len(df):
        return df

    df.iloc[[idx, new_idx]] = df.iloc[[new_idx, idx]].values
    df["Order"] = range(1, len(df) + 1)

    return df



# --------------------------------------------------
# Rate schedule import / AI extraction helpers
# --------------------------------------------------

def _strip_json_code_fence(text: str) -> str:
    text = (text or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    return text.strip()


def extract_rate_schedule_with_ai(uploaded_files, model_name: str = "gpt-4.1-mini") -> dict:
    """Use OpenAI to extract contractor and lab rates from uploaded rate schedules.

    Returns a dictionary with optional keys:
    - fieldwork_production_rates: Item, Unit, Production_per_day, Daily_Rate
    - soil_lab_tests: Test, Rate, Turnaround_days
    - rock_lab_tests: Test, Rate, Turnaround_days
    """
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to Streamlit secrets or an environment variable.")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("The openai package is not installed. Run: pip install openai") from exc

    if not uploaded_files:
        raise ValueError("Please upload at least one subcontractor rate schedule.")

    client = OpenAI(api_key=api_key)
    content = [{
        "type": "input_text",
        "text": (
            "Extract rates from the attached geotechnical subcontractor/laboratory rate schedule. "
            "Return JSON only with this structure: "
            "{\"subcontractors\":[{\"Subcontractor_ID\":str,\"Subcontractor_Name\":str,\"Subcontractor_Type\":str,\"Notes\":str}],"
            "\"subcontractor_rate_items\":[{\"Subcontractor_ID\":str,\"Subcontractor_Name\":str,\"Subcontractor_Type\":str,\"Item\":str,\"Unit\":str,\"Production_per_day\":number|null,\"Daily_Rate\":number|null,\"Unit_Rate\":number|null,\"Rate_Type\":str,\"Notes\":str}],"
            "\"fieldwork_production_rates\":[{\"Item\":str,\"Unit\":str,\"Production_per_day\":number|null,\"Daily_Rate\":number|null}],"
            "\"soil_lab_tests\":[{\"Test\":str,\"Rate\":number|null,\"Turnaround_days\":number|null}],"
            "\"rock_lab_tests\":[{\"Test\":str,\"Rate\":number|null,\"Turnaround_days\":number|null}]} "
            "Use null where a value is not stated. Do not invent rates. "
            "Classify drilling, CPT, test pit, excavator, traffic control and similar items as fieldwork_production_rates. "
            "Classify AS 1289 soil tests as soil_lab_tests and AS 4133 rock tests as rock_lab_tests."
        ),
    }]

    file_ids = []
    try:
        for uploaded_file in uploaded_files:
            uploaded_file.seek(0)
            created_file = client.files.create(
                file=(uploaded_file.name, uploaded_file.read()),
                purpose="assistants",
            )
            file_ids.append(created_file.id)
            content.append({"type": "input_file", "file_id": created_file.id})

        response = client.responses.create(
            model=model_name,
            input=[{"role": "user", "content": content}],
        )
        raw_text = _strip_json_code_fence(response.output_text)
        return json.loads(raw_text)
    finally:
        # Deleting uploaded files is best-effort only.
        for file_id in file_ids:
            try:
                client.files.delete(file_id)
            except Exception:
                pass


def apply_extracted_rates(extracted: dict, replace_existing: bool = False):
    """Apply extracted AI rates to Streamlit session-state subcontractor/rate tables."""
    subcontractors = pd.DataFrame(extracted.get("subcontractors", []) or [])
    sub_rates = pd.DataFrame(extracted.get("subcontractor_rate_items", []) or [])
    fieldwork = pd.DataFrame(extracted.get("fieldwork_production_rates", []) or [])
    soil = pd.DataFrame(extracted.get("soil_lab_tests", []) or [])
    rock = pd.DataFrame(extracted.get("rock_lab_tests", []) or [])

    if not subcontractors.empty:
        subcontractors = normalize_subcontractors_df(subcontractors)
        if replace_existing:
            st.session_state.subcontractors_df = subcontractors
        else:
            st.session_state.subcontractors_df = normalize_subcontractors_df(pd.concat([st.session_state.subcontractors_df, subcontractors], ignore_index=True))

    if not sub_rates.empty:
        sub_rates = normalize_subcontractor_rates_df(sub_rates)
        if replace_existing:
            st.session_state.subcontractor_rates_df = sub_rates
        else:
            st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(pd.concat([st.session_state.subcontractor_rates_df, sub_rates], ignore_index=True))

    # Backward compatibility: if AI only returns fieldwork_production_rates, place them under an AI extracted subcontractor.
    if not fieldwork.empty:
        fieldwork = normalize_rates_df(fieldwork)
        fallback_sub = pd.DataFrame([{
            "Subcontractor_ID": "AI_EXTRACTED",
            "Subcontractor_Name": "AI Extracted Rates",
            "Subcontractor_Type": "Mixed / Unknown",
            "Notes": "Created from extracted fieldwork_production_rates.",
        }])
        fw_items = fieldwork.rename(columns={"Daily_Rate": "Daily_Rate"}).copy()
        fw_items["Subcontractor_ID"] = "AI_EXTRACTED"
        fw_items["Subcontractor_Name"] = "AI Extracted Rates"
        fw_items["Subcontractor_Type"] = "Mixed / Unknown"
        fw_items["Unit_Rate"] = 0.0
        fw_items["Rate_Type"] = "Daily"
        fw_items["Notes"] = "AI extracted production item."
        st.session_state.subcontractors_df = normalize_subcontractors_df(pd.concat([st.session_state.subcontractors_df, fallback_sub], ignore_index=True))
        st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(pd.concat([st.session_state.subcontractor_rates_df, fw_items], ignore_index=True))

    if not soil.empty:
        soil["Selected"] = False
        soil = normalize_lab_tests_df(soil)
        if replace_existing:
            st.session_state.soil_lab_df = soil
        else:
            st.session_state.soil_lab_df = normalize_lab_tests_df(pd.concat([st.session_state.soil_lab_df, soil], ignore_index=True))

    if not rock.empty:
        rock["Selected"] = False
        rock = normalize_lab_tests_df(rock)
        if replace_existing:
            st.session_state.rock_lab_df = rock
        else:
            st.session_state.rock_lab_df = normalize_lab_tests_df(pd.concat([st.session_state.rock_lab_df, rock], ignore_index=True))

    # Keep legacy production table in sync for auto-duration dropdowns.
    st.session_state.rates_df = sync_rates_from_subcontractor_rates(st.session_state.subcontractor_rates_df)

# --------------------------------------------------
# AI guidance helpers
# --------------------------------------------------

def get_openai_api_key():
    """Read API key from Streamlit secrets or environment variable."""
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    return os.getenv("OPENAI_API_KEY", "")


def dataframe_to_context_text(df: pd.DataFrame, max_rows: int = 200) -> str:
    """Convert dataframe to compact CSV-like text for AI context."""
    if df is None or df.empty:
        return "No data provided."
    shown = df.head(max_rows).copy()
    return shown.to_csv(index=False)


def build_ai_context(project_info, tasks_df, rates_df, soil_lab_df, rock_lab_df, program_df) -> str:
    """Build a traceable context package for the AI assistant."""
    return f"""
You are assisting with geotechnical fieldwork planning.

Project information:
{json.dumps(project_info, indent=2, default=str)}

Production rates used for duration calculation:
{dataframe_to_context_text(rates_df)}

Subcontractor rate schedule:
{dataframe_to_context_text(st.session_state.get("subcontractor_rates_df", pd.DataFrame()))}

Investigation tasks:
{dataframe_to_context_text(tasks_df)}

Selected soil laboratory testing:
{dataframe_to_context_text(soil_lab_df[soil_lab_df.get('Selected', False) == True] if isinstance(soil_lab_df, pd.DataFrame) and 'Selected' in soil_lab_df.columns else soil_lab_df)}

Selected rock laboratory testing:
{dataframe_to_context_text(rock_lab_df[rock_lab_df.get('Selected', False) == True] if isinstance(rock_lab_df, pd.DataFrame) and 'Selected' in rock_lab_df.columns else rock_lab_df)}

Generated program:
{dataframe_to_context_text(program_df)}

Cost estimate:
{dataframe_to_context_text(st.session_state.cost_df if "cost_df" in st.session_state else pd.DataFrame())}

Important rules:
- Treat the rule-based program as the current baseline.
- Do not invent missing access constraints, subcontractor availability, or test quantities.
- Clearly state any assumptions.
- Focus on sequencing, dependencies, likely clashes, weekend/public holiday impacts, production-rate reasonableness, and practical fieldwork risks.
- If the program looks unrealistic, explain why and suggest what the user should check.
- Do not directly modify the program table. Provide guidance only unless the user explicitly asks for a revised table.
""".strip()


def ask_ai_for_program_guidance(
    user_question: str,
    project_info: dict,
    tasks_df: pd.DataFrame,
    rates_df: pd.DataFrame,
    soil_lab_df: pd.DataFrame,
    rock_lab_df: pd.DataFrame,
    program_df: pd.DataFrame,
    model_name: str,
) -> str:
    """Send current planning context to OpenAI and return guidance text."""
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. Add it to .streamlit/secrets.toml or as an environment variable."
        )

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("The openai package is not installed. Run: pip install openai") from exc

    client = OpenAI(api_key=api_key)
    context = build_ai_context(project_info, tasks_df, rates_df, soil_lab_df, rock_lab_df, program_df)

    response = client.responses.create(
        model=model_name,
        instructions=(
            "You are a practical geotechnical fieldwork planning assistant. "
            "Give concise, engineering-focused planning guidance. "
            "Be transparent about uncertainty and missing information."
        ),
        input=f"{context}\n\nUser question:\n{user_question}",
    )

    return response.output_text



# --------------------------------------------------
# AI preliminary program helpers
# --------------------------------------------------

AI_PROGRAM_COLUMNS = [
    "Order", "Task_ID", "Task_Type", "Location_ID", "Investigation_Type",
    "Depth_m", "Duration_days", "Depends_On", "Assigned_Subcontractor", "Rate_Item", "Start", "Finish",
    "Bar_Color", "Easting", "Northing", "Access_Notes",
    "Planning_Notes", "Traffic_Management", "Accommodation_Notes",
    "Distance_Notes", "Overhead_Spotter", "Services_Risk", "Groundwater_Risk", "Estimated_Cost",
]


def normalize_ai_program_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise AI/program table so it can be edited, plotted and exported."""
    if df is None or df.empty:
        return pd.DataFrame(columns=AI_PROGRAM_COLUMNS)

    df = df.copy()
    defaults = {
        "Order": None,
        "Task_ID": "",
        "Task_Type": "Fieldwork",
        "Location_ID": "",
        "Investigation_Type": "",
        "Depth_m": 0.0,
        "Duration_days": 1,
        "Depends_On": "",
        "Assigned_Subcontractor": "",
        "Rate_Item": "",
        "Start": None,
        "Finish": None,
        "Bar_Color": "blue",
        "Easting": 0.0,
        "Northing": 0.0,
        "Access_Notes": "",
        "Planning_Notes": "",
        "Traffic_Management": "",
        "Accommodation_Notes": "",
        "Distance_Notes": "",
        "Overhead_Spotter": "",
        "Services_Risk": "",
        "Groundwater_Risk": "",
        "Estimated_Cost": 0.0,
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df[col] = default

    if df["Order"].isna().any():
        df["Order"] = range(1, len(df) + 1)

    df["Order"] = pd.to_numeric(df["Order"], errors="coerce").fillna(9999).astype(int)
    df["Depth_m"] = pd.to_numeric(df["Depth_m"], errors="coerce").fillna(0.0)
    df["Duration_days"] = pd.to_numeric(df["Duration_days"], errors="coerce").fillna(1).astype(int)
    df["Easting"] = pd.to_numeric(df["Easting"], errors="coerce").fillna(0.0)
    df["Northing"] = pd.to_numeric(df["Northing"], errors="coerce").fillna(0.0)
    if "Estimated_Cost" in df.columns:
        df["Estimated_Cost"] = pd.to_numeric(df["Estimated_Cost"], errors="coerce").fillna(0.0)

    for col in [
        "Task_ID", "Task_Type", "Location_ID", "Investigation_Type", "Depends_On", "Assigned_Subcontractor", "Rate_Item",
        "Bar_Color", "Access_Notes", "Planning_Notes", "Traffic_Management",
        "Accommodation_Notes", "Distance_Notes", "Overhead_Spotter", "Services_Risk", "Groundwater_Risk",
    ]:
        df[col] = df[col].fillna("").astype(str)

    df.loc[~df["Bar_Color"].isin(COLOR_OPTIONS), "Bar_Color"] = "blue"
    df["Start"] = pd.to_datetime(df["Start"], errors="coerce")
    df["Finish"] = pd.to_datetime(df["Finish"], errors="coerce")

    # If AI did not provide dates, derive them from the project start date and duration.
    try:
        default_start = pd.to_datetime(st.session_state.project_info.get("start_date", date.today()))
    except Exception:
        default_start = pd.to_datetime(date.today())

    for idx, row in df.iterrows():
        if pd.isna(row["Start"]):
            df.at[idx, "Start"] = default_start
        if pd.isna(row["Finish"]):
            df.at[idx, "Finish"] = pd.to_datetime(df.at[idx, "Start"]) + pd.Timedelta(days=max(int(row["Duration_days"]), 1))

    ordered_cols = AI_PROGRAM_COLUMNS
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols].sort_values("Order").reset_index(drop=True)


def read_tabular_upload(uploaded_file) -> pd.DataFrame:
    """Read a CSV/XLSX upload into a dataframe."""
    if uploaded_file is None:
        return pd.DataFrame()
    name = uploaded_file.name.lower()
    uploaded_file.seek(0)
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    return pd.read_excel(uploaded_file)


def build_distance_summary(map_df: pd.DataFrame) -> str:
    """Create a simple pairwise distance summary from converted coordinates."""
    if map_df is None or map_df.empty or not {"Latitude", "Longitude"}.issubset(map_df.columns):
        return "No coordinate-derived distance summary available."
    try:
        from math import radians, sin, cos, sqrt, atan2
        rows = []
        pts = map_df[["Task_ID", "Location_ID", "Latitude", "Longitude"]].copy().reset_index(drop=True)
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                lat1, lon1 = radians(float(pts.loc[i, "Latitude"])), radians(float(pts.loc[i, "Longitude"]))
                lat2, lon2 = radians(float(pts.loc[j, "Latitude"])), radians(float(pts.loc[j, "Longitude"]))
                dlat, dlon = lat2 - lat1, lon2 - lon1
                a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
                c = 2 * atan2(sqrt(a), sqrt(1 - a))
                dist_m = 6371000 * c
                a_name = pts.loc[i, "Location_ID"] or pts.loc[i, "Task_ID"]
                b_name = pts.loc[j, "Location_ID"] or pts.loc[j, "Task_ID"]
                rows.append({"From": a_name, "To": b_name, "Approx_Distance_m": round(dist_m, 1)})
        return pd.DataFrame(rows).to_csv(index=False) if rows else "Only one mapped location available."
    except Exception as exc:
        return f"Distance summary could not be calculated: {exc}"


def build_ai_preliminary_program_context(project_info, tasks_df, rates_df, soil_lab_df, rock_lab_df, map_df, borehole_db_df) -> str:
    distance_summary = build_distance_summary(map_df)
    return f"""
You are preparing a preliminary geotechnical fieldwork program.

Project information and constraints:
{json.dumps(project_info, indent=2, default=str)}

Production rates used for duration calculation:
{dataframe_to_context_text(rates_df)}

Subcontractor rate schedule:
{dataframe_to_context_text(st.session_state.get("subcontractor_rates_df", pd.DataFrame()))}

Investigation tasks:
{dataframe_to_context_text(tasks_df)}

Selected soil laboratory testing:
{dataframe_to_context_text(soil_lab_df[soil_lab_df.get('Selected', False) == True] if isinstance(soil_lab_df, pd.DataFrame) and 'Selected' in soil_lab_df.columns else soil_lab_df)}

Selected rock laboratory testing:
{dataframe_to_context_text(rock_lab_df[rock_lab_df.get('Selected', False) == True] if isinstance(rock_lab_df, pd.DataFrame) and 'Selected' in rock_lab_df.columns else rock_lab_df)}

Converted test location coordinates:
{dataframe_to_context_text(map_df)}

Approximate distance between test locations:
{distance_summary}

Imported borehole / ground model database:
{dataframe_to_context_text(borehole_db_df, max_rows=150)}

Key matters to consider:
- Distance from live traffic and whether traffic management is likely required.
- Distance from nearest accommodation if staying away from home base is required.
- Distance between test locations and whether grouping by area would improve efficiency.
- Whether an overhead spotter may be required.
- Density and criticality of underground services based on BYDA information.
- Access constraints, restricted working hours, permits, inductions, and public holidays.
- Anticipated ground and groundwater conditions from the borehole database where available.
- Assign a suitable subcontractor and rate item from the subcontractor rate schedule where a task clearly relates to a listed item.
- Use the listed rates to estimate a rough cost for each task where possible. If no suitable rate item is available, leave Assigned_Subcontractor, Rate_Item and Estimated_Cost blank or 0.

Return JSON only, with this structure:
{{
  "preliminary_program": [
    {{
      "Order": 1,
      "Task_ID": "PRE01",
      "Task_Type": "Preliminaries",
      "Location_ID": "",
      "Investigation_Type": "Project setup / permits / BYDA / access coordination",
      "Depth_m": 0,
      "Duration_days": 2,
      "Depends_On": "",
      "Start": "YYYY-MM-DD",
      "Finish": "YYYY-MM-DD",
      "Bar_Color": "gray",
      "Easting": 0,
      "Northing": 0,
      "Access_Notes": "",
      "Planning_Notes": "",
      "Traffic_Management": "",
      "Accommodation_Notes": "",
      "Distance_Notes": "",
      "Overhead_Spotter": "",
      "Services_Risk": "",
      "Groundwater_Risk": "",
      "Assigned_Subcontractor": "",
      "Rate_Item": "",
      "Estimated_Cost": 0
    }}
  ],
  "general_comments": "short summary"
}}
Do not invent missing values. If something is unknown, state it as unknown in the relevant notes.
""".strip()


def generate_ai_preliminary_program(byda_files, model_name: str, borehole_db_df: pd.DataFrame) -> dict:
    """Ask AI for a preliminary program table using project/task/location inputs and optional BYDA files."""
    api_key = get_openai_api_key()
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set. Add it to Streamlit secrets or an environment variable.")
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("The openai package is not installed. Run: pip install openai") from exc

    selected_zone = st.session_state.project_info.get("gda2020_mga_zone", "Zone 55")
    try:
        map_df = convert_gda2020_mga_to_latlon(st.session_state.tasks_df, selected_zone) if MAP_DEPENDENCIES_AVAILABLE else pd.DataFrame()
    except Exception:
        map_df = pd.DataFrame()

    prompt = build_ai_preliminary_program_context(
        st.session_state.project_info,
        st.session_state.tasks_df,
        st.session_state.rates_df,
        st.session_state.soil_lab_df,
        st.session_state.rock_lab_df,
        map_df,
        borehole_db_df,
    )

    client = OpenAI(api_key=api_key)
    content = [{"type": "input_text", "text": prompt}]
    file_ids = []
    try:
        for uploaded_file in byda_files or []:
            uploaded_file.seek(0)
            created_file = client.files.create(
                file=(uploaded_file.name, uploaded_file.read()),
                purpose="assistants",
            )
            file_ids.append(created_file.id)
            content.append({"type": "input_file", "file_id": created_file.id})

        response = client.responses.create(
            model=model_name,
            input=[{"role": "user", "content": content}],
        )
        raw_text = _strip_json_code_fence(response.output_text)
        return json.loads(raw_text)
    finally:
        for file_id in file_ids:
            try:
                client.files.delete(file_id)
            except Exception:
                pass


# Override map builder with reliable circle symbols and labels.
def build_test_location_map(map_df: pd.DataFrame):
    """Build a Folium map for test locations using reliable CircleMarker symbols."""
    centre_lat = map_df["Latitude"].mean()
    centre_lon = map_df["Longitude"].mean()

    m = folium.Map(location=[centre_lat, centre_lon], zoom_start=15, tiles="OpenStreetMap")
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Esri World Imagery",
        name="Esri World Imagery",
        overlay=False,
        control=True,
    ).add_to(m)

    symbol_color = {
        "Borehole": "blue",
        "CPT": "red",
        "Test Pit": "brown",
        "DCP": "purple",
        "Monitoring Well": "green",
    }

    for _, row in map_df.iterrows():
        task_id = str(row.get("Task_ID", ""))
        location_id = str(row.get("Location_ID", ""))
        investigation_type = str(row.get("Investigation_Type", ""))
        depth = row.get("Depth_m", "")
        label = location_id if location_id else task_id
        marker_color = symbol_color.get(investigation_type, "gray")

        popup_html = f"""
        <b>{label}</b><br>
        Task ID: {task_id}<br>
        Investigation: {investigation_type}<br>
        Depth / Qty: {depth}<br>
        Easting: {row.get('Easting', '')}<br>
        Northing: {row.get('Northing', '')}
        """

        folium.CircleMarker(
            location=[row["Latitude"], row["Longitude"]],
            radius=6,
            color=marker_color,
            weight=2,
            fill=True,
            fill_color=marker_color,
            fill_opacity=0.9,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=label,
        ).add_to(m)

        folium.Marker(
            [row["Latitude"], row["Longitude"]],
            icon=folium.DivIcon(
                html=f"""
                <div style="
                    font-size:10pt;
                    font-weight:bold;
                    color:black;
                    background-color:white;
                    border:1px solid black;
                    border-radius:3px;
                    padding:2px;
                    white-space:nowrap;
                    transform:translate(10px,-8px);
                ">{label}</div>
                """
            ),
        ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# --------------------------------------------------
# Streamlit app
# --------------------------------------------------

st.set_page_config(page_title="Fieldwork Planner", layout="wide")
st.title("Fieldwork Planning Web Application")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Project Setup",
    "2. Subcontractor Rate Schedule",
    "3. Investigation Tasks",
    "4. AI Preliminary Program",
    "5. Program, Gantt & Test Location Plan",
    "6. Export / Save",
])

if "project_info" not in st.session_state:
    st.session_state.project_info = {}
if "rates_df" not in st.session_state:
    st.session_state.rates_df = default_rates()
if "subcontractors_df" not in st.session_state:
    st.session_state.subcontractors_df = default_subcontractors()
if "subcontractor_rates_df" not in st.session_state:
    st.session_state.subcontractor_rates_df = default_subcontractor_rates()
if "soil_lab_df" not in st.session_state:
    st.session_state.soil_lab_df = default_soil_lab_tests()
if "rock_lab_df" not in st.session_state:
    st.session_state.rock_lab_df = default_rock_lab_tests()
if "tasks_df" not in st.session_state:
    st.session_state.tasks_df = default_tasks()
if "program_df" not in st.session_state:
    st.session_state.program_df = pd.DataFrame()
if "ai_program_df" not in st.session_state:
    st.session_state.ai_program_df = pd.DataFrame()
if "ai_program_comments" not in st.session_state:
    st.session_state.ai_program_comments = ""
if "cost_df" not in st.session_state:
    st.session_state.cost_df = pd.DataFrame()
if "cost_summary_df" not in st.session_state:
    st.session_state.cost_summary_df = pd.DataFrame()

st.session_state.subcontractors_df = normalize_subcontractors_df(st.session_state.subcontractors_df)
st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(st.session_state.subcontractor_rates_df)
st.session_state.rates_df = sync_rates_from_subcontractor_rates(st.session_state.subcontractor_rates_df)
st.session_state.soil_lab_df = normalize_lab_tests_df(st.session_state.soil_lab_df)
st.session_state.rock_lab_df = normalize_lab_tests_df(st.session_state.rock_lab_df)
st.session_state.tasks_df = normalize_tasks_df(st.session_state.tasks_df)


# --------------------------------------------------
# Tab 1: Project setup
# --------------------------------------------------

with tab1:
    st.header("Project Initialization")

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("Project Name", value=st.session_state.project_info.get("project_name", ""))
        project_number = st.text_input("Project Number", value=st.session_state.project_info.get("project_number", ""))
        start_date = st.date_input("Project Start Date", value=pd.to_datetime(st.session_state.project_info.get("start_date", date.today())).date())
        working_hours = st.number_input("Working Hours per Day", min_value=1.0, max_value=24.0, value=float(st.session_state.project_info.get("working_hours", 8.0)))
        work_weekends = st.checkbox("Allow Weekend Work", value=bool(st.session_state.project_info.get("work_weekends", False)))
        internal_fieldwork_resources = st.number_input(
            "Internal Fieldwork Resources Available",
            min_value=0,
            step=1,
            value=int(st.session_state.project_info.get("internal_fieldwork_resources", 1)),
            help="Number of internal field engineers/field staff available for the program.",
        )
        external_fieldwork_resources = st.number_input(
            "External Fieldwork Resources / Crews Available",
            min_value=0,
            step=1,
            value=int(st.session_state.project_info.get("external_fieldwork_resources", 1)),
            help="Number of subcontractor field crews available, e.g. drill rigs, CPT rigs or test pit crews.",
        )

    with col2:
        shade_public_holidays = st.checkbox(
            "Shade Public Holidays on Gantt Chart",
            value=bool(st.session_state.project_info.get("shade_public_holidays", True)),
        )
        public_holiday_state = st.selectbox(
            "Australian Public Holiday State/Territory",
            ["VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"],
            index=["VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"].index(st.session_state.project_info.get("public_holiday_state", "VIC")),
        )
        gda2020_mga_zone = st.selectbox(
            "GDA2020 MGA Zone for Test Location Map",
            list(GDA2020_MGA_EPSG.keys()),
            index=list(GDA2020_MGA_EPSG.keys()).index(st.session_state.project_info.get("gda2020_mga_zone", "Zone 55")),
        )
        byda_plan_status = st.selectbox(
            "BYDA Plans / Utility Information Status",
            ["Not available", "Requested", "Received - low service density", "Received - moderate service density", "Received - high service density", "Received - review required"],
            index=["Not available", "Requested", "Received - low service density", "Received - moderate service density", "Received - high service density", "Received - review required"].index(st.session_state.project_info.get("byda_plan_status", "Not available")),
        )
        accommodation_required = st.checkbox("Accommodation likely required", value=bool(st.session_state.project_info.get("accommodation_required", False)))
        ai_model = st.selectbox(
            "AI Model Provider / Mode",
            ["OpenAI", "Not connected yet", "Azure OpenAI", "Claude", "Gemini", "Local Model"],
            index=0,
        )

    custom_public_holidays = st.text_area(
        "Additional / Custom Public Holidays",
        value=st.session_state.project_info.get("custom_public_holidays", ""),
        help="Optional. Enter one date per line, e.g. 25/12/2026 or 25/12/2026, Christmas Day.",
    )

    st.subheader("Additional Project Information for AI Planning")
    traffic_context = st.text_area(
        "Live traffic / road corridor information",
        value=st.session_state.project_info.get("traffic_context", ""),
        help="Describe nearby live traffic, road reserve constraints, lane closures, traffic management expectations, etc.",
    )
    nearest_accommodation_notes = st.text_area(
        "Nearest accommodation / travel notes",
        value=st.session_state.project_info.get("nearest_accommodation_notes", ""),
        help="Enter known accommodation location, expected drive time, whether crews return daily, etc.",
    )
    overhead_spotter_notes = st.text_area(
        "Overhead services / spotter requirements",
        value=st.session_state.project_info.get("overhead_spotter_notes", ""),
        help="Describe overhead power lines, railway overheads, vegetation, lifting constraints or spotter requirements.",
    )
    underground_services_notes = st.text_area(
        "Underground services / BYDA notes",
        value=st.session_state.project_info.get("underground_services_notes", ""),
        help="Summarise BYDA constraints, service density, critical assets, potholing requirements, exclusions, etc.",
    )
    additional_constraints = st.text_area(
        "Other constraints / assumptions",
        value=st.session_state.project_info.get("additional_constraints", ""),
        help="Access permits, landowner constraints, environmental windows, site inductions, work hours, water supply, etc.",
    )

    st.session_state.project_info = {
        "project_name": project_name,
        "project_number": project_number,
        "start_date": str(start_date),
        "working_hours": working_hours,
        "work_weekends": work_weekends,
        "internal_fieldwork_resources": internal_fieldwork_resources,
        "external_fieldwork_resources": external_fieldwork_resources,
        "shade_public_holidays": shade_public_holidays,
        "public_holiday_state": public_holiday_state,
        "custom_public_holidays": custom_public_holidays,
        "gda2020_mga_zone": gda2020_mga_zone,
        "byda_plan_status": byda_plan_status,
        "accommodation_required": accommodation_required,
        "traffic_context": traffic_context,
        "nearest_accommodation_notes": nearest_accommodation_notes,
        "overhead_spotter_notes": overhead_spotter_notes,
        "underground_services_notes": underground_services_notes,
        "additional_constraints": additional_constraints,
        "ai_model": ai_model,
        "rate_extraction_model": st.session_state.project_info.get("rate_extraction_model", "gpt-4.1-mini"),
        "ai_preliminary_model": st.session_state.project_info.get("ai_preliminary_model", "gpt-4.1-mini"),
    }

    st.info("Use the separate Subcontractor Rate Schedule tab to enter or extract subcontractor rates.")



# --------------------------------------------------
# Tab 2: Subcontractor Rate Schedule
# --------------------------------------------------

with tab2:
    st.header("Subcontractor Rate Schedule")
    st.caption("Enter subcontractors manually or use AI to extract rates from uploaded schedules. Each subcontractor is shown in a collapsible section with its type.")

    st.subheader("AI Rate Schedule Import")
    rate_schedule_files = st.file_uploader(
        "Upload subcontractor/laboratory rate schedule for AI extraction",
        type=["pdf", "docx", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Upload driller, excavator, traffic control or laboratory rate schedules. The AI will extract subcontractors and rate items for review.",
    )

    col_ai1, col_ai2, col_ai3 = st.columns([2, 1, 1])
    with col_ai1:
        rate_extraction_model = st.text_input(
            "AI model for rate extraction",
            value=st.session_state.project_info.get("rate_extraction_model", "gpt-4.1-mini"),
        )
    with col_ai2:
        replace_extracted_rates = st.checkbox("Replace existing subcontractor/rate tables", value=False)
    with col_ai3:
        extract_button = st.button("Extract Rates with AI")

    if extract_button:
        try:
            with st.spinner("Extracting subcontractor rates from uploaded schedule..."):
                extracted_rates = extract_rate_schedule_with_ai(rate_schedule_files, rate_extraction_model)
                apply_extracted_rates(extracted_rates, replace_existing=replace_extracted_rates)
            st.success("Rates extracted. Please review and edit before using them in the task table.")
            with st.expander("View raw extracted JSON"):
                st.json(extracted_rates)
        except Exception as e:
            st.error(f"Rate extraction failed: {e}")
    st.session_state.project_info["rate_extraction_model"] = rate_extraction_model

    st.subheader("Subcontractor Register")
    st.session_state.subcontractors_df = st.data_editor(
        st.session_state.subcontractors_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Subcontractor_ID": st.column_config.TextColumn("Subcontractor ID", required=True),
            "Subcontractor_Name": st.column_config.TextColumn("Subcontractor Name", required=True),
            "Subcontractor_Type": st.column_config.SelectboxColumn(
                "Type",
                options=["Driller", "Laboratory", "Excavator", "Traffic Control", "Utility Locator", "Surveyor", "Other"],
                required=True,
            ),
            "Notes": st.column_config.TextColumn("Notes"),
        },
    )
    st.session_state.subcontractors_df = normalize_subcontractors_df(st.session_state.subcontractors_df)

    st.subheader("Rates by Subcontractor")
    st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(st.session_state.subcontractor_rates_df)

    for _, sub in st.session_state.subcontractors_df.iterrows():
        sub_id = str(sub["Subcontractor_ID"])
        sub_name = str(sub["Subcontractor_Name"])
        sub_type = str(sub["Subcontractor_Type"])
        mask = st.session_state.subcontractor_rates_df["Subcontractor_ID"].astype(str) == sub_id
        sub_rates = st.session_state.subcontractor_rates_df[mask].copy()

        with st.expander(f"{sub_name} — {sub_type}", expanded=False):
            st.caption(f"Subcontractor ID: {sub_id}")
            edited_sub_rates = st.data_editor(
                sub_rates,
                num_rows="dynamic",
                use_container_width=True,
                key=f"rates_editor_{sub_id}",
                column_config={
                    "Subcontractor_ID": st.column_config.TextColumn("Subcontractor ID", disabled=True),
                    "Subcontractor_Name": st.column_config.TextColumn("Subcontractor Name", disabled=True),
                    "Subcontractor_Type": st.column_config.TextColumn("Type", disabled=True),
                    "Item": st.column_config.TextColumn("Rate Item", required=True),
                    "Unit": st.column_config.TextColumn("Unit"),
                    "Production_per_day": st.column_config.NumberColumn("Production per day", min_value=0.0),
                    "Daily_Rate": st.column_config.NumberColumn("Daily rate", min_value=0.0),
                    "Unit_Rate": st.column_config.NumberColumn("Unit rate", min_value=0.0),
                    "Rate_Type": st.column_config.SelectboxColumn("Rate Type", options=["Daily", "Unit", "Allowance"]),
                    "Notes": st.column_config.TextColumn("Notes"),
                },
            )
            edited_sub_rates["Subcontractor_ID"] = sub_id
            edited_sub_rates["Subcontractor_Name"] = sub_name
            edited_sub_rates["Subcontractor_Type"] = sub_type

            st.session_state.subcontractor_rates_df = pd.concat([
                st.session_state.subcontractor_rates_df[~mask],
                edited_sub_rates,
            ], ignore_index=True)
            st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(st.session_state.subcontractor_rates_df)

    st.subheader("All Subcontractor Rate Items")
    st.dataframe(st.session_state.subcontractor_rates_df, use_container_width=True)

    # Keep production table synced for duration calculation.
    st.session_state.rates_df = sync_rates_from_subcontractor_rates(st.session_state.subcontractor_rates_df)
    with st.expander("Derived Fieldwork Production Rates used for Duration Calculation", expanded=False):
        st.dataframe(st.session_state.rates_df, use_container_width=True)

    st.subheader("Soil Laboratory Testing")
    st.session_state.soil_lab_df = st.data_editor(
        st.session_state.soil_lab_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Selected": st.column_config.CheckboxColumn("Selected"),
            "Test": st.column_config.TextColumn("Test"),
            "Rate": st.column_config.NumberColumn("Test rate", min_value=0.0),
            "Turnaround_days": st.column_config.NumberColumn("Turnaround days", min_value=0),
        },
    )
    st.session_state.soil_lab_df = normalize_lab_tests_df(st.session_state.soil_lab_df)

    st.subheader("Rock Laboratory Testing")
    st.session_state.rock_lab_df = st.data_editor(
        st.session_state.rock_lab_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Selected": st.column_config.CheckboxColumn("Selected"),
            "Test": st.column_config.TextColumn("Test"),
            "Rate": st.column_config.NumberColumn("Test rate", min_value=0.0),
            "Turnaround_days": st.column_config.NumberColumn("Turnaround days", min_value=0),
        },
    )
    st.session_state.rock_lab_df = normalize_lab_tests_df(st.session_state.rock_lab_df)

# --------------------------------------------------
# Tab 3: Tasks
# --------------------------------------------------

with tab3:
    st.header("Investigation Task Input")

    uploaded_task_file = st.file_uploader("Upload investigation task spreadsheet", type=["xlsx", "xls", "csv"])
    if uploaded_task_file:
        st.session_state.tasks_df = read_tabular_upload(uploaded_task_file)
        st.session_state.tasks_df = normalize_tasks_df(st.session_state.tasks_df)

    st.info(
        "Use Order to control general sequence. Use Depends_On to force a task to start after another task. "
        "If Duration_days is 0, Task_Type must match a production item in the rates table. "
        "Non-production task types, including Fieldwork, require manual Duration_days."
    )

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        task_options = st.session_state.tasks_df["Task_ID"].astype(str).tolist()
        selected_task = st.selectbox("Select task to move", task_options)
    with col2:
        if st.button("Move Up"):
            st.session_state.tasks_df = move_row(st.session_state.tasks_df, selected_task, "up")
    with col3:
        if st.button("Move Down"):
            st.session_state.tasks_df = move_row(st.session_state.tasks_df, selected_task, "down")

    task_type_options = get_task_type_options(st.session_state.rates_df)
    dependency_options = [""] + st.session_state.tasks_df["Task_ID"].dropna().astype(str).unique().tolist()
    subcontractor_options = get_subcontractor_options()
    rate_item_options = get_rate_item_options()

    edited_tasks_df = st.data_editor(
        st.session_state.tasks_df.sort_values("Order"),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Order": st.column_config.NumberColumn("Order", min_value=1, step=1),
            "Task_ID": st.column_config.TextColumn("Task ID", required=True),
            "Task_Type": st.column_config.SelectboxColumn("Task Type", options=task_type_options, required=True),
            "Location_ID": st.column_config.TextColumn("Location ID"),
            "Investigation_Type": st.column_config.SelectboxColumn("Investigation Type", options=INVESTIGATION_TYPE_OPTIONS, required=True),
            "Depth_m": st.column_config.NumberColumn("Depth m / Quantity", min_value=0.0),
            "Duration_days": st.column_config.NumberColumn("Duration days", min_value=0.0),
            "Depends_On": st.column_config.SelectboxColumn("Depends On", options=dependency_options),
            "Assigned_Subcontractor": st.column_config.SelectboxColumn("Assigned Subcontractor", options=subcontractor_options),
            "Rate_Item": st.column_config.SelectboxColumn("Rate Item", options=rate_item_options, help="Rate item from the subcontractor rate schedule used for rough cost estimate."),
            "Bar_Color": st.column_config.SelectboxColumn("Bar Color", options=COLOR_OPTIONS),
            "Easting": st.column_config.NumberColumn("Easting", min_value=0.0),
            "Northing": st.column_config.NumberColumn("Northing", min_value=0.0),
            "Access_Notes": st.column_config.TextColumn("Access Notes"),
        },
    )
    st.session_state.tasks_df = normalize_tasks_df(edited_tasks_df)


# --------------------------------------------------
# Tab 4: AI Preliminary Program
# --------------------------------------------------

with tab4:
    st.header("AI Preliminary Program")
    st.info(
        "This AI step has one purpose: produce a preliminary editable program table from the project inputs, task list and mapped locations. "
        "It considers traffic, accommodation, spacing between test locations, overhead spotter needs, BYDA/service density and ground/groundwater information where provided."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        ai_preliminary_model = st.text_input(
            "OpenAI model for preliminary program",
            value=st.session_state.project_info.get("ai_preliminary_model", "gpt-4.1-mini"),
        )
    with col2:
        if st.button("Clear AI preliminary program"):
            st.session_state.ai_program_df = pd.DataFrame()
            st.session_state.ai_program_comments = ""

    st.session_state.project_info["ai_preliminary_model"] = ai_preliminary_model

    byda_files = st.file_uploader(
        "Upload BYDA plans / services information for AI review",
        type=["pdf", "png", "jpg", "jpeg", "docx", "xlsx", "xls", "csv"],
        accept_multiple_files=True,
        help="Optional. The AI can use these files to flag service density and likely potholing/traffic management constraints.",
    )
    borehole_db_file = st.file_uploader(
        "Upload borehole database / ground model table",
        type=["xlsx", "xls", "csv"],
        help="Optional. Include previous boreholes, groundwater observations, interpreted units, rock level or refusal information.",
    )

    borehole_db_df = pd.DataFrame()
    if borehole_db_file:
        try:
            borehole_db_df = read_tabular_upload(borehole_db_file)
            st.subheader("Imported Borehole / Ground Database Preview")
            st.dataframe(borehole_db_df.head(50), use_container_width=True)
        except Exception as e:
            st.error(f"Could not read borehole database: {e}")

    if st.button("Generate AI Preliminary Program"):
        try:
            with st.spinner("AI is preparing a preliminary program..."):
                result = generate_ai_preliminary_program(byda_files, ai_preliminary_model, borehole_db_df)
                st.session_state.ai_program_df = normalize_ai_program_df(pd.DataFrame(result.get("preliminary_program", [])))
                st.session_state.ai_program_comments = str(result.get("general_comments", ""))
            st.success("AI preliminary program generated. Review and edit the table below before using it.")
        except Exception as e:
            st.error(f"AI preliminary program failed: {e}")

    if st.session_state.ai_program_comments:
        st.subheader("AI General Comments")
        st.write(st.session_state.ai_program_comments)

    st.subheader("Editable AI Preliminary Program Table")
    if st.session_state.ai_program_df.empty:
        st.info("No AI preliminary program yet. Generate one above, or use the rule-based program in the next tab.")
    else:
        edited_ai_df = st.data_editor(
            normalize_ai_program_df(st.session_state.ai_program_df),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Start": st.column_config.DateColumn("Start"),
                "Finish": st.column_config.DateColumn("Finish"),
                "Bar_Color": st.column_config.SelectboxColumn("Bar Color", options=COLOR_OPTIONS),
                "Depends_On": st.column_config.TextColumn("Depends On"),
                "Assigned_Subcontractor": st.column_config.SelectboxColumn("Assigned Subcontractor", options=get_subcontractor_options()),
                "Rate_Item": st.column_config.SelectboxColumn("Rate Item", options=get_rate_item_options()),
                "Estimated_Cost": st.column_config.NumberColumn("AI Estimated Cost", min_value=0.0),
                "Planning_Notes": st.column_config.TextColumn("Planning Notes"),
                "Traffic_Management": st.column_config.TextColumn("Traffic Management"),
                "Accommodation_Notes": st.column_config.TextColumn("Accommodation Notes"),
                "Distance_Notes": st.column_config.TextColumn("Distance Notes"),
                "Overhead_Spotter": st.column_config.TextColumn("Overhead Spotter"),
                "Services_Risk": st.column_config.TextColumn("Services Risk"),
                "Groundwater_Risk": st.column_config.TextColumn("Groundwater Risk"),
            },
        )
        st.session_state.ai_program_df = normalize_ai_program_df(edited_ai_df)

        prelim_cost_df, prelim_summary_df = estimate_program_cost(
            st.session_state.ai_program_df,
            st.session_state.rates_df,
            st.session_state.soil_lab_df,
            st.session_state.rock_lab_df,
        )
        st.subheader("Preliminary Rough Cost Estimate")
        if prelim_cost_df.empty:
            st.info("No rough cost is available yet. Assign subcontractor/rate items or add rates.")
        else:
            st.dataframe(prelim_cost_df, use_container_width=True)
            if not prelim_summary_df.empty:
                st.dataframe(prelim_summary_df, use_container_width=True)
            st.metric("Preliminary Estimated Total Cost", f"${float(prelim_cost_df['Total_Cost'].sum()):,.2f}")

        if st.button("Use AI Preliminary Program for Gantt Chart"):
            st.session_state.program_df = normalize_ai_program_df(st.session_state.ai_program_df)
            st.session_state.cost_df, st.session_state.cost_summary_df = estimate_program_cost(
                st.session_state.program_df,
                st.session_state.rates_df,
                st.session_state.soil_lab_df,
                st.session_state.rock_lab_df,
            )
            st.success("AI preliminary program copied to the Program & Gantt tab.")


# --------------------------------------------------
# Tab 5: Program, Gantt and Map
# --------------------------------------------------

with tab5:
    st.header("Program, Gantt Chart & Test Location Plan")

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if st.button("Generate Rule-Based Program"):
            try:
                start = datetime.strptime(st.session_state.project_info["start_date"], "%Y-%m-%d").date()
                st.session_state.program_df = generate_program(
                    st.session_state.tasks_df,
                    st.session_state.rates_df,
                    start,
                    st.session_state.project_info["work_weekends"],
                )
                st.session_state.cost_df, st.session_state.cost_summary_df = estimate_program_cost(
                    st.session_state.program_df,
                    st.session_state.rates_df,
                    st.session_state.soil_lab_df,
                    st.session_state.rock_lab_df,
                )
                st.success("Rule-based program generated.")
            except ValueError as e:
                st.error(str(e))
    with col_b:
        if st.button("Load AI Preliminary Program"):
            if st.session_state.ai_program_df.empty:
                st.warning("No AI preliminary program is available yet.")
            else:
                st.session_state.program_df = normalize_ai_program_df(st.session_state.ai_program_df)
                st.session_state.cost_df, st.session_state.cost_summary_df = estimate_program_cost(
                    st.session_state.program_df,
                    st.session_state.rates_df,
                    st.session_state.soil_lab_df,
                    st.session_state.rock_lab_df,
                )
                st.success("AI preliminary program loaded.")

    if not st.session_state.program_df.empty:
        st.subheader("Editable Program Table")
        program_for_edit = normalize_ai_program_df(st.session_state.program_df)
        edited_program_df = st.data_editor(
            program_for_edit,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Start": st.column_config.DateColumn("Start"),
                "Finish": st.column_config.DateColumn("Finish"),
                "Assigned_Subcontractor": st.column_config.SelectboxColumn("Assigned Subcontractor", options=get_subcontractor_options()),
                "Rate_Item": st.column_config.SelectboxColumn("Rate Item", options=get_rate_item_options()),
                "Bar_Color": st.column_config.SelectboxColumn("Bar Color", options=COLOR_OPTIONS),
            },
        )
        st.session_state.program_df = normalize_ai_program_df(edited_program_df)
        st.session_state.cost_df, st.session_state.cost_summary_df = estimate_program_cost(
            st.session_state.program_df,
            st.session_state.rates_df,
            st.session_state.soil_lab_df,
            st.session_state.rock_lab_df,
        )

        plot_df = normalize_ai_program_df(st.session_state.program_df)
        plot_df = plot_df.sort_values("Order").reset_index(drop=True)
        n_tasks = len(plot_df)
        plot_df["Y"] = list(range(n_tasks, 0, -1))
        plot_df["Task_Label"] = plot_df["Order"].astype(str) + " - " + plot_df["Task_ID"].astype(str)

        location_text = plot_df["Location_ID"].fillna("").astype(str).str.strip()
        investigation_text = plot_df["Investigation_Type"].fillna("").astype(str).str.strip()
        plot_df["Bar_Label"] = location_text + "_" + investigation_text
        plot_df.loc[location_text == "", "Bar_Label"] = plot_df["Task_ID"].astype(str) + "_" + investigation_text
        plot_df["Bar_Label"] = plot_df["Bar_Label"].str.strip("_")
        plot_df["Bar_Color"] = plot_df["Bar_Color"].fillna("blue")

        fig = go.Figure()
        for _, row in plot_df.iterrows():
            start_dt = pd.to_datetime(row["Start"])
            finish_dt = pd.to_datetime(row["Finish"])
            duration_ms = max((finish_dt - start_dt).total_seconds() * 1000, 1)
            fig.add_trace(go.Bar(
                x=[duration_ms],
                y=[row["Y"]],
                base=[start_dt],
                orientation="h",
                width=1.0,
                marker=dict(color=row["Bar_Color"], line=dict(width=0)),
                text=[row["Bar_Label"]],
                textposition="inside",
                insidetextanchor="middle",
                customdata=[[
                    row.get("Task_ID", ""), row.get("Task_Type", ""), row.get("Location_ID", ""),
                    row.get("Investigation_Type", ""), row.get("Depth_m", ""), row.get("Duration_days", ""),
                    row.get("Depends_On", ""), row.get("Access_Notes", ""), finish_dt.strftime("%d-%b-%Y"),
                    row.get("Planning_Notes", ""), row.get("Services_Risk", ""), row.get("Groundwater_Risk", ""),
                ]],
                hovertemplate=(
                    "Task ID: %{customdata[0]}<br>Task Type: %{customdata[1]}<br>"
                    "Location ID: %{customdata[2]}<br>Investigation Type: %{customdata[3]}<br>"
                    "Depth: %{customdata[4]} m<br>Duration: %{customdata[5]} day(s)<br>"
                    "Depends On: %{customdata[6]}<br>Start: %{base|%d-%b-%Y}<br>"
                    "Finish: %{customdata[8]}<br>Planning Notes: %{customdata[9]}<br>"
                    "Services Risk: %{customdata[10]}<br>Groundwater Risk: %{customdata[11]}<extra></extra>"
                ),
                showlegend=False,
            ))

        fig.update_yaxes(
            tickmode="array",
            tickvals=plot_df["Y"].tolist(),
            ticktext=plot_df["Task_Label"].tolist(),
            range=[0.5, n_tasks + 0.5],
            dtick=1,
            showgrid=True,
            gridwidth=1,
            ticks="outside",
            zeroline=False,
        )
        fig.update_xaxes(
            type="date",
            dtick=24 * 60 * 60 * 1000,
            tickformat="%d-%b",
            showgrid=True,
            gridwidth=1,
            ticks="outside",
            zeroline=False,
        )
        fig.update_layout(
            height=max(350, 32 * n_tasks),
            barmode="overlay",
            bargap=0,
            bargroupgap=0,
            plot_bgcolor="white",
            xaxis_title="Date",
            yaxis_title="Task",
            showlegend=False,
            margin=dict(l=20, r=20, t=60, b=40),
        )

        start_date_plot = plot_df["Start"].min()
        finish_date_plot = plot_df["Finish"].max()
        all_dates = pd.date_range(start_date_plot, finish_date_plot, freq="D")
        for d in all_dates:
            if d.weekday() >= 5:
                fig.add_vrect(x0=d, x1=d + pd.Timedelta(days=1), fillcolor="lightgrey", opacity=0.25, layer="below", line_width=0)

        if st.session_state.project_info.get("shade_public_holidays", True):
            public_holidays = get_public_holidays(
                start_date_plot,
                finish_date_plot,
                st.session_state.project_info.get("public_holiday_state", "VIC"),
                st.session_state.project_info.get("custom_public_holidays", ""),
            )
            for holiday_date, holiday_name in sorted(public_holidays.items()):
                holiday_start = pd.to_datetime(holiday_date)
                fig.add_vrect(x0=holiday_start, x1=holiday_start + pd.Timedelta(days=1), fillcolor="red", opacity=0.28, layer="below", line_width=0)
                fig.add_annotation(x=holiday_start + pd.Timedelta(hours=12), y=n_tasks + 0.45, text=str(holiday_name), showarrow=False, textangle=-90, font=dict(size=8, color="red"), yanchor="top")

        st.subheader("Gantt Chart")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Cost Estimate")
        if st.session_state.cost_df.empty:
            st.info("No cost estimate available. Check that daily rates/test rates are provided.")
        else:
            st.dataframe(st.session_state.cost_df, use_container_width=True)
            if not st.session_state.cost_summary_df.empty:
                st.dataframe(st.session_state.cost_summary_df, use_container_width=True)
            total_cost = float(st.session_state.cost_df["Total_Cost"].sum())
            st.metric("Estimated Total Cost", f"${total_cost:,.2f}")
    else:
        st.info("Generate a rule-based program or load an AI preliminary program to show the editable program and Gantt chart.")

    st.subheader("Test Location Plan")
    selected_zone = st.session_state.project_info.get("gda2020_mga_zone", "Zone 55")
    st.write(f"Current coordinate system: GDA2020 MGA {selected_zone} ({GDA2020_MGA_EPSG.get(selected_zone, '')})")
    if not MAP_DEPENDENCIES_AVAILABLE:
        st.error("Mapping dependencies are not installed. Please run: pip install pyproj folium streamlit-folium")
    else:
        try:
            map_df = convert_gda2020_mga_to_latlon(st.session_state.tasks_df, selected_zone)
            if map_df.empty:
                st.warning("No valid coordinates found. Add non-zero Easting and Northing values to the task table.")
            else:
                st.dataframe(map_df[["Task_ID", "Location_ID", "Investigation_Type", "Easting", "Northing", "Latitude", "Longitude"]], use_container_width=True)
                m = build_test_location_map(map_df)
                st_folium(m, width=1100, height=600)
        except Exception as e:
            st.error(f"Map generation failed: {e}")


# --------------------------------------------------
# Tab 6: Export / Save
# --------------------------------------------------

with tab6:
    st.header("Export and Save Project")

    project_package = {
        "project_info": st.session_state.project_info,
        "rates": st.session_state.rates_df.to_dict(orient="records"),
        "subcontractors": st.session_state.subcontractors_df.to_dict(orient="records"),
        "subcontractor_rates": st.session_state.subcontractor_rates_df.to_dict(orient="records"),
        "soil_lab_tests": st.session_state.soil_lab_df.to_dict(orient="records"),
        "rock_lab_tests": st.session_state.rock_lab_df.to_dict(orient="records"),
        "tasks": st.session_state.tasks_df.to_dict(orient="records"),
        "ai_program": st.session_state.ai_program_df.to_dict(orient="records") if not st.session_state.ai_program_df.empty else [],
        "ai_program_comments": st.session_state.ai_program_comments,
        "program": st.session_state.program_df.to_dict(orient="records") if not st.session_state.program_df.empty else [],
        "cost": st.session_state.cost_df.to_dict(orient="records") if not st.session_state.cost_df.empty else [],
        "cost_summary": st.session_state.cost_summary_df.to_dict(orient="records") if not st.session_state.cost_summary_df.empty else [],
    }

    st.download_button(
        "Save Project JSON",
        data=save_project_json(project_package),
        file_name="fieldwork_project.json",
        mime="application/json",
    )

    uploaded_project = st.file_uploader("Load Existing Project JSON", type=["json"])
    if uploaded_project and st.button("Load Project"):
        loaded = load_project_json(uploaded_project)
        st.session_state.project_info = loaded.get("project_info", {})
        st.session_state.rates_df = normalize_rates_df(pd.DataFrame(loaded.get("rates", [])))
        st.session_state.subcontractors_df = normalize_subcontractors_df(pd.DataFrame(loaded.get("subcontractors", [])))
        st.session_state.subcontractor_rates_df = normalize_subcontractor_rates_df(pd.DataFrame(loaded.get("subcontractor_rates", [])))
        st.session_state.rates_df = sync_rates_from_subcontractor_rates(st.session_state.subcontractor_rates_df)
        st.session_state.soil_lab_df = normalize_lab_tests_df(pd.DataFrame(loaded.get("soil_lab_tests", [])))
        st.session_state.rock_lab_df = normalize_lab_tests_df(pd.DataFrame(loaded.get("rock_lab_tests", [])))
        st.session_state.tasks_df = normalize_tasks_df(pd.DataFrame(loaded.get("tasks", [])))
        st.session_state.ai_program_df = normalize_ai_program_df(pd.DataFrame(loaded.get("ai_program", [])))
        st.session_state.ai_program_comments = loaded.get("ai_program_comments", "")
        st.session_state.program_df = normalize_ai_program_df(pd.DataFrame(loaded.get("program", [])))
        st.session_state.cost_df = pd.DataFrame(loaded.get("cost", []))
        st.session_state.cost_summary_df = pd.DataFrame(loaded.get("cost_summary", []))
        st.success("Project loaded.")

    excel_bytes = dataframe_to_excel_bytes({
        "Subcontractors": st.session_state.subcontractors_df,
        "Subcontractor Rates": st.session_state.subcontractor_rates_df,
        "Derived Production Rates": st.session_state.rates_df,
        "Soil Lab Tests": st.session_state.soil_lab_df,
        "Rock Lab Tests": st.session_state.rock_lab_df,
        "Tasks": st.session_state.tasks_df,
        "AI Preliminary Program": st.session_state.ai_program_df,
        "Program": st.session_state.program_df,
        "Cost": st.session_state.cost_df,
        "Cost Summary": st.session_state.cost_summary_df,
    })

    st.download_button(
        "Export Excel Program",
        data=excel_bytes,
        file_name="fieldwork_program_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
