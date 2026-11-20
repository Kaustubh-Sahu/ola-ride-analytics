"""Plotly figure builders with one consistent dark theme."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

LIME, TEAL, AMBER, BLUE, VIOLET, RED, SLATE = (
    "#C6F135", "#2DD4BF", "#F5B83D", "#60A5FA", "#A78BFA", "#F87171", "#94A3B8")
PALETTE = [LIME, TEAL, AMBER, BLUE, VIOLET, RED, SLATE]
STATUS_COLORS = {
    "Success": LIME, "Canceled by Customer": AMBER, "Canceled by Driver": RED, "Driver Not Found": SLATE,
}
GRID = "rgba(148,163,184,0.12)"
FONT = "Inter, 'Segoe UI', system-ui, sans-serif"


def _style(fig: go.Figure, title: str | None = None, height: int = 360, legend: bool = True) -> go.Figure:
    fig.update_layout(
        title=dict(text=title or "", x=0, xanchor="left", font=dict(size=15, color="#F1F5F9")),
        height=height, template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family=FONT, color="#CBD5E1", size=12),
        margin=dict(l=8, r=8, t=52, b=8), colorway=PALETTE, showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1, title_text=""),
        hoverlabel=dict(bgcolor="#0F172A", bordercolor="#334155", font_size=13),
    )
    fig.update_xaxes(gridcolor=GRID, zeroline=False, title_text=None)
    fig.update_yaxes(gridcolor=GRID, zeroline=False, title_text=None)
    return fig


def donut(df: pd.DataFrame, names: str, values: str, title: str, colors: dict | None = None,
          center_text: str | None = None) -> go.Figure:
    colorway = [colors.get(n, SLATE) for n in df[names]] if colors else PALETTE[: len(df)]
    fig = go.Figure(go.Pie(
        labels=df[names], values=df[values], hole=0.62, sort=False, marker=dict(colors=colorway,
        line=dict(color="#0B0F14", width=2)), textinfo="percent", textfont=dict(size=12),
        hovertemplate="<b>%{label}</b><br>%{value:,} (%{percent})<extra></extra>"))
    if center_text:
        fig.add_annotation(text=center_text, showarrow=False, font=dict(size=18, color="#F1F5F9"))
    fig = _style(fig, title)
    fig.update_layout(legend=dict(orientation="v", y=0.5, x=1.0, xanchor="left", yanchor="middle"))
    return fig


def bar(df: pd.DataFrame, x: str, y: str, title: str, *, horizontal: bool = False, prefix: str = "",
        fmt: str = ",.0f", label: str | None = None, color: str | None = None,
        color_map: dict | None = None, value_range: tuple | None = None, height: int = 360) -> go.Figure:
    label = label or y.replace("_", " ")
    if horizontal:
        fig = px.bar(df, x=y, y=x, color=color, color_discrete_map=color_map, orientation="h")
        fig.update_yaxes(categoryorder="total ascending")
        vtemplate = f"{prefix}%{{x:{fmt}}}"
        if value_range:
            fig.update_xaxes(range=list(value_range))
    else:
        fig = px.bar(df, x=x, y=y, color=color, color_discrete_map=color_map)
        vtemplate = f"{prefix}%{{y:{fmt}}}"
        if value_range:
            fig.update_yaxes(range=list(value_range))
    if color is None:
        fig.update_traces(marker_color=LIME)
    fig.update_traces(
        texttemplate=vtemplate, textposition="outside", cliponaxis=False, marker_cornerradius=4,
        hovertemplate=f"<b>%{{{'y' if horizontal else 'x'}}}</b><br>{label}: {vtemplate}<extra></extra>")
    return _style(fig, title, height, legend=color is not None)


def stacked_bar(df: pd.DataFrame, x: str, y: str, color: str, title: str, *, percent: bool = False,
                color_map: dict | None = None, height: int = 360) -> go.Figure:
    fig = px.bar(df, x=x, y=y, color=color, color_discrete_map=color_map, barmode="relative")
    if percent:
        fig.update_layout(barnorm="percent")
        fig.update_yaxes(ticksuffix="%")
    fig.update_traces(marker_cornerradius=2,
                      hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:,}<extra></extra>")
    return _style(fig, title, height)


def bookings_trend(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Booking_Date"], y=df["Bookings"], name="All bookings", mode="lines",
                             line=dict(color=LIME, width=2.5), fill="tozeroy", fillcolor="rgba(198,241,53,0.08)"))
    fig.add_trace(go.Scatter(x=df["Booking_Date"], y=df["Successful"], name="Successful", mode="lines",
                             line=dict(color=TEAL, width=2)))
    fig.update_traces(hovertemplate="%{x|%d %b %Y}<br>%{fullData.name}: %{y:,}<extra></extra>")
    fig.update_yaxes(rangemode="tozero")
    return _style(fig, title)


def revenue_trend(df: pd.DataFrame, title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Booking_Date"], y=df["Revenue"], name="Daily revenue",
                         marker_color="rgba(198,241,53,0.35)",
                         hovertemplate="%{x|%d %b %Y}<br>Daily revenue: ₹%{y:,.0f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=df["Booking_Date"], y=df["Rolling_7d"], name="7-day average", mode="lines",
                             line=dict(color=LIME, width=3),
                             hovertemplate="%{x|%d %b %Y}<br>7-day avg: ₹%{y:,.0f}<extra></extra>"))
    return _style(fig, title)


def grouped_bar(df: pd.DataFrame, x: str, series: dict[str, str], title: str, *, fmt: str = ".2f",
                value_range: tuple | None = None, height: int = 360) -> go.Figure:
    fig = go.Figure()
    for (col, name), color in zip(series.items(), [LIME, TEAL, AMBER]):
        fig.add_trace(go.Bar(x=df[x], y=df[col], name=name, marker_color=color, marker_cornerradius=4,
                             texttemplate=f"%{{y:{fmt}}}", textposition="outside", cliponaxis=False,
                             hovertemplate=f"<b>%{{x}}</b><br>{name}: %{{y:{fmt}}}<extra></extra>"))
    fig.update_layout(barmode="group")
    if value_range:
        fig.update_yaxes(range=list(value_range))
    return _style(fig, title, height)


def histogram(df: pd.DataFrame, column: str, title: str, *, nbins: int = 30, prefix: str = "") -> go.Figure:
    fig = px.histogram(df, x=column, nbins=nbins)
    fig.update_traces(marker_color=LIME, marker_line=dict(color="#0B0F14", width=1),
                      hovertemplate=f"{prefix}%{{x}}<br>Rides: %{{y:,}}<extra></extra>")
    fig.update_layout(bargap=0.04)
    return _style(fig, title, legend=False)


def overlay_histogram(frames: dict[str, pd.Series], title: str, nbins: int = 20) -> go.Figure:
    fig = go.Figure()
    for (name, series), color in zip(frames.items(), [LIME, TEAL]):
        fig.add_trace(go.Histogram(x=series.dropna(), name=name, nbinsx=nbins, marker_color=color, opacity=0.65,
                                   hovertemplate=f"{name}<br>Rating %{{x}}<br>Rides: %{{y:,}}<extra></extra>"))
    fig.update_layout(barmode="overlay", bargap=0.06)
    return _style(fig, title)


def box(df: pd.DataFrame, x: str, y: str, title: str) -> go.Figure:
    fig = px.box(df, x=x, y=y, color=x)
    fig.update_traces(hovertemplate="%{x}<br>%{y:₹,.0f}<extra></extra>")
    return _style(fig, title, legend=False)
