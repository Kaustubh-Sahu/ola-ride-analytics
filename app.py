"""Ola Ride Booking Analytics - Streamlit dashboard.  Run with:  streamlit run app.py"""
from __future__ import annotations

import os

import streamlit as st

st.set_page_config(page_title="Ola Ride Analytics", page_icon="🚖", layout="wide",
                   initial_sidebar_state="expanded")

from modules import data_loader, views  # noqa: E402  (after set_page_config)
from modules.filters import apply_filters  # noqa: E402
from modules.ui import fmt_int, load_css  # noqa: E402

PAGES = {
    "Overall": views.render_overall,
    "Vehicle Type": views.render_vehicle,
    "Revenue": views.render_revenue,
    "Cancellations": views.render_cancellations,
    "Ratings": views.render_ratings,
}
SOURCES = ["Bundled Ola dataset", "Upload CSV / Excel", "MySQL database"]


def setting(name: str, fallback: str = "") -> str:
    """Read from .streamlit/secrets.toml, then environment variables."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        pass
    return os.getenv(name, fallback)


def choose_and_load():
    """Sidebar data-source picker. Returns (df, report) or stops the app with a clear message."""
    source = st.sidebar.selectbox("Data source", SOURCES, key="source")
    try:
        if source == SOURCES[0]:
            with st.spinner("Loading dataset..."):
                return data_loader.load_default()

        if source == SOURCES[1]:
            file = st.sidebar.file_uploader("CSV or Excel (.xlsx)", type=["csv", "xlsx"])
            if file is None:
                st.info("Upload your OlaData export (CSV or Excel) in the sidebar, "
                        "or switch to the bundled dataset.")
                st.stop()
            with st.spinner("Reading and cleaning file..."):
                return data_loader.load_upload(file.name, file.getvalue())

        with st.sidebar.form("mysql_form"):
            host = st.text_input("Host", setting("MYSQL_HOST", "localhost"))
            port = st.number_input("Port", 1, 65535, int(setting("MYSQL_PORT", "3306")))
            user = st.text_input("User", setting("MYSQL_USER", "root"))
            password = st.text_input("Password", setting("MYSQL_PASSWORD"), type="password")
            database = st.text_input("Database", setting("MYSQL_DATABASE", "OLA"))
            table = st.text_input("Table", setting("MYSQL_TABLE", "OlaData"))
            if st.form_submit_button("Connect", width="stretch"):
                st.session_state["mysql_cfg"] = (host, int(port), user, password, database, table)
        cfg = st.session_state.get("mysql_cfg")
        if cfg is None:
            st.info("Enter your MySQL details in the sidebar and press Connect.")
            st.stop()
        with st.spinner("Querying MySQL..."):
            return data_loader.load_mysql(*cfg)
    except Exception as exc:  # show a friendly message instead of a stack trace
        st.error(f"Could not load the data: {exc}")
        st.stop()


def main() -> None:
    load_css()
    st.sidebar.markdown('<div class="brand"><span class="brand-dot"></span>Ola Analytics</div>'
                        '<div class="brand-sub">Ride booking insights</div>', unsafe_allow_html=True)
    page = st.sidebar.radio("Navigation", list(PAGES), label_visibility="collapsed", key="page")

    st.sidebar.markdown('<div class="side-label">Data</div>', unsafe_allow_html=True)
    data, report = choose_and_load()
    with st.sidebar.expander("Data quality report"):
        st.write(f"Rows loaded: **{report['rows_loaded']:,}**")
        st.write(f"Rows after cleaning: **{report['rows_clean']:,}**")
        st.write(f"Duplicates removed: **{report['duplicate_rows_removed'] + report['duplicate_ids_removed']:,}**")
        st.write(f"Invalid dates removed: **{report['invalid_dates_removed']:,}**")
        st.caption("Empty ratings, payment method etc. are kept empty for bookings that were not completed, "
                   "as in the original SQL table.")

    filtered, summary = apply_filters(data)
    if filtered.empty:
        st.warning("No bookings match the selected filters. Adjust or clear the filters in the sidebar.")
        st.stop()

    st.sidebar.download_button(
        f"Download filtered data ({fmt_int(len(filtered))} rows)",
        data=lambda: filtered.drop(columns=["Booking_Date"]).to_csv(index=False).encode("utf-8"),
        file_name="ola_filtered_data.csv", mime="text/csv", width="stretch")

    PAGES[page](filtered, summary)
    views.render_data_section(filtered)


main()
