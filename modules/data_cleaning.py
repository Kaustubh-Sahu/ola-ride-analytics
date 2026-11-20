"""Data cleaning for the OlaData table.

Handles: stray whitespace, text placeholders for missing values ("null", "#NAME?"),
wrong dtypes, invalid dates and duplicate rows. It never fills or invents values:
ratings, payment method etc. stay empty for bookings that were not completed,
exactly like the NULLs in the SQL table.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

REQUIRED_COLUMNS = [
    "Date", "Booking_ID", "Booking_Status", "Customer_ID", "Vehicle_Type",
    "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver", "Incomplete_Rides",
    "Incomplete_Rides_Reason", "Booking_Value", "Payment_Method", "Ride_Distance",
    "Driver_Ratings", "Customer_Rating",
]
TEXT_COLUMNS = [
    "Booking_ID", "Booking_Status", "Customer_ID", "Vehicle_Type", "Pickup_Location",
    "Drop_Location", "Canceled_Rides_by_Customer", "Canceled_Rides_by_Driver",
    "Incomplete_Rides", "Incomplete_Rides_Reason", "Payment_Method",
]
NUMERIC_COLUMNS = [
    "Booking_Value", "Ride_Distance", "Driver_Ratings", "Customer_Rating", "V_TAT", "C_TAT",
]
JUNK_COLUMNS = ["Vehicle Images", "Column1"]  # empty / '#NAME?' columns in the Power BI model
NULL_TOKENS = {"", "null", "none", "nan", "na", "n/a", "#name?"}


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (clean_dataframe, report). Raises ValueError if essential columns are missing."""
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            "The dataset is missing required column(s): " + ", ".join(missing)
            + ". Expected the columns of the OlaData table."
        )

    report = {"rows_loaded": len(df)}
    df = df.drop(columns=[c for c in JUNK_COLUMNS if c in df.columns])

    # Text columns: trim and turn placeholder strings into real missing values.
    for col in (c for c in TEXT_COLUMNS if c in df.columns):
        s = df[col].astype("string").str.strip()
        s = s.mask(s.str.lower().isin(NULL_TOKENS))
        df[col] = s.astype(object).where(s.notna(), np.nan)

    # Numeric columns.
    for col in (c for c in NUMERIC_COLUMNS if c in df.columns):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Dates.
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad_dates = int(df["Date"].isna().sum())
    df = df[df["Date"].notna()]
    report["invalid_dates_removed"] = bad_dates

    # Duplicates: exact duplicate rows first, then repeated Booking_IDs.
    before = len(df)
    df = df.drop_duplicates()
    report["duplicate_rows_removed"] = before - len(df)
    before = len(df)
    df = df.drop_duplicates(subset="Booking_ID", keep="first")
    report["duplicate_ids_removed"] = before - len(df)

    df["Booking_Date"] = df["Date"].dt.normalize()
    df = df.sort_values("Date").reset_index(drop=True)
    report["rows_clean"] = len(df)
    report["missing_values"] = {c: int(n) for c, n in df.isna().sum().items() if n}
    return df, report
