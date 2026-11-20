"""All metrics. Each function mirrors a query in OlaDataSQLqueries.sql or a measure in the Power BI report.

Conventions (kept identical to the SQL / DAX logic):
* Revenue = Booking_Value of rows with Booking_Status = 'Success' only.
* Cancellation % (Power BI) = (Canceled by Customer + Canceled by Driver) / all bookings * 100.
  'Driver Not Found' is reported separately and is not part of that percentage.
* AVG / MAX / MIN ignore missing values, as in SQL.
"""
from __future__ import annotations

import pandas as pd

SUCCESS = "Success"
CUSTOMER_CANCEL = "Canceled by Customer"
DRIVER_CANCEL = "Canceled by Driver"
NOT_FOUND = "Driver Not Found"
PERSONAL_CAR_REASON = "Personal & Car related issue"
STATUS_ORDER = [SUCCESS, CUSTOMER_CANCEL, DRIVER_CANCEL, NOT_FOUND]


def successful(df: pd.DataFrame) -> pd.DataFrame:
    """SQL view Successfull_Booking."""
    return df[df["Booking_Status"] == SUCCESS]


def _nz(value) -> float:
    return 0.0 if pd.isna(value) else float(value)


# ---------------------------------------------------------------- Overall
def overall_kpis(df: pd.DataFrame) -> dict:
    succ = successful(df)
    total = len(df)
    return {
        "total_bookings": total,
        "successful_bookings": len(succ),
        "success_rate": len(succ) / total * 100 if total else 0.0,
        "successful_value": _nz(succ["Booking_Value"].sum()),   # SQL: total_Booking_Value
        "all_quoted_value": _nz(df["Booking_Value"].sum()),     # Power BI card (all statuses)
        "total_distance": _nz(df["Ride_Distance"].sum()),
        "avg_distance_completed": _nz(succ["Ride_Distance"].mean()),
        "total_customers": int(df["Customer_ID"].nunique()),
    }


def status_distribution(df: pd.DataFrame) -> pd.DataFrame:
    counts = df["Booking_Status"].value_counts()
    order = [s for s in STATUS_ORDER if s in counts.index] + [s for s in counts.index if s not in STATUS_ORDER]
    return counts.reindex(order).rename_axis("Booking_Status").reset_index(name="Bookings")


def bookings_over_time(df: pd.DataFrame) -> pd.DataFrame:
    d = df.assign(_ok=df["Booking_Status"].eq(SUCCESS))
    out = d.groupby("Booking_Date").agg(Bookings=("Booking_ID", "size"), Successful=("_ok", "sum"))
    return out.reset_index()


def distance_by_vehicle(df: pd.DataFrame) -> pd.DataFrame:
    return (df.groupby("Vehicle_Type")["Ride_Distance"].sum().sort_values(ascending=False)
            .reset_index(name="Total_Distance"))


def payment_distribution(df: pd.DataFrame) -> pd.DataFrame:
    return (df["Payment_Method"].dropna().value_counts()
            .rename_axis("Payment_Method").reset_index(name="Rides"))


# ---------------------------------------------------------------- Vehicle type
def vehicle_summary(df: pd.DataFrame) -> pd.DataFrame:
    d = df.assign(_ok=df["Booking_Status"].eq(SUCCESS))
    out = d.groupby("Vehicle_Type").agg(
        Bookings=("Booking_ID", "size"),
        Successful=("_ok", "sum"),
        Total_Distance=("Ride_Distance", "sum"),
        Avg_Distance_All=("Ride_Distance", "mean"),            # SQL avg_ride_distance (all bookings)
        Avg_Customer_Rating=("Customer_Rating", "mean"),       # SQL avg_customer_rating
        Avg_Driver_Rating=("Driver_Ratings", "mean"),
    )
    succ = successful(df).groupby("Vehicle_Type")
    out["Avg_Distance_Completed"] = succ["Ride_Distance"].mean()
    out["Booking_Value"] = succ["Booking_Value"].sum()
    out["Booking_Value"] = out["Booking_Value"].fillna(0)
    out["Success_Rate"] = out["Successful"] / out["Bookings"] * 100
    return out.sort_values("Bookings", ascending=False).reset_index()


def status_by_vehicle(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby(["Vehicle_Type", "Booking_Status"]).size().reset_index(name="Bookings")


# ---------------------------------------------------------------- Revenue
def revenue_kpis(df: pd.DataFrame) -> dict:
    succ = successful(df)
    return {
        "total_value": _nz(succ["Booking_Value"].sum()),
        "successful_rides": len(succ),
        "avg_value": _nz(succ["Booking_Value"].mean()),
        "excluded_value": _nz(df.loc[df["Booking_Status"] != SUCCESS, "Booking_Value"].sum()),
        "excluded_rides": int((df["Booking_Status"] != SUCCESS).sum()),
    }


def revenue_by_payment(df: pd.DataFrame) -> pd.DataFrame:
    return (successful(df).groupby("Payment_Method")["Booking_Value"].sum()
            .sort_values(ascending=False).reset_index())


def revenue_by_vehicle(df: pd.DataFrame) -> pd.DataFrame:
    return (successful(df).groupby("Vehicle_Type")["Booking_Value"].sum()
            .sort_values(ascending=False).reset_index())


def revenue_trend(df: pd.DataFrame) -> pd.DataFrame:
    succ = successful(df)
    if succ.empty:
        return pd.DataFrame(columns=["Booking_Date", "Revenue", "Rolling_7d"])
    daily = succ.groupby("Booking_Date")["Booking_Value"].sum()
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max()), fill_value=0)
    out = daily.rename("Revenue").rename_axis("Booking_Date").reset_index()
    out["Rolling_7d"] = out["Revenue"].rolling(7, min_periods=1).mean()
    return out


# ---------------------------------------------------------------- Cancellations
def cancellation_summary(df: pd.DataFrame) -> dict:
    total = len(df)
    by_customer = int((df["Booking_Status"] == CUSTOMER_CANCEL).sum())   # SQL Rides_Cancelled_By_Customer
    by_driver = int((df["Booking_Status"] == DRIVER_CANCEL).sum())
    return {
        "by_customer": by_customer,
        "by_driver": by_driver,
        "driver_not_found": int((df["Booking_Status"] == NOT_FOUND).sum()),
        "cancel_pct": (by_customer + by_driver) / total * 100 if total else 0.0,   # DAX CanceledPercentage
        "personal_car": int((df["Canceled_Rides_by_Driver"] == PERSONAL_CAR_REASON).sum()),  # SQL view
        "incomplete": int((df["Incomplete_Rides"] == "Yes").sum()),
    }


def category_comparison(df: pd.DataFrame) -> pd.DataFrame:
    s = cancellation_summary(df)
    return pd.DataFrame({
        "Category": ["Canceled by Customer", "Canceled by Driver", "Driver Not Found", "Incomplete after pickup"],
        "Rides": [s["by_customer"], s["by_driver"], s["driver_not_found"], s["incomplete"]],
    })


def reason_counts(df: pd.DataFrame, column: str) -> pd.DataFrame:
    return df[column].dropna().value_counts().rename_axis("Reason").reset_index(name="Rides")


def unsuccessful_by_status_daily(df: pd.DataFrame) -> pd.DataFrame:
    bad = df[df["Booking_Status"] != SUCCESS]
    return bad.groupby(["Booking_Date", "Booking_Status"]).size().reset_index(name="Rides")


# ---------------------------------------------------------------- Ratings
def rating_summary(df: pd.DataFrame) -> dict:
    prime = df.loc[df["Vehicle_Type"] == "Prime Sedan", "Driver_Ratings"]   # SQL max_min_ratings
    return {
        "avg_customer": df["Customer_Rating"].mean(),
        "avg_driver": df["Driver_Ratings"].mean(),
        "prime_max": prime.max() if prime.notna().any() else None,
        "prime_min": prime.min() if prime.notna().any() else None,
    }


# ---------------------------------------------------------------- SQL view equivalents
def top_customers(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """SQL view top5customers."""
    out = df.groupby("Customer_ID")["Booking_ID"].count().rename("total_rides").reset_index()
    return out.sort_values(["total_rides", "Customer_ID"], ascending=[False, True]).head(n).reset_index(drop=True)


def upi_rides(df: pd.DataFrame) -> pd.DataFrame:
    """SQL view upi."""
    return df[df["Payment_Method"] == "UPI"]


def incomplete_rides(df: pd.DataFrame) -> pd.DataFrame:
    """SQL view incomplete_rides."""
    return df.loc[df["Incomplete_Rides"] == "Yes", ["Booking_ID", "Incomplete_Rides_Reason"]]
