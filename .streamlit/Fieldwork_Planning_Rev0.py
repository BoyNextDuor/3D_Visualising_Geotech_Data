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
from openai import OpenAI
import streamlit as st

if "OPENAI_API_KEY" not in st.secrets:
    st.error(
        "OPENAI_API_KEY not found. Please add it to Streamlit Secrets."
    )
    st.stop()

client = OpenAI(
    api_key=st.secrets["OPENAI_API_KEY"]
)


# --------------------------------------------------
# Default tables
# --------------------------------------------------

def default_rates():
    return pd.DataFrame([
        {"Item": "Drilling", "Unit": "m", "Production_per_day": 20.0},
        {"Item": "Excavator", "Unit": "day", "Production_per_day": 1.0},
        {"Item": "Vacuum Truck", "Unit": "day", "Production_per_day": 1.0},
        {"Item": "Traffic Control", "Unit": "day", "Production_per_day": 1.0},
    ])


def default_soil_lab_tests():
    return pd.DataFrame([
        {"Selected": False, "Test": "Moisture Content (AS 1289.2.1.1)", "Turnaround_days": 3},
        {"Selected": False, "Test": "Liquid Limit (AS 1289.3.1.1)", "Turnaround_days": 5},
        {"Selected": False, "Test": "Plastic Limit / Plasticity Index (AS 1289.3.2.1 / AS 1289.3.3.1)", "Turnaround_days": 5},
        {"Selected": False, "Test": "Particle Size Distribution - Sieve (AS 1289.3.6.1)", "Turnaround_days": 7},
        {"Selected": False, "Test": "Particle Size Distribution - Hydrometer (AS 1289.3.6.3)", "Turnaround_days": 10},
        {"Selected": False, "Test": "Emerson Class (AS 1289.3.8.1)", "Turnaround_days": 5},
        {"Selected": False, "Test": "pH Value (AS 1289.4.3.1)", "Turnaround_days": 5},
        {"Selected": False, "Test": "Standard Compaction (AS 1289.5.1.1)", "Turnaround_days": 7},
        {"Selected": False, "Test": "CBR - Laboratory Soaked (AS 1289.6.1.1)", "Turnaround_days": 10},
        {"Selected": False, "Test": "Direct Shear Box (AS 1289.6.2.2)", "Turnaround_days": 10},
        {"Selected": False, "Test": "Consolidation / Oedometer (AS 1289.6.6.1)", "Turnaround_days": 14},
        {"Selected": False, "Test": "Shrink-Swell Index (AS 1289.7.1.1)", "Turnaround_days": 10},
    ])


def default_rock_lab_tests():
    return pd.DataFrame([
        {"Selected": False, "Test": "Point Load Strength Index Is50 (AS 4133)", "Turnaround_days": 5},
        {"Selected": False, "Test": "Uniaxial Compressive Strength - UCS (AS 4133.4.2.2)", "Turnaround_days": 7},
        {"Selected": False, "Test": "UCS with Elastic Modulus and Poisson's Ratio (AS 4133)", "Turnaround_days": 10},
        {"Selected": False, "Test": "Brazilian Tensile Strength (AS 4133)", "Turnaround_days": 7},
        {"Selected": False, "Test": "Rock Density / Unit Weight (AS 4133)", "Turnaround_days": 5},
        {"Selected": False, "Test": "Porosity and Water Absorption (AS 4133)", "Turnaround_days": 7},
        {"Selected": False, "Test": "Slake Durability Index (AS 4133)", "Turnaround_days": 10},
        {"Selected": False, "Test": "Rock Direct Shear - Discontinuity (AS 4133)", "Turnaround_days": 14},
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
            "Bar_Color": "gray",
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
            "Bar_Color": "blue",
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
            "Bar_Color": "green",
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
        "Depth_m/Qty": 0.0,
        "Duration_days": 0.0,
        "Depends_On": "",
        "Bar_Color": "blue",
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

    for col in ["Task_ID", "Task_Type", "Location_ID", "Investigation_Type", "Depends_On", "Bar_Color", "Access_Notes"]:
        df[col] = df[col].fillna("").astype(str)

    # Do not force Task_Type here because production items are user-editable in the rates table.
    df.loc[~df["Bar_Color"].isin(COLOR_OPTIONS), "Bar_Color"] = "blue"

    ordered_cols = list(required_defaults.keys())
    extra_cols = [c for c in df.columns if c not in ordered_cols]
    return df[ordered_cols + extra_cols].sort_values("Order").reset_index(drop=True)



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

        previous_finish_dates = [v["Finish_Actual"] for v in scheduled.values()]
        if previous_finish_dates:
            sequence_start = max(previous_finish_dates) + timedelta(days=1)
        else:
            sequence_start = start_date

        current_start = max(earliest_start, sequence_start)
        current_start = next_working_day(current_start, work_weekends)

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
            "Start": current_start,
            "Finish": finish_plot,
            "Bar_Color": task.get("Bar_Color", "blue"),
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

Production rates:
{dataframe_to_context_text(rates_df)}

Investigation tasks:
{dataframe_to_context_text(tasks_df)}

Selected soil laboratory testing:
{dataframe_to_context_text(soil_lab_df[soil_lab_df.get('Selected', False) == True] if isinstance(soil_lab_df, pd.DataFrame) and 'Selected' in soil_lab_df.columns else soil_lab_df)}

Selected rock laboratory testing:
{dataframe_to_context_text(rock_lab_df[rock_lab_df.get('Selected', False) == True] if isinstance(rock_lab_df, pd.DataFrame) and 'Selected' in rock_lab_df.columns else rock_lab_df)}

Generated program:
{dataframe_to_context_text(program_df)}

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
# Streamlit app
# --------------------------------------------------

st.set_page_config(page_title="Fieldwork Planner", layout="wide")
st.title("Fieldwork Planning Web Application")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "1. Project Setup",
    "2. Investigation Tasks",
    "3. Program & Gantt Chart",
    "4. Export / Save",
    "5. AI Guidance"
])

if "project_info" not in st.session_state:
    st.session_state.project_info = {}

if "rates_df" not in st.session_state:
    st.session_state.rates_df = default_rates()

if "soil_lab_df" not in st.session_state:
    st.session_state.soil_lab_df = default_soil_lab_tests()

if "rock_lab_df" not in st.session_state:
    st.session_state.rock_lab_df = default_rock_lab_tests()

if "tasks_df" not in st.session_state:
    st.session_state.tasks_df = default_tasks()

if "program_df" not in st.session_state:
    st.session_state.program_df = pd.DataFrame()

if "ai_messages" not in st.session_state:
    st.session_state.ai_messages = []

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
        start_date = st.date_input("Project Start Date", value=date.today())

    with col2:
        working_hours = st.number_input("Working Hours per Day", min_value=1.0, max_value=24.0, value=8.0)
        work_weekends = st.checkbox("Allow Weekend Work", value=False)
        shade_public_holidays = st.checkbox(
            "Shade Public Holidays on Gantt Chart",
            value=st.session_state.project_info.get("shade_public_holidays", True),
        )
        public_holiday_state = st.selectbox(
            "Australian Public Holiday State/Territory",
            ["VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"],
            index=["VIC", "NSW", "QLD", "SA", "WA", "TAS", "ACT", "NT"].index(
                st.session_state.project_info.get("public_holiday_state", "VIC")
            ),
        )
        ai_model = st.selectbox(
            "AI Model for Future Document Reading",
            ["Not connected yet", "OpenAI", "Azure OpenAI", "Claude", "Gemini", "Local Model"]
        )

    custom_public_holidays = st.text_area(
        "Additional / Custom Public Holidays",
        value=st.session_state.project_info.get("custom_public_holidays", ""),
        help=(
            "Optional. Enter one date per line, e.g. 25/12/2026 or "
            "25/12/2026, Christmas Day. These will be shaded on the Gantt chart."
        ),
    )

    st.subheader("Fieldwork Production Rates")
    st.session_state.rates_df = st.data_editor(
        st.session_state.rates_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Item": st.column_config.TextColumn("Production Item", required=True),
            "Unit": st.column_config.TextColumn("Unit"),
            "Production_per_day": st.column_config.NumberColumn("Production per day", min_value=0.0),
        },
    )

    st.subheader("Soil Laboratory Testing")
    st.session_state.soil_lab_df = st.data_editor(
        st.session_state.soil_lab_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Selected": st.column_config.CheckboxColumn("Selected"),
            "Test": st.column_config.TextColumn("Test"),
            "Turnaround_days": st.column_config.NumberColumn("Turnaround days", min_value=0),
        },
    )

    st.subheader("Rock Laboratory Testing")
    st.session_state.rock_lab_df = st.data_editor(
        st.session_state.rock_lab_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Selected": st.column_config.CheckboxColumn("Selected"),
            "Test": st.column_config.TextColumn("Test"),
            "Turnaround_days": st.column_config.NumberColumn("Turnaround days", min_value=0),
        },
    )

    st.session_state.project_info = {
        "project_name": project_name,
        "project_number": project_number,
        "start_date": str(start_date),
        "working_hours": working_hours,
        "work_weekends": work_weekends,
        "shade_public_holidays": shade_public_holidays,
        "public_holiday_state": public_holiday_state,
        "custom_public_holidays": custom_public_holidays,
        "ai_model": ai_model,
    }


# --------------------------------------------------
# Tab 2: Tasks
# --------------------------------------------------

with tab2:
    st.header("Investigation Task Input")

    uploaded_task_file = st.file_uploader(
        "Upload investigation task spreadsheet",
        type=["xlsx", "xls", "csv"]
    )

    if uploaded_task_file:
        if uploaded_task_file.name.endswith(".csv"):
            st.session_state.tasks_df = pd.read_csv(uploaded_task_file)
        else:
            st.session_state.tasks_df = pd.read_excel(uploaded_task_file)
        st.session_state.tasks_df = normalize_tasks_df(st.session_state.tasks_df)

    st.info(
        "Use Order to control general sequence. Use Depends_On to prevent a task "
        "from starting before another Task_ID is completed. If Duration_days is 0, "
        "Task_Type must be one of the production items in the rates table. "
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

    edited_tasks_df = st.data_editor(
        st.session_state.tasks_df.sort_values("Order"),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Order": st.column_config.NumberColumn("Order", min_value=1, step=1),
            "Task_ID": st.column_config.TextColumn("Task ID", required=True),
            "Task_Type": st.column_config.SelectboxColumn(
                "Task Type",
                options=task_type_options,
                required=True,
                help="Select a production item for auto-duration, or a non-production task type with manual duration. Fieldwork is non-production and requires manual duration.",
            ),
            "Location_ID": st.column_config.TextColumn("Location ID"),
            "Investigation_Type": st.column_config.SelectboxColumn(
                "Investigation Type",
                options=INVESTIGATION_TYPE_OPTIONS,
                required=True,
            ),
            "Depth_m": st.column_config.NumberColumn(
                "Depth m",
                min_value=0.0,
            ),
            "Duration_days": st.column_config.NumberColumn(
                "Duration days",
                min_value=0.0,
                help="Set to 0 or blank to auto-calculate fieldwork duration from Depth_m / Production_per_day.",
            ),
            "Depends_On": st.column_config.SelectboxColumn(
                "Depends On",
                options=dependency_options,
                help="Select a prerequisite task. The current task will not start before this task is complete.",
            ),
            "Bar_Color": st.column_config.SelectboxColumn(
                "Bar Color",
                options=COLOR_OPTIONS,
                help="Select the Gantt bar colour.",
            ),
            "Access_Notes": st.column_config.TextColumn("Access Notes"),
        },
    )

    st.session_state.tasks_df = normalize_tasks_df(edited_tasks_df)


# --------------------------------------------------
# Tab 3: Program and Gantt
# --------------------------------------------------

with tab3:
    st.header("Program Generation")

    if st.button("Generate Program and Gantt Chart"):
        try:
            start = datetime.strptime(st.session_state.project_info["start_date"], "%Y-%m-%d").date()

            st.session_state.program_df = generate_program(
                st.session_state.tasks_df,
                st.session_state.rates_df,
                start,
                st.session_state.project_info["work_weekends"]
            )

            st.success("Program generated successfully.")

        except ValueError as e:
            st.error(str(e))

    if not st.session_state.program_df.empty:
        st.subheader("Generated Program")
        st.dataframe(st.session_state.program_df, use_container_width=True)

        plot_df = st.session_state.program_df.copy()
        plot_df = plot_df.sort_values("Order").reset_index(drop=True)

        # Numeric y-axis gives full control of bar position.
        # Each row is 1 unit high; bars use width=1 so adjacent task bars touch vertically.
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
                marker=dict(
                    color=row["Bar_Color"],
                    line=dict(width=0),
                ),
                text=[row["Bar_Label"]],
                textposition="inside",
                insidetextanchor="middle",
                customdata=[[ 
                    row["Task_ID"],
                    row["Task_Type"],
                    row["Location_ID"],
                    row["Investigation_Type"],
                    row["Depth_m"],
                    row["Duration_days"],
                    row["Depends_On"],
                    row["Access_Notes"],
                    finish_dt.strftime("%d-%b-%Y"),
                ]],
                hovertemplate=(
                    "Task ID: %{customdata[0]}<br>"
                    "Task Type: %{customdata[1]}<br>"
                    "Location ID: %{customdata[2]}<br>"
                    "Investigation Type: %{customdata[3]}<br>"
                    "Depth: %{customdata[4]} m<br>"
                    "Duration: %{customdata[5]} day(s)<br>"
                    "Depends On: %{customdata[6]}<br>"
                    "Start: %{base|%d-%b-%Y}<br>"
                    "Finish: %{customdata[8]}<br>"
                    "Access Notes: %{customdata[7]}"
                    "<extra></extra>"
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
        
        start_date = plot_df["Start"].min()
        finish_date = plot_df["Finish"].max()
        
        all_dates = pd.date_range(start_date, finish_date, freq="D")
        
        for d in all_dates:
            if d.weekday() >= 5:      # Saturday=5, Sunday=6
                fig.add_vrect(
                    x0=d,
                    x1=d + pd.Timedelta(days=1),
                    fillcolor="lightgrey",
                    opacity=0.25,
                    layer="below",
                    line_width=0,
                )

        if st.session_state.project_info.get("shade_public_holidays", True):
            public_holidays = get_public_holidays(
                start_date,
                finish_date,
                st.session_state.project_info.get("public_holiday_state", "VIC"),
                st.session_state.project_info.get("custom_public_holidays", ""),
            )

            chart_start_date = pd.to_datetime(start_date).date()
            chart_finish_date = pd.to_datetime(finish_date).date()

            for holiday_date, holiday_name in sorted(public_holidays.items()):
                if chart_start_date <= holiday_date <= chart_finish_date:
                    holiday_start = pd.to_datetime(holiday_date)

                    fig.add_vrect(
                        x0=holiday_start,
                        x1=holiday_start + pd.Timedelta(days=1),
                        fillcolor="red",
                        opacity=0.28,
                        layer="below",
                        line_width=0,
                    )

                    fig.add_annotation(
                        x=holiday_start + pd.Timedelta(hours=12),
                        y=n_tasks + 0.45,
                        text=str(holiday_name),
                        showarrow=False,
                        textangle=-90,
                        font=dict(size=8, color="red"),
                        yanchor="top",
                    )
        
        st.plotly_chart(fig, use_container_width=True)


# --------------------------------------------------
# Tab 4: Export / Save
# --------------------------------------------------

with tab4:
    st.header("Export and Save Project")

    project_package = {
        "project_info": st.session_state.project_info,
        "rates": st.session_state.rates_df.to_dict(orient="records"),
        "soil_lab_tests": st.session_state.soil_lab_df.to_dict(orient="records"),
        "rock_lab_tests": st.session_state.rock_lab_df.to_dict(orient="records"),
        "tasks": st.session_state.tasks_df.to_dict(orient="records"),
        "program": st.session_state.program_df.to_dict(orient="records") if not st.session_state.program_df.empty else [],
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
        st.session_state.rates_df = pd.DataFrame(loaded.get("rates", []))
        st.session_state.soil_lab_df = pd.DataFrame(loaded.get("soil_lab_tests", []))
        st.session_state.rock_lab_df = pd.DataFrame(loaded.get("rock_lab_tests", []))
        st.session_state.tasks_df = normalize_tasks_df(pd.DataFrame(loaded.get("tasks", [])))
        st.session_state.program_df = pd.DataFrame(loaded.get("program", []))

        st.success("Project loaded.")

    excel_bytes = dataframe_to_excel_bytes({
        "Rates": st.session_state.rates_df,
        "Soil Lab Tests": st.session_state.soil_lab_df,
        "Rock Lab Tests": st.session_state.rock_lab_df,
        "Tasks": st.session_state.tasks_df,
        "Program": st.session_state.program_df,
    })

    st.download_button(
        "Export Excel Program",
        data=excel_bytes,
        file_name="fieldwork_program_summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# --------------------------------------------------
# Tab 5: AI Guidance
# --------------------------------------------------

with tab5:
    st.header("AI Program Guidance")

    st.info(
        "Ask AI to review the current tasks and generated program. "
        "The AI provides guidance only; it does not automatically change the program."
    )

    col1, col2 = st.columns([2, 1])
    with col1:
        ai_model_name = st.text_input(
            "OpenAI model",
            value=st.session_state.project_info.get("ai_guidance_model", "gpt-5.5"),
            help="Use a model available to your OpenAI API key."
        )
    with col2:
        if st.button("Clear AI chat"):
            st.session_state.ai_messages = []

    st.session_state.project_info["ai_guidance_model"] = ai_model_name

    if st.session_state.program_df.empty:
        st.warning("Generate the program first so the AI can review the actual Gantt schedule.")

    for msg in st.session_state.ai_messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    suggested_questions = [
        "Does this program look realistic?",
        "What sequencing risks should I check?",
        "Are there any dependency issues or missing assumptions?",
        "How can I shorten the program without weekend work?",
    ]

    selected_question = st.selectbox(
        "Optional quick question",
        options=[""] + suggested_questions,
    )

    user_question = st.chat_input("Ask AI about the fieldwork program")

    if selected_question and st.button("Ask selected question"):
        user_question = selected_question

    if user_question:
        st.session_state.ai_messages.append({"role": "user", "content": user_question})

        with st.chat_message("user"):
            st.write(user_question)

        with st.chat_message("assistant"):
            with st.spinner("Reviewing program..."):
                try:
                    answer = ask_ai_for_program_guidance(
                        user_question=user_question,
                        project_info=st.session_state.project_info,
                        tasks_df=st.session_state.tasks_df,
                        rates_df=st.session_state.rates_df,
                        soil_lab_df=st.session_state.soil_lab_df,
                        rock_lab_df=st.session_state.rock_lab_df,
                        program_df=st.session_state.program_df,
                        model_name=ai_model_name,
                    )
                    st.write(answer)
                except Exception as e:
                    answer = f"AI guidance failed: {e}"
                    st.error(answer)

        st.session_state.ai_messages.append({"role": "assistant", "content": answer})
