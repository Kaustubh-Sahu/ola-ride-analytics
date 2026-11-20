"""Small UI helpers: CSS loading, KPI cards, formatting."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"


def load_css() -> None:
    try:
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)
    except OSError:
        pass  # styling is optional; the app still works without it


def fmt_int(value) -> str:
    return "–" if pd.isna(value) else f"{int(round(value)):,}"


def fmt_inr(value) -> str:
    """Indian-style compact currency: ₹3.51 Cr / ₹4.2 L / ₹512."""
    if pd.isna(value):
        return "–"
    a = abs(value)
    if a >= 1e7:
        return f"₹{value / 1e7:,.2f} Cr"
    if a >= 1e5:
        return f"₹{value / 1e5:,.2f} L"
    return f"₹{value:,.0f}"


def fmt_num(value, digits: int = 2) -> str:
    return "–" if value is None or pd.isna(value) else f"{value:,.{digits}f}"


def kpi_row(items: list[tuple[str, str, str]]) -> None:
    """items = [(label, value, sub-text), ...] rendered as equal-width cards."""
    for col, (label, value, sub) in zip(st.columns(len(items)), items):
        col.markdown(
            f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value">{value}</div><div class="kpi-sub">{sub or "&nbsp;"}</div></div>',
            unsafe_allow_html=True)


def page_header(title: str, subtitle: str) -> None:
    st.markdown(f'<div class="page-title">{title}</div><div class="page-sub">{subtitle}</div>',
                unsafe_allow_html=True)


def show(fig) -> None:
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
