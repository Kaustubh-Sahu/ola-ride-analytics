"""Data sources: bundled CSV, uploaded CSV/Excel, or MySQL. All loaders return (clean_df, report)."""
from __future__ import annotations

import io
import re
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

from modules.data_cleaning import clean_data

DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "OlaData.csv"


@st.cache_data(show_spinner=False)
def load_default(path: str = str(DEFAULT_DATA_PATH)) -> tuple[pd.DataFrame, dict]:
    if not Path(path).exists():
        raise FileNotFoundError(f"Bundled dataset not found at {path}.")
    return clean_data(pd.read_csv(path, low_memory=False))


@st.cache_data(show_spinner=False)
def load_upload(file_name: str, content: bytes) -> tuple[pd.DataFrame, dict]:
    name = file_name.lower()
    if name.endswith(".csv"):
        raw = pd.read_csv(io.BytesIO(content), low_memory=False)
    elif name.endswith((".xlsx", ".xlsm")):
        raw = pd.read_excel(io.BytesIO(content), engine="openpyxl")
    else:
        raise ValueError("Unsupported file type. Upload a .csv or .xlsx file.")
    if raw.empty:
        raise ValueError("The uploaded file contains no rows.")
    return clean_data(raw)


@st.cache_data(show_spinner=False, ttl=600)
def load_mysql(host: str, port: int, user: str, password: str, database: str,
               table: str) -> tuple[pd.DataFrame, dict]:
    if not re.fullmatch(r"[A-Za-z0-9_]+", table):
        raise ValueError("Table name may only contain letters, numbers and underscores.")
    url = URL.create("mysql+pymysql", username=user, password=password,
                     host=host, port=int(port), database=database)
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as conn:
            raw = pd.read_sql(f"SELECT * FROM `{table}`", conn)
    finally:
        engine.dispose()
    return clean_data(raw)
