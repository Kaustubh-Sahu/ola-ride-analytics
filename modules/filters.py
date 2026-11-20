"""Sidebar filters. Widget keys include a dataset fingerprint so stale selections never survive a data change."""
from __future__ import annotations

import hashlib

import pandas as pd
import streamlit as st

NO_PAYMENT = "No payment (not completed)"


def _fingerprint(df: pd.DataFrame) -> str:
    basis = (len(df), str(df["Booking_Date"].min()), str(df["Booking_Date"].max()),
             tuple(sorted(df["Vehicle_Type"].dropna().unique())),
             tuple(sorted(df["Booking_Status"].dropna().unique())))
    return hashlib.md5(repr(basis).encode()).hexdigest()[:8]


def _reset(defaults: dict) -> None:
    for key, value in defaults.items():
        st.session_state[key] = value


def apply_filters(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Render the filters in the sidebar; return (filtered_df, human readable summary)."""
    fp = _fingerprint(df)
    k_date, k_veh, k_stat, k_pay = (f"{n}_{fp}" for n in ("f_date", "f_vehicle", "f_status", "f_payment"))
    dmin, dmax = df["Booking_Date"].min().date(), df["Booking_Date"].max().date()
    defaults = {k_date: (dmin, dmax), k_veh: [], k_stat: [], k_pay: []}

    st.sidebar.markdown('<div class="side-label">Filters</div>', unsafe_allow_html=True)
    # Once the key lives in session state (e.g. after "Clear filters") passing a default too triggers a warning.
    date_kwargs = {} if k_date in st.session_state else {"value": (dmin, dmax)}
    dates = st.sidebar.date_input("Date range", min_value=dmin, max_value=dmax, key=k_date, **date_kwargs)
    vehicles = st.sidebar.multiselect("Vehicle type", sorted(df["Vehicle_Type"].dropna().unique()),
                                      placeholder="All vehicle types", key=k_veh)
    statuses = st.sidebar.multiselect("Booking status", sorted(df["Booking_Status"].dropna().unique()),
                                      placeholder="All statuses", key=k_stat)
    pay_options = sorted(df["Payment_Method"].dropna().unique()) + [NO_PAYMENT]
    payments = st.sidebar.multiselect("Payment method", pay_options, placeholder="All payment methods", key=k_pay)
    st.sidebar.button("Clear filters", on_click=_reset, args=(defaults,), width="stretch")

    if not (isinstance(dates, (tuple, list)) and len(dates) == 2):
        st.info("Select an end date to apply the date range.")
        st.stop()

    mask = (df["Booking_Date"] >= pd.Timestamp(dates[0])) & (df["Booking_Date"] <= pd.Timestamp(dates[1]))
    if vehicles:
        mask &= df["Vehicle_Type"].isin(vehicles)
    if statuses:
        mask &= df["Booking_Status"].isin(statuses)
    if payments:
        pay_mask = df["Payment_Method"].isin([p for p in payments if p != NO_PAYMENT])
        if NO_PAYMENT in payments:
            pay_mask |= df["Payment_Method"].isna()
        mask &= pay_mask

    active = [n for n, v in (("vehicle", vehicles), ("status", statuses), ("payment", payments)) if v]
    summary = f"{dates[0]:%d %b} – {dates[1]:%d %b %Y}" + (f" · filtered by {', '.join(active)}" if active else "")
    return df[mask], summary
