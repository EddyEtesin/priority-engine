from __future__ import annotations

import html
import json
from pathlib import Path
from textwrap import dedent
from typing import Any

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# APPLICATION CONFIGURATION
# ============================================================

ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "data" / "warehouse" / "priority_engine.duckdb"

st.set_page_config(
    page_title="Priority Engine",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Portfolio design system. Keep these values aligned with the portfolio.
BG = "#FBF7F5"
ACCENT = "#FF4500"
INK = "#271111"
SOFT = "#F5EDE9"
CARD = "#FFFFFF"
BORDER = "#EEE3DE"
MUTED = "#806F69"
GREEN = "#2F7D4A"
YELLOW = "#F2C94C"
PURPLE = "#6B2D5C"
RED = "#C8321F"

PRIORITY_ORDER = ["P1", "P2", "P3", "P4"]
PRIORITY_COLORS = {
    "P1": RED,
    "P2": ACCENT,
    "P3": YELLOW,
    "P4": GREEN,
}

SLA_ORDER = ["breached", "at_risk", "on_track", "met"]
SLA_COLORS = {
    "met": GREEN,
    "breached": RED,
    "at_risk": ACCENT,
    "on_track": YELLOW,
}


# ============================================================
# VISUAL DESIGN
# ============================================================

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700;12..96,800&family=Instrument+Sans:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600&display=swap');

    :root {
        --bg: #FBF7F5;
        --accent: #FF4500;
        --ink: #271111;
        --soft: #F5EDE9;
        --card: #FFFFFF;
        --border: #EEE3DE;
        --muted: #806F69;
    }

    .stApp {
        background: var(--bg);
        color: var(--ink);
        font-family: 'Instrument Sans', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(251, 247, 245, 0.94);
    }

    .block-container {
        max-width: 1580px;
        padding-top: 1.35rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3, h4 {
        font-family: 'Bricolage Grotesque', sans-serif !important;
        color: var(--ink) !important;
        letter-spacing: -0.035em;
    }

    p, label {
        font-family: 'Instrument Sans', sans-serif;
    }

    code, .mono {
        font-family: 'Geist Mono', monospace !important;
    }

    /* Sidebar shell */
    section[data-testid="stSidebar"] {
        width: 315px !important;
        min-width: 315px !important;
    }

    [data-testid="stSidebar"] {
        background: #F5EDE9 !important;
        border-right: 1px solid #EEE3DE;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding: 1.25rem 0.95rem 2rem;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        color: #271111;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] {
        background: #FFFFFF !important;
        border: 1px solid #EEE3DE !important;
        border-radius: 12px !important;
        margin-bottom: 9px;
        overflow: hidden;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] details,
    [data-testid="stSidebar"] [data-testid="stExpander"] details > div {
        background: #FFFFFF !important;
        color: #271111 !important;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        background: #FFFFFF !important;
        color: #271111 !important;
        padding: 12px 13px !important;
        font-family: 'Bricolage Grotesque', sans-serif !important;
        font-weight: 700 !important;
        font-size: 0.84rem !important;
    }

    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: #FF4500 !important;
    }

    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] label {
        color: #806F69 !important;
        font-size: 0.74rem !important;
        font-weight: 600 !important;
    }

    /* BaseWeb select and multiselect surfaces */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #FFFFFF !important;
        color: #271111 !important;
        border-color: #E8D9D2 !important;
        border-radius: 9px !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] input {
        background: transparent !important;
        color: #271111 !important;
        -webkit-text-fill-color: #271111 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background: #F5EDE9 !important;
        border: 1px solid #E8D9D2 !important;
        border-radius: 6px !important;
        color: #603E35 !important;
    }

    [data-testid="stSidebar"] [data-baseweb="tag"] span {
        color: #603E35 !important;
    }

    /* Date and text controls: use the full expander content width. */
    [data-testid="stSidebar"] [data-testid="stDateInput"],
    [data-testid="stSidebar"] [data-testid="stTextInput"] {
        width: 100% !important;
        min-width: 0 !important;
    }

    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-testid="stDateInput"] [data-baseweb="input"] > div,
    [data-testid="stSidebar"] [data-testid="stTextInput"] [data-baseweb="input"],
    [data-testid="stSidebar"] [data-testid="stTextInput"] [data-baseweb="input"] > div {
        width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        background: #FFFFFF !important;
        border: 1px solid #E8D9D2 !important;
        border-radius: 9px !important;
        box-shadow: none !important;
    }

    [data-testid="stSidebar"] [data-testid="stDateInput"] input,
    [data-testid="stSidebar"] [data-testid="stTextInput"] input {
        width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
        background: transparent !important;
        color: #271111 !important;
        -webkit-text-fill-color: #271111 !important;
        border: 0 !important;
        border-radius: 9px !important;
        padding-left: 11px !important;
        padding-right: 9px !important;
        color-scheme: light !important;
    }

    [data-testid="stSidebar"] [data-testid="stDateInput"] svg {
        color: #806F69 !important;
        fill: #806F69 !important;
    }

    [data-testid="stSidebar"] [data-testid="stCheckbox"] label,
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
        color: #806F69 !important;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button {
        background: #FFFFFF !important;
        color: #271111 !important;
        border: 1px solid #E8D9D2 !important;
        border-radius: 9px !important;
        min-height: 39px;
        font-weight: 600;
    }

    [data-testid="stSidebar"] [data-testid="stButton"] button:hover {
        background: #FFF0EB !important;
        border-color: #FF4500 !important;
        color: #C8321F !important;
    }

    /* Dropdown popovers */
    [data-baseweb="popover"],
    [data-baseweb="menu"],
    ul[role="listbox"] {
        background: #FFFFFF !important;
        color: #271111 !important;
    }

    li[role="option"] {
        color: #271111 !important;
    }

    li[role="option"]:hover {
        background: #FFF0EB !important;
    }

    /* Brand and sidebar copy */
    .brand-mark {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 1.25rem;
    }

    .brand-icon {
        width: 38px;
        height: 38px;
        border-radius: 11px;
        background: #FF4500;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 700;
        flex: 0 0 38px;
    }

    .brand-name {
        font-family: 'Bricolage Grotesque', sans-serif;
        font-size: 1.1rem;
        font-weight: 800;
        color: #271111;
        line-height: 1.1;
    }

    .brand-subtitle {
        font-family: 'Geist Mono', monospace;
        font-size: 0.60rem;
        color: #806F69;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .sidebar-kicker, .eyebrow {
        font-family: 'Geist Mono', monospace;
        font-size: 0.65rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #FF4500;
        font-weight: 600;
        margin-bottom: 7px;
    }

    .sidebar-intro {
        font-size: 0.77rem;
        line-height: 1.6;
        color: #806F69;
        margin: 8px 0 16px;
    }

    .sidebar-footer {
        border-top: 1px solid #E5D8D1;
        margin-top: 17px;
        padding-top: 14px;
        font-size: 0.68rem;
        line-height: 1.7;
        color: #806F69;
    }

    /* Introduction */
    .hero-shell {
        background: #F5EDE9;
        border: 1px solid #EEE3DE;
        border-radius: 18px;
        padding: 26px 29px;
        margin-bottom: 17px;
        position: relative;
        overflow: hidden;
    }

    .hero-shell:before {
        content: "";
        position: absolute;
        width: 5px;
        height: 100%;
        left: 0;
        top: 0;
        background: #FF4500;
    }

    .hero-title {
        font-family: 'Bricolage Grotesque', sans-serif;
        font-size: clamp(2rem, 3.3vw, 3.05rem);
        line-height: 1.04;
        letter-spacing: -0.06em;
        font-weight: 800;
        color: #271111;
        max-width: 850px;
        margin: 10px 0;
    }

    .hero-title span {
        color: #FF4500;
    }

    .hero-description {
        max-width: 850px;
        font-size: 0.88rem;
        line-height: 1.72;
        color: #806F69;
        margin-top: 11px;
    }

    .pipeline {
        display: grid;
        grid-template-columns: repeat(5, minmax(0, 1fr));
        gap: 8px;
        margin-top: 22px;
    }

    .pipeline-step {
        background: #FFFFFF;
        border: 1px solid #EEE3DE;
        border-radius: 10px;
        padding: 10px 11px;
    }

    .pipeline-number {
        font-family: 'Geist Mono', monospace;
        font-size: 0.59rem;
        color: #FF4500;
    }

    .pipeline-name {
        font-family: 'Bricolage Grotesque', sans-serif;
        font-size: 0.81rem;
        font-weight: 700;
        color: #271111;
        margin-top: 5px;
    }

    .pipeline-detail {
        font-size: 0.64rem;
        color: #806F69;
        margin-top: 3px;
    }

    /* Dashboard elements */
    [data-testid="stTabs"] {
        margin-top: 1.05rem;
    }

    [data-testid="stTabs"] button {
        font-family: 'Instrument Sans', sans-serif;
        font-weight: 600;
        color: #806F69;
    }

    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #FF4500;
        border-bottom-color: #FF4500;
    }

    .snapshot-pill {
        display: inline-block;
        padding: 6px 10px;
        border: 1px solid #EEE3DE;
        border-radius: 30px;
        background: #FFFFFF;
        color: #806F69;
        font-family: 'Geist Mono', monospace;
        font-size: 0.63rem;
    }

    /* Priority classification key */
    .priority-key {
        background: #FFFFFF;
        border: 1px solid #EEE3DE;
        border-radius: 11px;
        padding: 12px 13px;
        min-height: 82px;
    }

    .priority-key-label {
        display: flex;
        align-items: center;
        gap: 7px;
        color: #271111;
        font-family: 'Bricolage Grotesque', sans-serif;
        font-size: 0.88rem;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .priority-key-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
        flex: 0 0 9px;
    }

    .priority-key-detail {
        color: #806F69;
        font-size: 0.69rem;
        line-height: 1.45;
    }

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #EEE3DE;
        border-radius: 14px;
        padding: 15px 15px 13px;
        min-height: 116px;
        box-shadow: 0 2px 8px rgba(39, 17, 17, 0.025);
    }

    .metric-label {
        font-size: 0.73rem;
        font-weight: 600;
        color: #806F69;
        margin-bottom: 11px;
    }

    .metric-value {
        font-family: 'Bricolage Grotesque', sans-serif;
        color: #271111;
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.06em;
        line-height: 1;
    }

    .metric-note {
        color: #806F69;
        font-size: 0.67rem;
        line-height: 1.4;
        margin-top: 10px;
    }

    .metric-accent { border-top: 3px solid #FF4500; }
    .metric-green { border-top: 3px solid #2F7D4A; }
    .metric-red { border-top: 3px solid #C8321F; }
    .metric-yellow { border-top: 3px solid #F2C94C; }

    .section-heading {
        font-family: 'Bricolage Grotesque', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        letter-spacing: -0.035em;
        color: #271111;
        margin: 1rem 0 3px;
    }

    .section-description {
        color: #806F69;
        font-size: 0.77rem;
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }

    .ticket-panel {
        background: #FFFFFF;
        border: 1px solid #EEE3DE;
        border-radius: 14px;
        padding: 17px;
    }

    .ticket-id {
        font-family: 'Geist Mono', monospace;
        color: #FF4500;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .ticket-description {
        color: #271111;
        font-size: 0.87rem;
        line-height: 1.65;
        margin-top: 12px;
    }

    .tag {
        display: inline-block;
        padding: 5px 8px;
        border-radius: 7px;
        margin: 3px 4px 3px 0;
        font-family: 'Geist Mono', monospace;
        font-size: 0.63rem;
        text-transform: uppercase;
        font-weight: 600;
        background: #F5EDE9;
        color: #271111;
    }

    .footer-note {
        border-top: 1px solid #EEE3DE;
        padding-top: 15px;
        margin-top: 2rem;
        color: #806F69;
        font-size: 0.68rem;
        line-height: 1.6;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #EEE3DE;
        border-radius: 11px;
        overflow: hidden;
    }

    .stAlert {
        border-radius: 11px;
    }

    [data-testid="stDownloadButton"] button {
        background: #FFFFFF;
        color: #271111;
        border: 1px solid #EEE3DE;
        border-radius: 9px;
    }

    @media (max-width: 950px) {
        .pipeline {
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }
        .hero-shell {
            padding: 21px 18px;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_html(markup: str) -> None:
    """Render HTML without Markdown's indented-code-block interpretation."""
    cleaned = dedent(markup).strip()
    st.markdown(cleaned, unsafe_allow_html=True)


# ============================================================
# DATA ACCESS
# ============================================================


@st.cache_data(ttl=60, show_spinner="Loading Priority Engine data...")
def load_data(database_path: str, database_mtime: float) -> pd.DataFrame:
    """Load the dbt fact model from DuckDB."""
    del database_mtime  # Included in the cache key to refresh after dbt rebuilds.

    connection = duckdb.connect(database_path, read_only=True)
    try:
        data = connection.execute(
            "SELECT * FROM analytics_marts.fct_support_tickets"
        ).df()
    finally:
        connection.close()

    if data.empty:
        return data

    datetime_columns = [
        "created_at",
        "updated_at",
        "first_response_at",
        "resolved_at",
        "snapshot_at",
        "first_response_due_at",
        "resolution_due_at",
    ]
    for column in datetime_columns:
        if column in data.columns:
            data[column] = pd.to_datetime(
                data[column], utc=True, errors="coerce"
            )

    numeric_columns = [
        "priority_score",
        "severity_points",
        "impact_points",
        "customer_tier_points",
        "reopened_points",
        "csat_score",
        "reopened_count",
        "first_response_elapsed_hours",
        "resolution_elapsed_hours",
        "first_response_minutes_remaining",
        "resolution_minutes_remaining",
        "actual_first_response_hours",
        "actual_resolution_hours",
        "ticket_age_hours",
        "first_response_target_hours",
        "resolution_target_hours",
    ]
    for column in numeric_columns:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    boolean_columns = [
        "is_open_ticket",
        "is_resolved",
        "is_assigned",
        "is_reopened",
    ]
    for column in boolean_columns:
        if column in data.columns:
            data[column] = data[column].fillna(False).astype(bool)

    return data


# ============================================================
# GENERAL HELPERS
# ============================================================


def value_options(data: pd.DataFrame, column: str) -> list[str]:
    if column not in data.columns:
        return []
    return sorted(data[column].dropna().astype(str).unique().tolist())


def format_number(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.0f}"


def format_decimal(value: Any, places: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:,.{places}f}"


def format_percentage(value: Any) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.1f}%"


def safe_text(value: Any, fallback: str = "Not recorded") -> str:
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except (TypeError, ValueError):
        pass
    text_value = str(value).strip()
    return text_value if text_value else fallback


def sla_compliance(series: pd.Series) -> float:
    """Met divided by final SLA outcomes (met + breached)."""
    eligible = series.isin(["met", "breached"])
    if not eligible.any():
        return float("nan")
    return round((series[eligible] == "met").mean() * 100, 1)


def sla_compliance_details(series: pd.Series) -> tuple[int, int, float]:
    met = int((series == "met").sum())
    breached = int((series == "breached").sum())
    denominator = met + breached
    percentage = round(met / denominator * 100, 1) if denominator else float("nan")
    return met, breached, percentage


def metric_card(
    label: str,
    value: str,
    note: str,
    style: str = "metric-accent",
) -> None:
    render_html(
        f"""
        <div class="metric-card {html.escape(style)}">
            <div class="metric-label">{html.escape(label)}</div>
            <div class="metric-value">{html.escape(value)}</div>
            <div class="metric-note">{html.escape(note)}</div>
        </div>
        """
    )


def section_heading(title: str, description: str = "") -> None:
    render_html(
        f"""
        <div class="section-heading">{html.escape(title)}</div>
        <div class="section-description">{html.escape(description)}</div>
        """
    )


def style_chart(fig: Any, height: int = 320) -> Any:
    fig.update_layout(
        height=height,
        font={"family": "Instrument Sans", "color": INK, "size": 12},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin={"l": 12, "r": 12, "t": 34, "b": 12},
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {
                "family": "Instrument Sans",
                "size": 11,
                "color": INK,
            },
            "title_font": {
                "family": "Instrument Sans",
                "size": 11,
                "color": INK,
            },
        },
        hoverlabel={
            "bgcolor": "#FFFFFF",
            "bordercolor": "#E8D9D2",
            "font": {
                "family": "Instrument Sans",
                "size": 13,
                "color": INK,
            },
            "align": "left",
            "namelength": -1,
        },
    )
    # Explicit axis typography overrides low-contrast Plotly/Streamlit defaults.
    # This keeps tick labels and axis titles readable on the cream background.
    axis_tick_style = {
        "family": "Instrument Sans",
        "size": 12,
        "color": INK,
    }
    axis_title_style = {
        "family": "Instrument Sans",
        "size": 12,
        "color": INK,
    }

    fig.update_xaxes(
        showgrid=False,
        linecolor=BORDER,
        zeroline=False,
        tickfont=axis_tick_style,
        title_font=axis_title_style,
        automargin=True,
        ticks="outside",
        tickcolor=BORDER,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=BORDER,
        zeroline=False,
        tickfont=axis_tick_style,
        title_font=axis_title_style,
        automargin=True,
        ticks="outside",
        tickcolor=BORDER,
    )

    # Make any text labels drawn on the chart readable as well.
    for trace in fig.data:
        if getattr(trace, "text", None) is not None:
            trace.textfont = {
                "family": "Instrument Sans",
                "size": 12,
                "color": INK,
            }

    return fig


def show_chart(fig: Any, key: str) -> None:
    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            # Hide the camera, zoom, pan and fullscreen toolbar completely.
            # Hover labels and the chart itself remain interactive.
            "displayModeBar": False,
            "displaylogo": False,
            "scrollZoom": False,
            "responsive": True,
        },
        key=key,
    )


def format_timestamp(value: Any) -> str:
    if value is None:
        return "Not recorded"
    try:
        if pd.isna(value):
            return "Not recorded"
    except (TypeError, ValueError):
        pass
    return pd.to_datetime(value, utc=True).strftime("%d %b %Y, %H:%M UTC")


def empty_message(message: str) -> None:
    st.info(message)


def export_button(
    data: pd.DataFrame,
    filename: str,
    key: str,
    label: str = "↓  Export CSV",
) -> None:
    st.download_button(
        label=label,
        data=data.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        key=key,
    )


def reset_filters(defaults: dict[str, Any]) -> None:
    """Reset widget state before Streamlit rebuilds the page."""
    for key, value in defaults.items():
        st.session_state[key] = value


def json_safe_record(record: pd.Series) -> str:
    """Convert pandas and NumPy scalar values into valid JSON."""
    output: dict[str, Any] = {}
    for column, value in record.items():
        if value is None:
            output[column] = None
            continue
        try:
            if pd.isna(value):
                output[column] = None
                continue
        except (TypeError, ValueError):
            pass

        if isinstance(value, pd.Timestamp):
            output[column] = value.isoformat()
        elif hasattr(value, "item"):
            output[column] = value.item()
        else:
            output[column] = value

    return json.dumps(
        output,
        indent=2,
        ensure_ascii=False,
        allow_nan=False,
    )


# ============================================================
# LOAD AND VALIDATE DATA
# ============================================================

if not DB_PATH.exists():
    st.error("The Priority Engine database could not be found.")
    st.code(str(DB_PATH))
    st.info("Run the Python ingestion pipeline and dbt build first.")
    st.stop()

try:
    tickets = load_data(str(DB_PATH), DB_PATH.stat().st_mtime)
except Exception as error:
    st.error("The dashboard could not read the dbt fact table.")
    st.exception(error)
    st.info(
        "Check that analytics_marts.fct_support_tickets exists "
        "in your DuckDB database."
    )
    st.stop()

if tickets.empty:
    st.warning("The fact table contains no tickets.")
    st.stop()

required_columns = {
    "ticket_id",
    "customer_id",
    "agent_id",
    "category",
    "customer_tier",
    "channel",
    "severity",
    "status",
    "priority_score",
    "priority_band",
    "created_at",
    "is_open_ticket",
    "is_assigned",
    "is_reopened",
    "first_response_sla_status",
    "resolution_sla_status",
}

missing_columns = required_columns.difference(tickets.columns)
if missing_columns:
    st.error(
        "The fact table is missing required columns: "
        + ", ".join(sorted(missing_columns))
    )
    st.stop()

valid_created_dates = tickets["created_at"].dropna()
if valid_created_dates.empty:
    st.error("No valid ticket creation timestamps are available.")
    st.stop()

# Date limits must be defined before the date filter is initialised.
min_date = valid_created_dates.dt.date.min()
max_date = valid_created_dates.dt.date.max()

snapshot_value = (
    tickets["snapshot_at"].dropna().max()
    if "snapshot_at" in tickets.columns
    else pd.NaT
)
snapshot_label = format_timestamp(snapshot_value)


# ============================================================
# SIDEBAR FILTERS
# ============================================================

priority_options = value_options(tickets, "priority_band")
severity_options = value_options(tickets, "severity")
status_options = value_options(tickets, "status")
category_options = value_options(tickets, "category")
tier_options = value_options(tickets, "customer_tier")
channel_options = value_options(tickets, "channel")
agent_options = value_options(tickets, "agent_id")

# Empty multiselect defaults mean "all". This avoids a sidebar full of chips.
filter_defaults: dict[str, Any] = {
    "filter_start_date": min_date,
    "filter_end_date": max_date,
    "filter_priorities": [],
    "filter_severities": [],
    "filter_statuses": [],
    "filter_categories": [],
    "filter_tiers": [],
    "filter_channels": [],
    "filter_agents": [],
    "filter_include_unassigned": True,
    "filter_sla_measure": "First response",
    "filter_sla_status": "All",
    "filter_search": "",
}

for key, default_value in filter_defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value
    elif isinstance(default_value, list):
        # Remove selections that no longer exist in the current data snapshot.
        allowed_values = {
            "filter_priorities": priority_options,
            "filter_severities": severity_options,
            "filter_statuses": status_options,
            "filter_categories": category_options,
            "filter_tiers": tier_options,
            "filter_channels": channel_options,
            "filter_agents": agent_options,
        }[key]
        st.session_state[key] = [
            value for value in st.session_state[key] if value in allowed_values
        ]

with st.sidebar:
    render_html(
        """
        <div class="brand-mark">
            <div class="brand-icon">◈</div>
            <div>
                <div class="brand-name">Priority Engine</div>
                <div class="brand-subtitle">Support intelligence</div>
            </div>
        </div>
        <div class="sidebar-kicker">Workspace / Filters</div>
        <div class="sidebar-intro">
            Focus the analysis by date, ticket attributes, assignment or
            service-level outcome. All dashboard sections update together.
        </div>
        """
    )

    st.button(
        "↺  Reset all filters",
        use_container_width=True,
        on_click=reset_filters,
        args=(filter_defaults,),
        key="reset_all_filters",
    )

    with st.expander("01  /  Time period", expanded=True):
        st.date_input(
            "From",
            min_value=min_date,
            max_value=max_date,
            key="filter_start_date",
            format="YYYY-MM-DD",
            help="Start of the ticket creation period (UTC).",
        )
        st.date_input(
            "To",
            min_value=min_date,
            max_value=max_date,
            key="filter_end_date",
            format="YYYY-MM-DD",
            help="End of the ticket creation period (UTC).",
        )

    start_date = st.session_state["filter_start_date"]
    end_date = st.session_state["filter_end_date"]

    # Handle an invalid interval without mutating an already-rendered widget.
    if start_date > end_date:
        st.warning(
            "The start date is after the end date. The dashboard is showing "
            "the start date only until the interval is corrected."
        )
        end_date = start_date

    with st.expander("02  /  Ticket attributes", expanded=False):
        selected_priorities = st.multiselect(
            "Priority",
            options=priority_options,
            key="filter_priorities",
            placeholder="All priorities",
        )
        selected_severities = st.multiselect(
            "Severity",
            options=severity_options,
            key="filter_severities",
            placeholder="All severities",
        )
        selected_statuses = st.multiselect(
            "Ticket status",
            options=status_options,
            key="filter_statuses",
            placeholder="All statuses",
        )
        selected_categories = st.multiselect(
            "Category",
            options=category_options,
            key="filter_categories",
            placeholder="All categories",
        )
        selected_tiers = st.multiselect(
            "Customer tier",
            options=tier_options,
            key="filter_tiers",
            placeholder="All customer tiers",
        )
        selected_channels = st.multiselect(
            "Support channel",
            options=channel_options,
            key="filter_channels",
            placeholder="All channels",
        )

    with st.expander("03  /  Assignment", expanded=False):
        selected_agents = st.multiselect(
            "Assigned agent",
            options=agent_options,
            key="filter_agents",
            placeholder="All agents",
        )
        include_unassigned = st.checkbox(
            "Include unassigned tickets",
            key="filter_include_unassigned",
        )

    with st.expander("04  /  SLA monitoring", expanded=False):
        sla_measure = st.selectbox(
            "SLA measure",
            options=["First response", "Resolution"],
            key="filter_sla_measure",
        )
        sla_filter = st.selectbox(
            "SLA status",
            options=["All", "breached", "at_risk", "on_track", "met"],
            key="filter_sla_status",
        )
        st.caption(
            "Filter by first-response or resolution outcome."
        )

    sla_column = (
        "first_response_sla_status"
        if sla_measure == "First response"
        else "resolution_sla_status"
    )

    with st.expander("05  /  Find a ticket", expanded=False):
        search_term = st.text_input(
            "Search records",
            placeholder="Ticket ID, customer or description",
            key="filter_search",
        )

    render_html(
        """
        <div class="sidebar-footer">
            <b>PROJECT 09</b><br>
            Rule-based prioritisation<br>
            SLA monitoring<br>
            Operational analytics<br><br>
            Built with Python, DuckDB, dbt and Streamlit.
        </div>
        """
    )


# ============================================================
# APPLY GLOBAL FILTERS
# ============================================================

filtered = tickets.copy()
created_dates = filtered["created_at"].dt.date
filtered = filtered.loc[created_dates.between(start_date, end_date)]

attribute_filters = [
    ("priority_band", selected_priorities),
    ("severity", selected_severities),
    ("status", selected_statuses),
    ("category", selected_categories),
    ("customer_tier", selected_tiers),
    ("channel", selected_channels),
]

for column, selected_values in attribute_filters:
    if selected_values:
        filtered = filtered.loc[
            filtered[column].astype("string").isin(selected_values)
        ]

# Empty agent selection means all agents. Unassigned tickets are controlled
# independently so they are not accidentally removed by a null cast.
if selected_agents:
    agent_mask = (
        filtered["agent_id"].astype("string").isin(selected_agents)
    )
    if include_unassigned:
        agent_mask |= filtered["agent_id"].isna()
else:
    agent_mask = pd.Series(True, index=filtered.index)
    if not include_unassigned:
        agent_mask &= filtered["agent_id"].notna()

filtered = filtered.loc[agent_mask]

if sla_filter != "All":
    filtered = filtered.loc[filtered[sla_column] == sla_filter]

if search_term.strip():
    searchable_columns = [
        column
        for column in [
            "ticket_id",
            "customer_id",
            "agent_id",
            "description",
            "category",
        ]
        if column in filtered.columns
    ]
    search_mask = pd.Series(False, index=filtered.index)
    for column in searchable_columns:
        search_mask |= (
            filtered[column]
            .fillna("")
            .astype(str)
            .str.contains(search_term.strip(), case=False, regex=False)
        )
    filtered = filtered.loc[search_mask]

filtered = filtered.copy()


# ============================================================
# PROJECT INTRODUCTION
# ============================================================

pipeline_items = [
    ("01 / INGEST", "Collect", "Python pipeline"),
    ("02 / STORE", "Organise", "DuckDB warehouse"),
    ("03 / TRANSFORM", "Model", "dbt transformations"),
    ("04 / EVALUATE", "Prioritise", "Priority and SLA rules"),
    ("05 / ANALYSE", "Act", "Operational dashboard"),
]

pipeline_html = "".join(
    f"""
    <div class="pipeline-step">
        <div class="pipeline-number">{html.escape(number)}</div>
        <div class="pipeline-name">{html.escape(name)}</div>
        <div class="pipeline-detail">{html.escape(detail)}</div>
    </div>
    """
    for number, name, detail in pipeline_items
)

render_html(
    f"""
    <div class="hero-shell">
        <div class="eyebrow">Project 09 / Customer support operations</div>
        <div class="hero-title">
            From support requests<br>
            to <span>prioritised action.</span>
        </div>
        <div class="hero-description">
            Support teams receive requests with different levels of urgency,
            customer impact and service expectations. When every ticket enters
            the same queue, teams can struggle to identify which issues need
            attention first.
            <br><br>
            Priority Engine turns raw support-ticket records into a ranked
            workload. It applies transparent priority rules, monitors first-
            response and resolution commitments, and brings the results into
            one operational workspace.
        </div>
        <div class="pipeline">{pipeline_html}</div>
    </div>
    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;
                gap:8px;margin:0 2px 15px;">
        <span class="snapshot-pill">● SYNTHETIC DATASET</span>
        <span class="snapshot-pill">SNAPSHOT · {html.escape(snapshot_label)}</span>
    </div>
    """
)

st.caption(
    f"Showing {len(filtered):,} of {len(tickets):,} tickets "
    "after applying the selected filters."
)

if filtered.empty:
    st.warning(
        "No tickets match the selected filters. Adjust the sidebar filters "
        "or reset them to return to the full dataset."
    )
    st.stop()


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_tickets = len(filtered)
open_tickets = int(filtered["is_open_ticket"].sum())
urgent_open_tickets = int(
    (
        filtered["is_open_ticket"]
        & filtered["priority_band"].isin(["P1", "P2"])
    ).sum()
)

first_met, first_breached, first_compliance = sla_compliance_details(
    filtered["first_response_sla_status"]
)
resolution_met, resolution_breached, resolution_compliance = (
    sla_compliance_details(filtered["resolution_sla_status"])
)

first_at_risk = int(
    (filtered["first_response_sla_status"] == "at_risk").sum()
)
resolution_at_risk = int(
    (filtered["resolution_sla_status"] == "at_risk").sum()
)
average_csat = (
    filtered["csat_score"].mean()
    if "csat_score" in filtered.columns
    else float("nan")
)


# ============================================================
# DASHBOARD NAVIGATION
# ============================================================

overview_tab, queue_tab, sla_tab, performance_tab, explorer_tab = st.tabs(
    [
        "◈  Overview",
        "↗  Priority queue",
        "◷  SLA monitor",
        "▤  Performance",
        "⌕  Ticket explorer",
    ]
)


# ============================================================
# TAB 1: OVERVIEW
# ============================================================

with overview_tab:
    render_html('<div class="eyebrow">Operational overview</div>')

    kpi_columns = st.columns(5, gap="medium")

    with kpi_columns[0]:
        metric_card(
            "Total tickets",
            format_number(total_tickets),
            "Tickets in this filtered view",
            "metric-accent",
        )
    with kpi_columns[1]:
        open_pct = open_tickets / total_tickets * 100 if total_tickets else 0
        metric_card(
            "Open workload",
            format_number(open_tickets),
            f"{open_pct:.1f}% of filtered tickets",
            "metric-yellow",
        )
    with kpi_columns[2]:
        metric_card(
            "Urgent open",
            format_number(urgent_open_tickets),
            "P1 and P2 tickets still open",
            "metric-red",
        )
    with kpi_columns[3]:
        metric_card(
            "First response SLA",
            format_percentage(first_compliance),
            f"{first_met:,} met · {first_breached:,} breached",
            "metric-green",
        )
    with kpi_columns[4]:
        metric_card(
            "Resolution SLA",
            format_percentage(resolution_compliance),
            f"{resolution_met:,} met · {resolution_breached:,} breached",
            "metric-green",
        )

    # Keep the priority key outside the plotting area so it is visible
    # before a reader interprets the bars.
    st.markdown(" ")
    section_heading(
        "Priority guide",
        "The colours and thresholds used to classify each ticket.",
    )

    priority_definitions = [
        ("P1", "Critical", "Critical severity or score ≥ 120", RED),
        ("P2", "High", "Score from 85 to 119", ACCENT),
        ("P3", "Standard", "Score from 45 to 84", "#C49A16"),
        ("P4", "Low", "Score below 45", GREEN),
    ]

    priority_key_columns = st.columns(4, gap="small")
    for index, (band, label, detail, color) in enumerate(priority_definitions):
        with priority_key_columns[index]:
            render_html(
                f"""
                <div class="priority-key">
                    <div class="priority-key-label">
                        <span class="priority-key-dot" style="background:{color};"></span>
                        {band} · {label}
                    </div>
                    <div class="priority-key-detail">{html.escape(detail)}</div>
                </div>
                """
            )

    st.markdown(" ")
    chart_left, chart_right = st.columns(2, gap="large")

    # Chart 1: priority distribution
    with chart_left:
        section_heading(
            "Where attention is needed",
            "Distribution of tickets across the priority framework.",
        )
        priority_labels = {
            "P1": "Critical",
            "P2": "High",
            "P3": "Standard",
            "P4": "Low",
        }
        priority_rules = {
            "P1": "Critical severity or score ≥ 120",
            "P2": "Score from 85 to 119",
            "P3": "Score from 45 to 84",
            "P4": "Score below 45",
        }

        priority_counts = (
            filtered["priority_band"]
            .value_counts()
            .reindex(PRIORITY_ORDER, fill_value=0)
            .rename_axis("priority_band")
            .reset_index(name="tickets")
        )
        priority_counts["share"] = (
            priority_counts["tickets"] / max(total_tickets, 1) * 100
        )
        priority_counts["priority_label"] = priority_counts[
            "priority_band"
        ].map(priority_labels)
        priority_counts["priority_rule"] = priority_counts[
            "priority_band"
        ].map(priority_rules)

        fig = px.bar(
            priority_counts,
            x="tickets",
            y="priority_band",
            orientation="h",
            color="priority_band",
            color_discrete_map=PRIORITY_COLORS,
            text="tickets",
            custom_data=[
                "priority_label",
                "share",
                "priority_rule",
            ],
            category_orders={"priority_band": ["P4", "P3", "P2", "P1"]},
        )
        fig.update_traces(
            textposition="outside",
            marker_line_width=0,
            hovertemplate=(
                "<span style='color:#FF4500;font-size:10px;letter-spacing:1px;'>"
                "<b>PRIORITY BAND · %{y}</b></span><br>"
                "<span style='font-size:17px;'><b>%{customdata[0]}</b></span>"
                "<br><br>"
                "<b>%{x:,.0f} tickets</b><br>"
                "%{customdata[1]:.1f}% of filtered workload<br>"
                "<span style='color:#806F69;'>%{customdata[2]}</span>"
                "<extra></extra>"
            ),
        )
        fig.update_layout(
            showlegend=False,
            xaxis_title="Number of tickets",
            yaxis_title=None,
        )
        show_chart(style_chart(fig, 305), "overview_priority")

    # Chart 2: daily ticket volume
    with chart_right:
        section_heading(
            "Incoming support demand",
            "Daily ticket creation during the selected period.",
        )
        trend = (
            filtered.set_index("created_at")
            .resample("D")
            .size()
            .reset_index(name="tickets")
        )
        trend["rolling_7_day_average"] = (
            trend["tickets"].rolling(window=7, min_periods=1).mean()
        )
        fig = px.area(
            trend,
            x="created_at",
            y="tickets",
            markers=True,
            custom_data=["rolling_7_day_average"],
        )
        fig.update_traces(
            line={"color": ACCENT, "width": 2.5},
            fillcolor="rgba(255,69,0,0.10)",
            marker={"color": ACCENT, "size": 5},
            hoverlabel={
                "bgcolor": "#FFFFFF",
                "bordercolor": "#E8D9D2",
                "font": {
                    "family": "Instrument Sans",
                    "size": 13,
                    "color": INK,
                },
                "align": "left",
                "namelength": -1,
            },
            hovertemplate=(
                "<span style='color:#FF4500;font-size:10px;letter-spacing:1px;'>"
                "<b>SUPPORT DEMAND</b></span><br>"
                "<span style='font-size:15px;'><b>%{x|%a, %d %b %Y}</b></span>"
                "<br><br>"
                "<b>%{y:,.0f} tickets created</b><br>"
                "7-day average: %{customdata[0]:.1f} tickets/day"
                "<extra></extra>"
            ),
        )
        fig.update_layout(
            xaxis_title=None,
            yaxis_title="Tickets created",
        )
        show_chart(style_chart(fig, 305), "overview_trend")

    st.markdown(" ")
    section_heading(
        "Operational signals",
        "A compact view of issues that can require management attention.",
    )

    unassigned_open = int(
        (filtered["is_open_ticket"] & ~filtered["is_assigned"]).sum()
    )
    reopened_total = int(filtered["is_reopened"].sum())

    signal_columns = st.columns(4, gap="medium")
    with signal_columns[0]:
        metric_card(
            "First response breaches",
            format_number(first_breached),
            "Late or overdue",
            "metric-red",
        )
    with signal_columns[1]:
        metric_card(
            "Resolution breaches",
            format_number(resolution_breached),
            "Late or overdue",
            "metric-red",
        )
    with signal_columns[2]:
        metric_card(
            "Unassigned open",
            format_number(unassigned_open),
            "Open tickets without an agent",
            "metric-yellow",
        )
    with signal_columns[3]:
        metric_card(
            "Reopened tickets",
            format_number(reopened_total),
            "At least one reopening",
            "metric-accent",
        )

    st.markdown(" ")
    experience_left, experience_right = st.columns(2, gap="large")

    with experience_left:
        section_heading(
            "Customer experience",
            "Satisfaction scores where a response was recorded.",
        )
        csat_columns = st.columns(2)
        with csat_columns[0]:
            metric_card(
                "Average CSAT",
                format_decimal(average_csat, 2),
                "Scale: 1 to 5",
                "metric-yellow",
            )
        with csat_columns[1]:
            csat_count = (
                int(filtered["csat_score"].count())
                if "csat_score" in filtered.columns
                else 0
            )
            metric_card(
                "CSAT responses",
                format_number(csat_count),
                "Recorded survey responses",
                "metric-accent",
            )

    with experience_right:
        section_heading(
            "Tickets approaching deadlines",
            "Tickets currently marked at risk by the SLA rules.",
        )
        risk_columns = st.columns(2)
        with risk_columns[0]:
            metric_card(
                "First response at risk",
                format_number(first_at_risk),
                "Response target nearing",
                "metric-red",
            )
        with risk_columns[1]:
            metric_card(
                "Resolution at risk",
                format_number(resolution_at_risk),
                "Resolution target nearing",
                "metric-red",
            )

    st.markdown(" ")
    render_html(
        """
        <div class="ticket-panel">
            <div class="eyebrow">How to read the results</div>
            <div style="font-family:'Bricolage Grotesque';font-size:1.02rem;
                        font-weight:700;color:#271111;">
                Priority and SLA performance answer different questions.
            </div>
            <div style="font-size:0.82rem;line-height:1.7;
                        color:#806F69;margin-top:8px;">
                Priority scoring determines which tickets deserve greater
                attention based on severity, impact, customer tier and
                reopening history. SLA monitoring checks whether response
                and resolution commitments have been met. A high-priority
                ticket can still be within its SLA, while a lower-priority
                ticket may already have breached its target.
            </div>
        </div>
        """
    )

    st.markdown(" ")
    export_button(
        filtered,
        "priority_engine_filtered_tickets.csv",
        "overview_export",
        "↓  Export filtered tickets",
    )


# ============================================================
# TAB 2: PRIORITY QUEUE
# ============================================================

with queue_tab:
    render_html('<div class="eyebrow">Workload management</div>')
    section_heading(
        "Priority queue",
        "Open tickets ranked by priority band and score.",
    )

    open_queue = filtered.loc[filtered["is_open_ticket"]].copy()

    if open_queue.empty:
        empty_message("There are no open tickets in this filtered view.")
    else:
        open_queue["_priority_order"] = open_queue["priority_band"].map(
            {band: index for index, band in enumerate(PRIORITY_ORDER)}
        )

        sort_columns = ["_priority_order", "priority_score"]
        sort_ascending = [True, False]
        if "resolution_minutes_remaining" in open_queue.columns:
            sort_columns.append("resolution_minutes_remaining")
            sort_ascending.append(True)

        open_queue = open_queue.sort_values(
            by=sort_columns,
            ascending=sort_ascending,
            na_position="last",
        )

        queue_cards = st.columns(4, gap="medium")
        priority_notes = {
            "P1": ("Critical", "metric-red"),
            "P2": ("High priority", "metric-accent"),
            "P3": ("Standard priority", "metric-yellow"),
            "P4": ("Low priority", "metric-green"),
        }

        for index, band in enumerate(PRIORITY_ORDER):
            with queue_cards[index]:
                metric_card(
                    f"{band} open tickets",
                    format_number((open_queue["priority_band"] == band).sum()),
                    priority_notes[band][0],
                    priority_notes[band][1],
                )

        st.markdown(" ")
        queue_columns = [
            "ticket_id",
            "priority_band",
            "priority_score",
            "priority_reason",
            "severity",
            "category",
            "customer_tier",
            "status",
            "agent_id",
            "ticket_age_hours",
            "resolution_sla_status",
            "resolution_minutes_remaining",
        ]
        visible_columns = [
            column for column in queue_columns if column in open_queue.columns
        ]
        queue_display = open_queue[visible_columns].copy().rename(
            columns={
                "ticket_id": "Ticket",
                "priority_band": "Priority",
                "priority_score": "Score",
                "priority_reason": "Priority reasoning",
                "severity": "Severity",
                "category": "Category",
                "customer_tier": "Customer tier",
                "status": "Status",
                "agent_id": "Agent",
                "ticket_age_hours": "Age (hours)",
                "resolution_sla_status": "Resolution SLA",
                "resolution_minutes_remaining": "Minutes to resolution deadline",
            }
        )

        st.dataframe(
            queue_display,
            use_container_width=True,
            hide_index=True,
            height=475,
            column_config={
                "Score": st.column_config.NumberColumn(format="%.0f"),
                "Age (hours)": st.column_config.NumberColumn(format="%.1f"),
                "Minutes to resolution deadline": st.column_config.NumberColumn(
                    format="%.0f"
                ),
            },
        )

        export_button(
            queue_display,
            "priority_engine_priority_queue.csv",
            "queue_download",
            "↓  Download priority queue",
        )

    with st.expander("How priority scores are calculated"):
        st.markdown(
            """
            | Factor | Classification | Points |
            |---|---|---:|
            | Severity | Critical | 100 |
            | | High | 70 |
            | | Medium | 40 |
            | | Low | 10 |
            | Impact | Widespread | 30 |
            | | Multiple customers | 20 |
            | | Individual | 5 |
            | Customer tier | Enterprise | 15 |
            | | Premium | 8 |
            | | Standard | 0 |
            | Reopened | 5 per reopening, capped at 15 | |

            **Priority bands**

            - P1: Critical severity or score of 120 and above.
            - P2: Score of 85 to 119.
            - P3: Score of 45 to 84.
            - P4: Score below 45.

            Critical severity always receives P1 status.
            """
        )


# ============================================================
# TAB 3: SLA MONITOR
# ============================================================

with sla_tab:
    render_html('<div class="eyebrow">Service-level monitoring</div>')
    section_heading(
        "SLA monitor",
        "Compare first-response and resolution outcomes. Compliance is "
        "calculated from tickets with a final met or breached outcome.",
    )

    sla_kpis = st.columns(4, gap="medium")
    with sla_kpis[0]:
        metric_card(
            "First response met",
            format_number(first_met),
            "Within response target",
            "metric-green",
        )
    with sla_kpis[1]:
        metric_card(
            "First response breached",
            format_number(first_breached),
            "Late or overdue",
            "metric-red",
        )
    with sla_kpis[2]:
        metric_card(
            "Resolution met",
            format_number(resolution_met),
            "Within resolution target",
            "metric-green",
        )
    with sla_kpis[3]:
        metric_card(
            "Resolution breached",
            format_number(resolution_breached),
            "Late or overdue",
            "metric-red",
        )

    st.markdown(" ")
    section_heading(
        "SLA outcomes",
        "First-response and resolution results for the selected workload.",
    )

    sla_long = pd.concat(
        [
            filtered[["first_response_sla_status"]]
            .rename(columns={"first_response_sla_status": "sla_status"})
            .assign(sla_measure="First response"),
            filtered[["resolution_sla_status"]]
            .rename(columns={"resolution_sla_status": "sla_status"})
            .assign(sla_measure="Resolution"),
        ],
        ignore_index=True,
    )

    sla_summary = (
        sla_long.groupby(["sla_measure", "sla_status"])
        .size()
        .reset_index(name="tickets")
    )
    sla_summary["share"] = sla_summary["tickets"] / sla_summary.groupby(
        "sla_measure"
    )["tickets"].transform("sum") * 100

    fig = px.bar(
        sla_summary,
        x="tickets",
        y="sla_measure",
        color="sla_status",
        orientation="h",
        barmode="stack",
        color_discrete_map=SLA_COLORS,
        custom_data=["sla_status", "share"],
        category_orders={
            "sla_status": SLA_ORDER,
            "sla_measure": ["Resolution", "First response"],
        },
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Outcome: %{customdata[0]}<br>"
            "Tickets: %{x:,.0f}<br>"
            "Share of this SLA measure: %{customdata[1]:.1f}%"
            "<extra></extra>"
        )
    )
    fig.update_layout(
        xaxis_title="Number of tickets",
        yaxis_title=None,
        legend_title="SLA outcome",
    )
    show_chart(style_chart(fig, 315), "sla_outcomes")

    st.markdown(" ")
    section_heading(
        "SLA exceptions",
        "Tickets that have breached or are approaching either service-level deadline.",
    )

    exception_mask = (
        filtered["first_response_sla_status"].isin(["at_risk", "breached"])
        | filtered["resolution_sla_status"].isin(["at_risk", "breached"])
    )
    exceptions = filtered.loc[exception_mask].copy()

    if exceptions.empty:
        empty_message("There are no at-risk or breached tickets in this filtered view.")
    else:
        exceptions["_priority_order"] = exceptions["priority_band"].map(
            {band: index for index, band in enumerate(PRIORITY_ORDER)}
        )
        exceptions = exceptions.sort_values(
            ["_priority_order", "priority_score"],
            ascending=[True, False],
        )

        exception_columns = [
            "ticket_id",
            "priority_band",
            "priority_score",
            "severity",
            "status",
            "agent_id",
            "first_response_sla_status",
            "first_response_minutes_remaining",
            "resolution_sla_status",
            "resolution_minutes_remaining",
        ]
        exception_display = exceptions[
            [column for column in exception_columns if column in exceptions.columns]
        ].copy().rename(
            columns={
                "ticket_id": "Ticket",
                "priority_band": "Priority",
                "priority_score": "Score",
                "severity": "Severity",
                "status": "Ticket status",
                "agent_id": "Agent",
                "first_response_sla_status": "First response SLA",
                "first_response_minutes_remaining": "Response minutes remaining",
                "resolution_sla_status": "Resolution SLA",
                "resolution_minutes_remaining": "Resolution minutes remaining",
            }
        )
        st.dataframe(
            exception_display,
            use_container_width=True,
            hide_index=True,
            height=320,
        )

        export_button(
            exception_display,
            "priority_engine_sla_exceptions.csv",
            "sla_exception_export",
            "↓  Download SLA exceptions",
        )


# ============================================================
# TAB 4: TEAM AND CATEGORY PERFORMANCE
# ============================================================

with performance_tab:
    render_html('<div class="eyebrow">Operational performance</div>')
    section_heading(
        "Team and category performance",
        "Review workload allocation, service outcomes and customer feedback.",
    )

    agent_tickets = filtered.loc[filtered["agent_id"].notna()].copy()

    if agent_tickets.empty:
        empty_message("There are no assigned tickets in this filtered view.")
    else:
        agent_tickets["urgent_open"] = (
            agent_tickets["is_open_ticket"]
            & agent_tickets["priority_band"].isin(["P1", "P2"])
        )

        agent_summary = (
            agent_tickets.groupby("agent_id")
            .agg(
                assigned_tickets=("ticket_id", "count"),
                open_tickets=("is_open_ticket", "sum"),
                urgent_open_tickets=("urgent_open", "sum"),
                first_response_compliance=(
                    "first_response_sla_status", sla_compliance
                ),
                resolution_compliance=(
                    "resolution_sla_status", sla_compliance
                ),
                average_resolution_hours=("actual_resolution_hours", "mean"),
                average_csat=("csat_score", "mean"),
                reopened_tickets=("is_reopened", "sum"),
            )
            .reset_index()
            .sort_values("assigned_tickets", ascending=False)
        )

        section_heading(
            "Agent workload",
            "Assigned ticket volumes and urgent open workload by agent.",
        )

        agent_chart, agent_table = st.columns([1, 1.45], gap="large")

        with agent_chart:
            top_agents = agent_summary.head(12).copy()
            top_agents["urgent_open_share"] = (
                top_agents["urgent_open_tickets"]
                / top_agents["assigned_tickets"].clip(lower=1)
                * 100
            )
            top_agents = top_agents.sort_values(
                "assigned_tickets", ascending=True
            )
            fig = px.bar(
                top_agents,
                x="assigned_tickets",
                y="agent_id",
                orientation="h",
                text="assigned_tickets",
                color="urgent_open_tickets",
                color_continuous_scale=[SOFT, ACCENT],
                custom_data=["urgent_open_tickets", "urgent_open_share"],
            )
            fig.update_traces(
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "Assigned tickets: %{x:,.0f}<br>"
                    "Urgent open tickets: %{customdata[0]:,.0f}<br>"
                    "Urgent share of assigned workload: %{customdata[1]:.1f}%"
                    "<extra></extra>"
                )
            )
            fig.update_layout(
                xaxis_title="Assigned tickets",
                yaxis_title=None,
                coloraxis_colorbar_title="Urgent open",
            )
            show_chart(style_chart(fig, 385), "agent_workload")

        with agent_table:
            agent_display = agent_summary.rename(
                columns={
                    "agent_id": "Agent",
                    "assigned_tickets": "Assigned",
                    "open_tickets": "Open",
                    "urgent_open_tickets": "Urgent open",
                    "first_response_compliance": "Response SLA %",
                    "resolution_compliance": "Resolution SLA %",
                    "average_resolution_hours": "Avg resolution (h)",
                    "average_csat": "Avg CSAT",
                    "reopened_tickets": "Reopened",
                }
            )
            st.dataframe(
                agent_display,
                use_container_width=True,
                hide_index=True,
                height=385,
                column_config={
                    "Response SLA %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Resolution SLA %": st.column_config.NumberColumn(format="%.1f%%"),
                    "Avg resolution (h)": st.column_config.NumberColumn(format="%.1f"),
                    "Avg CSAT": st.column_config.NumberColumn(format="%.2f"),
                },
            )

    st.markdown(" ")
    section_heading(
        "Category performance",
        "Ticket demand, urgent workload and service outcomes by support category.",
    )

    category_data = filtered.copy()
    category_data["urgent_ticket"] = category_data["priority_band"].isin(
        ["P1", "P2"]
    )

    category_summary = (
        category_data.groupby("category")
        .agg(
            total_tickets=("ticket_id", "count"),
            open_tickets=("is_open_ticket", "sum"),
            urgent_tickets=("urgent_ticket", "sum"),
            first_response_breaches=(
                "first_response_sla_status",
                lambda values: int((values == "breached").sum()),
            ),
            resolution_breaches=(
                "resolution_sla_status",
                lambda values: int((values == "breached").sum()),
            ),
            average_resolution_hours=("actual_resolution_hours", "mean"),
            average_csat=("csat_score", "mean"),
        )
        .reset_index()
        .sort_values("total_tickets", ascending=False)
    )

    category_display = category_summary.rename(
        columns={
            "category": "Category",
            "total_tickets": "Total tickets",
            "open_tickets": "Open tickets",
            "urgent_tickets": "P1/P2 tickets",
            "first_response_breaches": "Response breaches",
            "resolution_breaches": "Resolution breaches",
            "average_resolution_hours": "Avg resolution (h)",
            "average_csat": "Avg CSAT",
        }
    )
    st.dataframe(
        category_display,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAB 5: TICKET EXPLORER
# ============================================================

with explorer_tab:
    render_html('<div class="eyebrow">Record-level investigation</div>')
    section_heading(
        "Ticket explorer",
        "Inspect an individual ticket, its priority calculation, ownership, "
        "timeline and SLA outcomes.",
    )

    explorer_data = filtered.sort_values("created_at", ascending=False)
    ticket_ids = explorer_data["ticket_id"].astype(str).tolist()

    if not ticket_ids:
        empty_message("No tickets are available in this filtered view.")
    else:
        # Keep the saved selection valid when global filters change.
        if st.session_state.get("explorer_ticket") not in ticket_ids:
            st.session_state["explorer_ticket"] = ticket_ids[0]

        selected_ticket_id = st.selectbox(
            "Select a ticket",
            options=ticket_ids,
            key="explorer_ticket",
        )

        selected_ticket = explorer_data.loc[
            explorer_data["ticket_id"].astype(str) == selected_ticket_id
        ].iloc[0]

        st.markdown(" ")
        detail_left, detail_right = st.columns([1.25, 1], gap="large")

        with detail_left:
            ticket_category = safe_text(
                selected_ticket.get("category"), "Uncategorised"
            )
            ticket_description = safe_text(
                selected_ticket.get("description"), "No description provided."
            )

            render_html(
                f"""
                <div class="ticket-panel">
                    <div class="ticket-id">{html.escape(selected_ticket_id)}</div>
                    <div style="font-family:'Bricolage Grotesque';
                                font-size:1.55rem;font-weight:800;
                                color:#271111;letter-spacing:-0.04em;
                                margin-top:8px;">
                        {html.escape(ticket_category.replace('_', ' ').title())}
                    </div>
                    <div style="margin-top:11px;">
                        <span class="tag">{html.escape(safe_text(selected_ticket.get('priority_band')))}</span>
                        <span class="tag">{html.escape(safe_text(selected_ticket.get('severity')))}</span>
                        <span class="tag">{html.escape(safe_text(selected_ticket.get('status')).replace('_', ' '))}</span>
                    </div>
                    <div class="ticket-description">
                        {html.escape(ticket_description)}
                    </div>
                </div>
                """
            )

            st.markdown(" ")
            section_heading(
                "Priority score breakdown",
                "The rule-based calculation behind this ticket's priority.",
            )

            score_fields = [
                ("Severity", "severity_points"),
                ("Impact", "impact_points"),
                ("Customer tier", "customer_tier_points"),
                ("Reopening", "reopened_points"),
            ]
            score_columns = st.columns(4)
            for index, (label, column) in enumerate(score_fields):
                with score_columns[index]:
                    metric_card(
                        label,
                        format_number(selected_ticket.get(column)),
                        "Points",
                        "metric-accent",
                    )

            st.markdown(" ")
            metric_card(
                "Total priority score",
                format_number(selected_ticket.get("priority_score")),
                safe_text(
                    selected_ticket.get("priority_reason"),
                    "Priority reason not recorded",
                ),
                "metric-red",
            )

        with detail_right:
            section_heading(
                "Customer and assignment",
                "Ticket ownership and customer information.",
            )

            details = [
                ("Customer", selected_ticket.get("customer_id")),
                ("Customer tier", selected_ticket.get("customer_tier")),
                ("Assigned agent", selected_ticket.get("agent_id")),
                ("Channel", selected_ticket.get("channel")),
                ("Impact scope", selected_ticket.get("impact_scope")),
                ("Times reopened", selected_ticket.get("reopened_count")),
                ("CSAT score", selected_ticket.get("csat_score")),
            ]

            for label, value in details:
                display_value = safe_text(value).replace("_", " ").title()
                render_html(
                    f"""
                    <div style="display:flex;justify-content:space-between;
                                gap:12px;padding:9px 3px;
                                border-bottom:1px solid {BORDER};">
                        <span style="color:{MUTED};font-size:0.77rem;">
                            {html.escape(label)}
                        </span>
                        <span style="color:{INK};font-size:0.77rem;
                                     font-weight:600;text-align:right;">
                            {html.escape(display_value)}
                        </span>
                    </div>
                    """
                )

            st.markdown(" ")
            section_heading(
                "Ticket timeline",
                "All recorded timestamps are displayed in UTC.",
            )

            timeline_fields = [
                ("Created", "created_at"),
                ("Last updated", "updated_at"),
                ("First response", "first_response_at"),
                ("Resolved", "resolved_at"),
            ]

            for label, column in timeline_fields:
                render_html(
                    f"""
                    <div style="display:flex;justify-content:space-between;
                                gap:12px;padding:9px 3px;
                                border-bottom:1px solid {BORDER};">
                        <span style="color:{MUTED};font-size:0.76rem;">
                            {html.escape(label)}
                        </span>
                        <span style="font-family:'Geist Mono';color:{INK};
                                     font-size:0.64rem;text-align:right;">
                            {html.escape(format_timestamp(selected_ticket.get(column)))}
                        </span>
                    </div>
                    """
                )

        st.markdown(" ")
        section_heading(
            "SLA assessment",
            "Deadlines and outcomes for the selected ticket.",
        )

        sla_detail_columns = st.columns(2, gap="large")
        sla_configs = [
            {
                "label": "First-response status",
                "status_col": "first_response_sla_status",
                "target_col": "first_response_target_hours",
                "due_col": "first_response_due_at",
                "elapsed_col": "first_response_elapsed_hours",
            },
            {
                "label": "Resolution status",
                "status_col": "resolution_sla_status",
                "target_col": "resolution_target_hours",
                "due_col": "resolution_due_at",
                "elapsed_col": "resolution_elapsed_hours",
            },
        ]

        for index, config in enumerate(sla_configs):
            with sla_detail_columns[index]:
                status_value = safe_text(
                    selected_ticket.get(config["status_col"]), "Unknown"
                )
                if status_value == "met":
                    metric_style = "metric-green"
                elif status_value == "breached":
                    metric_style = "metric-red"
                else:
                    metric_style = "metric-yellow"

                metric_card(
                    config["label"],
                    status_value.replace("_", " ").title(),
                    "Target: "
                    + format_decimal(
                        selected_ticket.get(config["target_col"]), 2
                    )
                    + " hours",
                    metric_style,
                )
                st.caption(
                    "Due: "
                    + format_timestamp(selected_ticket.get(config["due_col"]))
                )
                st.caption(
                    "Elapsed: "
                    + format_decimal(
                        selected_ticket.get(config["elapsed_col"]), 2
                    )
                    + " hours"
                )

        st.download_button(
            "↓  Download ticket record as JSON",
            data=json_safe_record(selected_ticket),
            file_name=f"{selected_ticket_id}.json",
            mime="application/json",
            key="single_ticket_download",
        )


# ============================================================
# FOOTER
# ============================================================

render_html(
    f"""
    <div class="footer-note">
        <span style="font-family:'Geist Mono';">
            PRIORITY ENGINE / PROJECT 09
        </span>
        &nbsp;&nbsp;·&nbsp;&nbsp;
        Rule-based prioritisation and SLA monitoring
        <br><br>
        Synthetic support-ticket data. Snapshot: {html.escape(snapshot_label)}.
        SLA calculations use elapsed clock hours, not business-hour calendars.
    </div>
    """
)
