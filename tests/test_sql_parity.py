"""Run the project's real SQL file (in SQLite) and compare every view with the Pandas implementation."""
import re
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from modules import calculations as calc

SQL_FILE = Path(__file__).resolve().parent.parent / "sql" / "OlaDataSQLqueries.sql"


@pytest.fixture(scope="module")
def con(df):
    con = sqlite3.connect(":memory:")
    df.drop(columns=["Booking_Date"]).assign(Date=df["Date"].astype(str)).to_sql("OlaData", con, index=False)
    script = SQL_FILE.read_text()
    script = re.sub(r"(?im)^\s*(create database|use)\b[^;]*;", "", script)
    script = re.sub(r"(?im)^\s*select \* from OlaData;", "", script)
    con.executescript(script)
    return con


def q(con, sql):
    return pd.read_sql(sql, con)


def test_total_booking_value(con, df):
    assert q(con, "select * from total_Booking_Value").iloc[0, 0] == calc.revenue_kpis(df)["total_value"]


def test_successful_bookings(con, df):
    assert len(q(con, "select * from Successfull_Booking")) == len(calc.successful(df))


def test_customer_cancellations(con, df):
    assert q(con, "select * from Rides_Cancelled_By_Customer").iloc[0, 0] == calc.cancellation_summary(df)["by_customer"]


def test_personal_car_issue(con, df):
    assert q(con, "select * from personal_and_car_related_issues").iloc[0, 0] == calc.cancellation_summary(df)["personal_car"]


def test_prime_sedan_ratings(con, df):
    row = q(con, "select * from max_min_ratings").iloc[0]
    r = calc.rating_summary(df)
    assert row["max_ratings"] == r["prime_max"] and row["min_ratings"] == r["prime_min"]


def test_upi_and_incomplete(con, df):
    assert len(q(con, "select * from upi")) == len(calc.upi_rides(df))
    assert len(q(con, "select * from incomplete_rides")) == len(calc.incomplete_rides(df))


def test_avg_distance_and_rating_by_vehicle(con, df):
    v = calc.vehicle_summary(df).set_index("Vehicle_Type")
    dist = q(con, "select * from avg_ride_distance").set_index("Vehicle_Type")["avg_distance"]
    rating = q(con, "select * from avg_customer_rating").set_index("Vehicle_Type")["avg_Ratings"]
    for vt in v.index:
        assert dist[vt] == pytest.approx(v.loc[vt, "Avg_Distance_All"])
        assert rating[vt] == round(v.loc[vt, "Avg_Customer_Rating"], 2)


def test_top5_customers(con, df):
    sql = q(con, "select * from top5customers")["total_rides"].tolist()
    assert sql == calc.top_customers(df)["total_rides"].tolist()
