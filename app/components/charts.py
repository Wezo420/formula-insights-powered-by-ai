"""
Plotly chart factory functions.
Every chart uses the dark theme and F1 colour conventions.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from config.settings import PLOTLY_TEMPLATE, COMPOUND_COLORS
from utils.helpers import get_driver_color, format_lap_time

_LAYOUT_DEFAULTS = dict(
    template=PLOTLY_TEMPLATE,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Barlow, sans-serif", color="#f0f0f5"),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(
        bgcolor="rgba(17,17,24,0.8)",
        bordercolor="rgba(255,255,255,0.07)",
        borderwidth=1,
    ),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.1)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.1)"),
)


def _apply_defaults(fig: go.Figure, title: str = "") -> go.Figure:
    fig.update_layout(title=dict(text=title, font=dict(size=16, family="Barlow Condensed")),
                      **_LAYOUT_DEFAULTS)
    return fig


# ── Lap time chart ────────────────────────────────────────────────────────────
def lap_time_chart(
    laps: pd.DataFrame,
    drivers: list[str],
    col: str = "LapTimeSmoothed",
    title: str = "Lap Times",
) -> go.Figure:
    fig = go.Figure()
    all_drivers = laps["Driver"].unique().tolist() if not laps.empty else []

    if col not in laps.columns and "LapTimeSeconds" in laps.columns:
        col = "LapTimeSeconds"

    for i, driver in enumerate(drivers):
        df = laps[laps["Driver"] == driver].sort_values("LapNumber")
        if df.empty or col not in df.columns:
            continue
        color = get_driver_color(driver, all_drivers)
        fig.add_trace(
            go.Scatter(
                x=df["LapNumber"],
                y=df[col],
                name=driver,
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=4, color=color),
                hovertemplate=(
                    f"<b>{driver}</b><br>"
                    "Lap %{x}<br>"
                    "Time: %{customdata}<extra></extra>"
                ),
                customdata=[format_lap_time(t) for t in df[col]],
            )
        )

    fig.update_layout(
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (s)",
        hovermode="x unified",
    )
    return _apply_defaults(fig, title)


# ── Delta / gap chart ─────────────────────────────────────────────────────────
def delta_chart(
    gap_df: pd.DataFrame,
    driver_a: str,
    driver_b: str,
    title: str = "Pace Gap",
) -> go.Figure:
    fig = go.Figure()
    if gap_df.empty or "PaceGap" not in gap_df.columns:
        return _apply_defaults(fig, title)

    colors = [
        "#e10600" if v >= 0 else "#27F4D2" for v in gap_df["PaceGap"]
    ]
    fig.add_trace(
        go.Bar(
            x=gap_df["LapNumber"],
            y=gap_df["PaceGap"],
            marker_color=colors,
            name=f"{driver_a} vs {driver_b}",
            hovertemplate="Lap %{x}<br>Gap: %{y:.3f}s<extra></extra>",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.3)")
    fig.update_layout(
        xaxis_title="Lap Number",
        yaxis_title=f"Gap: {driver_a} − {driver_b} (s)",
    )
    return _apply_defaults(fig, title)


# ── Stint / strategy chart ────────────────────────────────────────────────────
def strategy_chart(stints: pd.DataFrame, title: str = "Tyre Strategy") -> go.Figure:
    fig = go.Figure()
    if stints.empty:
        return _apply_defaults(fig, title)

    drivers = stints["Driver"].unique().tolist()
    for y_pos, driver in enumerate(drivers):
        drv_stints = stints[stints["Driver"] == driver]
        for _, row in drv_stints.iterrows():
            compound = str(row.get("Compound", "UNKNOWN")).upper()
            color = COMPOUND_COLORS.get(compound, "#999999")
            fig.add_trace(
                go.Bar(
                    x=[row["StintLength"]],
                    y=[driver],
                    base=[row["StartLap"] - 1],
                    orientation="h",
                    marker_color=color,
                    marker_line_color="rgba(0,0,0,0.4)",
                    marker_line_width=1,
                    name=compound,
                    showlegend=True,
                    legendgroup=compound,
                    hovertemplate=(
                        f"<b>{driver}</b><br>"
                        f"Compound: {compound}<br>"
                        f"Laps: {int(row['StartLap'])}–{int(row['EndLap'])}<br>"
                        f"Length: {int(row['StintLength'])} laps<extra></extra>"
                    ),
                )
            )

    # Deduplicate legend entries
    seen = set()
    for trace in fig.data:
        if trace.name in seen:
            trace.showlegend = False
        seen.add(trace.name)

    fig.update_layout(
        barmode="overlay",
        xaxis_title="Lap Number",
        yaxis_title="Driver",
        bargap=0.3,
    )
    return _apply_defaults(fig, title)


# ── Telemetry overlay chart ────────────────────────────────────────────────────
def telemetry_chart(
    tel_data: dict[str, pd.DataFrame],
    channel: str = "Speed",
    title: str = "",
    circuit_info = None
) -> go.Figure:
    """
    tel_data: {"DRIVER_ABB": telemetry_df, ...}
    """
    fig = go.Figure()
    drivers = list(tel_data.keys())

    for i, (driver, df) in enumerate(tel_data.items()):
        if df.empty or channel not in df.columns or "Distance" not in df.columns:
            continue
        color = get_driver_color(driver, drivers)
        fig.add_trace(
            go.Scatter(
                x=df["Distance"],
                y=df[channel],
                name=driver,
                mode="lines",
                line=dict(color=color, width=1.8),
                hovertemplate=f"<b>{driver}</b><br>Dist: %{{x:.0f}}m<br>{channel}: %{{y:.1f}}<extra></extra>",
            )
        )
    if circuit_info is not None and hasattr(circuit_info, 'corners'):
        for _, corner in circuit_info.corners.iterrows():
            fig.add_vline(
                x=corner['Distance'], 
                line_width=1, 
                line_dash="dash", 
                line_color="rgba(255,255,255,0.15)", 
                annotation_text=str(corner['Number']), 
                annotation_position="top left",
                annotation_font=dict(color="rgba(255,255,255,0.5)", size=10)
            )

    units = {"Speed": "km/h", "Throttle": "%", "Brake": "%", "RPM": "rpm", "nGear": ""}
    # units = {"Speed": "km/h", "Throttle": "%", "Brake": "%", "RPM": "rpm", "nGear": ""}
    fig.update_layout(
        xaxis_title="Distance (m)",
        yaxis_title=f"{channel} ({units.get(channel, '')})",
        hovermode="x unified",
    )
    return _apply_defaults(fig, title or f"{channel} Trace")


# ── Multi-channel telemetry (subplots) ────────────────────────────────────────
def telemetry_dashboard(
    tel_data: dict[str, pd.DataFrame],
    channels: list[str] | None = None,
    circuit_info = None
) -> go.Figure:
    if channels is None:
        channels = ["Speed", "Throttle", "Brake", "nGear"]

    channels = [c for c in channels if any(c in df.columns for df in tel_data.values())]
    if not channels:
        return go.Figure()

    fig = make_subplots(
        rows=len(channels),
        cols=1,
        shared_xaxes=True,
        subplot_titles=channels,
        vertical_spacing=0.04,
    )
    drivers = list(tel_data.keys())

    for row_idx, channel in enumerate(channels, start=1):
        for driver, df in tel_data.items():
            if df.empty or channel not in df.columns:
                continue
            color = get_driver_color(driver, drivers)
            fig.add_trace(
                go.Scatter(
                    x=df["Distance"],
                    y=df[channel],
                    name=driver,
                    mode="lines",
                    line=dict(color=color, width=1.6),
                    legendgroup=driver,
                    showlegend=(row_idx == 1),
                    hovertemplate=f"<b>{driver}</b> {channel}: %{{y:.1f}}<extra></extra>",
                ),
                row=row_idx,
                col=1,
            )
    if circuit_info is not None and hasattr(circuit_info, 'corners'):
        for _, corner in circuit_info.corners.iterrows():
            fig.add_vline(
                x=corner['Distance'],
                line_width=1,
                line_dash="dash",
                line_color="rgba(255,255,255,0.15)",
                annotation_text=str(corner['Number']),
                annotation_position="top left",
                annotation_font=dict(color="rgba(255,255,255,0.5)", size=10)
            )

    units = {"Speed": "km/h", "Throttle": "%", "Brake": "%", "RPM": "rpm", "nGear": ""}

    fig.update_layout(
        height=180 * len(channels),
        hovermode="x unified",
        **_LAYOUT_DEFAULTS,
    )
    for i in range(1, len(channels) + 1):
        fig.update_xaxes(
            gridcolor="rgba(255,255,255,0.04)",
            row=i, col=1,
        )
        fig.update_yaxes(
            gridcolor="rgba(255,255,255,0.04)",
            row=i, col=1,
        )
    if len(channels) > 0:
        fig.update_xaxes(title_text="Distance (m)", row=len(channels), col=1)
    return fig


# ── Degradation curve ─────────────────────────────────────────────────────────
def degradation_chart(
    deg_data: dict[str, pd.DataFrame],
    title: str = "Tyre Degradation",
) -> go.Figure:
    """
    deg_data: {driver: DataFrame with LapInStint, LapTime, Type columns}
    """
    fig = go.Figure()
    drivers = list(deg_data.keys())

    for driver, df in deg_data.items():
        if df.empty:
            continue
        color = get_driver_color(driver, drivers)
        actual = df[df["Type"] == "Actual"]
        projected = df[df["Type"] == "Projected"]

        fig.add_trace(
            go.Scatter(
                x=actual["LapInStint"],
                y=actual["LapTime"],
                name=f"{driver} (actual)",
                mode="lines+markers",
                line=dict(color=color, width=2),
                marker=dict(size=5, color=color),
            )
        )
        if not projected.empty:
            fig.add_trace(
                go.Scatter(
                    x=projected["LapInStint"],
                    y=projected["LapTime"],
                    name=f"{driver} (projected)",
                    mode="lines",
                    line=dict(color=color, width=1.5, dash="dot"),
                )
            )

    fig.update_layout(
        xaxis_title="Lap in Stint",
        yaxis_title="Lap Time (s)",
        hovermode="x unified",
    )
    return _apply_defaults(fig, title)


# ── Pace violin / box ─────────────────────────────────────────────────────────
def pace_distribution_chart(
    laps: pd.DataFrame,
    drivers: list[str],
    col: str = "LapTimeSeconds",
    title: str = "Pace Distribution",
) -> go.Figure:
    fig = go.Figure()
    if laps.empty or col not in laps.columns:
        return _apply_defaults(fig, title)

    all_drivers = laps["Driver"].unique().tolist()
    for driver in drivers:
        df = laps[laps["Driver"] == driver]
        if df.empty:
            continue
        color = get_driver_color(driver, all_drivers)
        fig.add_trace(
            go.Violin(
                y=df[col].dropna(),
                name=driver,
                box_visible=True,
                meanline_visible=True,
                fillcolor=color,
                line_color=color,
                opacity=0.7,
            )
        )
    fig.update_layout(yaxis_title="Lap Time (s)", violinmode="group")
    return _apply_defaults(fig, title)


# ── Cumulative gap chart ──────────────────────────────────────────────────────
def cumulative_gap_chart(
    laps: pd.DataFrame,
    drivers: list[str],
    leader: str,
    title: str = "Gap to Leader",
) -> go.Figure:
    from src.processing.feature_engineering import compute_delta_to_leader

    fig = go.Figure()
    if laps.empty or leader not in laps["Driver"].unique():
        return _apply_defaults(fig, title)

    enriched = compute_delta_to_leader(laps, leader)
    all_drivers = laps["Driver"].unique().tolist()

    for driver in drivers:
        df = enriched[enriched["Driver"] == driver].sort_values("LapNumber")
        if df.empty:
            continue
        color = get_driver_color(driver, all_drivers)
        fig.add_trace(
            go.Scatter(
                x=df["LapNumber"],
                y=df["DeltaToLeader"],
                name=driver,
                mode="lines",
                line=dict(color=color, width=2),
                hovertemplate=f"<b>{driver}</b><br>Lap %{{x}}<br>Gap: %{{y:+.3f}}s<extra></extra>",
            )
        )

    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    fig.update_layout(
        xaxis_title="Lap Number",
        yaxis_title=f"Gap to {leader} (s)",
        hovermode="x unified",
    )
    return _apply_defaults(fig, title)


# ── Speed delta chart ─────────────────────────────────────────────────────────
def speed_delta_chart(
    delta_df: pd.DataFrame,
    driver_a: str,
    driver_b: str,
) -> go.Figure:
    fig = go.Figure()
    if delta_df.empty or "SpeedDelta" not in delta_df.columns:
        return _apply_defaults(fig, f"Speed Delta: {driver_a} vs {driver_b}")

    pos = delta_df["SpeedDelta"].clip(lower=0)
    neg = delta_df["SpeedDelta"].clip(upper=0)

    fig.add_trace(go.Scatter(
        x=delta_df["Distance"], y=pos, fill="tozeroy",
        fillcolor="rgba(225,6,0,0.35)", line=dict(color="#e10600", width=1),
        name=f"{driver_a} faster",
    ))
    fig.add_trace(go.Scatter(
        x=delta_df["Distance"], y=neg, fill="tozeroy",
        fillcolor="rgba(39,244,210,0.25)", line=dict(color="#27F4D2", width=1),
        name=f"{driver_b} faster",
    ))
    fig.add_hline(y=0, line_color="rgba(255,255,255,0.2)")
    fig.update_layout(
        xaxis_title="Distance (m)",
        yaxis_title="Speed Delta (km/h)",
        hovermode="x unified",
    )
    return _apply_defaults(fig, f"Speed Delta: {driver_a} vs {driver_b}")
