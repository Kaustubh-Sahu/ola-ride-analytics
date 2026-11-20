"""The five dashboard pages plus the data preview section."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from modules import calculations as calc
from modules import charts
from modules.ui import fmt_inr, fmt_int, fmt_num, kpi_row, page_header, show


# ---------------------------------------------------------------- Overall
def render_overall(df: pd.DataFrame, summary: str) -> None:
    page_header("Overall Dashboard", summary)
    k = calc.overall_kpis(df)
    kpi_row([
        ("Total Bookings", fmt_int(k["total_bookings"]), "All booking requests"),
        ("Successful Bookings", fmt_int(k["successful_bookings"]), "Status = Success"),
        ("Success Rate", f"{k['success_rate']:.1f}%", "Successful ÷ total bookings"),
        ("Booking Value", fmt_inr(k["successful_value"]),
         f"Successful rides only · {fmt_inr(k['all_quoted_value'])} quoted across all bookings"),
    ])
    kpi_row([
        ("Total Ride Distance", f"{fmt_int(k['total_distance'])} km", "Cancelled rides cover 0 km"),
        ("Avg Ride Distance", f"{fmt_num(k['avg_distance_completed'], 1)} km", "Per successful ride"),
        ("Total Customers", fmt_int(k["total_customers"]), "Unique Customer_ID"),
    ])

    left, right = st.columns([1, 1.6])
    with left:
        status = calc.status_distribution(df)
        show(charts.donut(status, "Booking_Status", "Bookings", "Booking status distribution",
                          colors=charts.STATUS_COLORS, center_text=fmt_int(k["total_bookings"])))
    with right:
        show(charts.bookings_trend(calc.bookings_over_time(df), "Bookings over time"))

    left, right = st.columns([1.6, 1])
    with left:
        show(charts.bar(calc.distance_by_vehicle(df), "Vehicle_Type", "Total_Distance",
                        "Ride distance by vehicle type (km)", label="Total distance (km)"))
    with right:
        show(charts.donut(calc.payment_distribution(df), "Payment_Method", "Rides", "Payment method distribution"))


# ---------------------------------------------------------------- Vehicle type
def render_vehicle(df: pd.DataFrame, summary: str) -> None:
    page_header("Vehicle Type Analysis", summary)
    v = calc.vehicle_summary(df)
    if v.empty:
        st.info("No vehicle data for the current filters.")
        return
    top_b, top_r = v.iloc[0], v.loc[v["Booking_Value"].idxmax()]
    rated = v.dropna(subset=["Avg_Customer_Rating"])
    top_rated = rated.loc[rated["Avg_Customer_Rating"].idxmax()] if not rated.empty else None
    far = v.loc[v["Avg_Distance_Completed"].idxmax()] if v["Avg_Distance_Completed"].notna().any() else None
    kpi_row([
        ("Most Booked", top_b["Vehicle_Type"], f"{fmt_int(top_b['Bookings'])} bookings"),
        ("Highest Revenue", top_r["Vehicle_Type"], fmt_inr(top_r["Booking_Value"])),
        ("Best Customer Rating", top_rated["Vehicle_Type"] if top_rated is not None else "–",
         f"{fmt_num(top_rated['Avg_Customer_Rating'])} avg" if top_rated is not None else ""),
        ("Longest Avg Ride", far["Vehicle_Type"] if far is not None else "–",
         f"{fmt_num(far['Avg_Distance_Completed'], 1)} km per successful ride" if far is not None else ""),
    ])

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(v, "Vehicle_Type", "Bookings", "Total bookings by vehicle type"))
    with c2:
        show(charts.donut(v, "Vehicle_Type", "Bookings", "Vehicle-wise booking distribution"))

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(v, "Vehicle_Type", "Booking_Value", "Booking value by vehicle type (successful rides)",
                        prefix="₹", label="Booking value"))
    with c2:
        show(charts.grouped_bar(
            v, "Vehicle_Type",
            {"Avg_Distance_All": "All bookings (SQL avg_ride_distance)", "Avg_Distance_Completed": "Successful rides only"},
            "Average ride distance (km)", fmt=".1f"))
        st.caption("The SQL view averages every booking, including cancelled ones that have 0 km, "
                   "so it is lower than the average of rides actually completed.")

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(v, "Vehicle_Type", "Avg_Customer_Rating", "Average customer rating", fmt=".2f",
                        label="Avg customer rating", value_range=(3, 5.3)))
        st.caption("Ratings are on a 3–5 scale in this dataset, so the axis starts at 3.")
    with c2:
        show(charts.stacked_bar(calc.status_by_vehicle(df), "Vehicle_Type", "Bookings", "Booking_Status",
                                "Booking outcome mix by vehicle type", percent=True,
                                color_map=charts.STATUS_COLORS))

    st.markdown('<div class="section">Vehicle comparison table</div>', unsafe_allow_html=True)
    table = v[["Vehicle_Type", "Bookings", "Successful", "Success_Rate", "Booking_Value", "Total_Distance",
               "Avg_Distance_All", "Avg_Distance_Completed", "Avg_Customer_Rating", "Avg_Driver_Rating"]]
    st.dataframe(table, hide_index=True, width="stretch", column_config={
        "Success_Rate": st.column_config.NumberColumn("Success %", format="%.1f%%"),
        "Booking_Value": st.column_config.NumberColumn("Booking value (₹)", format="₹%d"),
        "Total_Distance": st.column_config.NumberColumn("Total km", format="%d"),
        "Avg_Distance_All": st.column_config.NumberColumn("Avg km (all)", format="%.2f"),
        "Avg_Distance_Completed": st.column_config.NumberColumn("Avg km (completed)", format="%.2f"),
        "Avg_Customer_Rating": st.column_config.NumberColumn("Cust. rating", format="%.2f"),
        "Avg_Driver_Rating": st.column_config.NumberColumn("Driver rating", format="%.2f"),
    })


# ---------------------------------------------------------------- Revenue
def render_revenue(df: pd.DataFrame, summary: str) -> None:
    page_header("Revenue Analysis", summary + " · revenue counts successful rides only")
    k = calc.revenue_kpis(df)
    kpi_row([
        ("Total Successful Booking Value", fmt_inr(k["total_value"]), "SQL: total_Booking_Value"),
        ("Successful Rides", fmt_int(k["successful_rides"]), "Revenue-generating rides"),
        ("Avg Booking Value", fmt_inr(k["avg_value"]), "Per successful ride"),
        ("Excluded Value", fmt_inr(k["excluded_value"]),
         f"{fmt_int(k['excluded_rides'])} cancelled / unfulfilled bookings, not counted"),
    ])
    trend = calc.revenue_trend(df)
    if trend.empty:
        st.info("No successful bookings for the current filters, so there is no revenue to show.")
        return
    show(charts.revenue_trend(trend, "Revenue trend over time"))

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(calc.revenue_by_payment(df), "Payment_Method", "Booking_Value",
                        "Revenue by payment method", prefix="₹", label="Revenue"))
    with c2:
        show(charts.bar(calc.revenue_by_vehicle(df), "Vehicle_Type", "Booking_Value",
                        "Revenue by vehicle type", prefix="₹", label="Revenue", horizontal=True))

    succ = calc.successful(df)
    c1, c2 = st.columns(2)
    with c1:
        show(charts.histogram(succ, "Booking_Value", "Booking value distribution (successful rides)",
                              nbins=40, prefix="₹"))
    with c2:
        show(charts.box(succ, "Vehicle_Type", "Booking_Value", "Booking value spread by vehicle type"))


# ---------------------------------------------------------------- Cancellations
def render_cancellations(df: pd.DataFrame, summary: str) -> None:
    page_header("Cancellation Analysis", summary)
    s = calc.cancellation_summary(df)
    kpi_row([
        ("Cancelled by Customers", fmt_int(s["by_customer"]), "Status = Canceled by Customer"),
        ("Cancelled by Drivers", fmt_int(s["by_driver"]), "Status = Canceled by Driver"),
        ("Cancellation %", f"{s['cancel_pct']:.2f}%", "(Customer + Driver cancellations) ÷ total"),
    ])
    kpi_row([
        ("Driver Not Found", fmt_int(s["driver_not_found"]), "Unfulfilled, not in cancellation %"),
        ("Incomplete Rides", fmt_int(s["incomplete"]), "Started but not completed"),
        ("Driver: Personal & Car Issue", fmt_int(s["personal_car"]), "SQL: personal_and_car_related_issues"),
    ])

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(calc.category_comparison(df), "Category", "Rides", "Cancellation categories compared",
                        label="Rides"))
    with c2:
        by_vehicle = calc.status_by_vehicle(df)
        by_vehicle = by_vehicle[by_vehicle["Booking_Status"] != calc.SUCCESS]
        show(charts.stacked_bar(by_vehicle, "Vehicle_Type", "Bookings", "Booking_Status",
                                "Unsuccessful bookings by vehicle type", color_map=charts.STATUS_COLORS))

    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(calc.reason_counts(df, "Canceled_Rides_by_Driver"), "Reason", "Rides",
                        "Driver cancellation reasons", horizontal=True))
    with c2:
        show(charts.bar(calc.reason_counts(df, "Canceled_Rides_by_Customer"), "Reason", "Rides",
                        "Customer cancellation reasons", horizontal=True))

    c1, c2 = st.columns([1, 1.6])
    with c1:
        show(charts.donut(calc.reason_counts(df, "Incomplete_Rides_Reason"), "Reason", "Rides",
                          "Incomplete ride reasons", center_text=fmt_int(s["incomplete"])))
    with c2:
        show(charts.stacked_bar(calc.unsuccessful_by_status_daily(df), "Booking_Date", "Rides", "Booking_Status",
                                "Daily unsuccessful bookings", color_map=charts.STATUS_COLORS))


# ---------------------------------------------------------------- Ratings
def render_ratings(df: pd.DataFrame, summary: str) -> None:
    page_header("Ratings Analysis", summary + " · ratings exist only for completed rides")
    r = calc.rating_summary(df)
    kpi_row([
        ("Avg Customer Rating", fmt_num(r["avg_customer"]), "Out of 5"),
        ("Avg Driver Rating", fmt_num(r["avg_driver"]), "Out of 5"),
        ("Prime Sedan · Max Driver Rating", fmt_num(r["prime_max"], 1), "SQL: max_min_ratings"),
        ("Prime Sedan · Min Driver Rating", fmt_num(r["prime_min"], 1), "SQL: max_min_ratings"),
    ])
    v = calc.vehicle_summary(df)
    if v.empty:
        st.info("No data for the current filters.")
        return
    c1, c2 = st.columns(2)
    with c1:
        show(charts.bar(v, "Vehicle_Type", "Avg_Customer_Rating", "Customer ratings by vehicle type", fmt=".2f",
                        label="Avg customer rating", value_range=(3, 5.3)))
    with c2:
        show(charts.bar(v, "Vehicle_Type", "Avg_Driver_Rating", "Driver ratings by vehicle type", fmt=".2f",
                        label="Avg driver rating", value_range=(3, 5.3)))
    st.caption("Ratings are on a 3–5 scale in this dataset, so the axes start at 3.")

    c1, c2 = st.columns(2)
    with c1:
        show(charts.overlay_histogram(
            {"Customer rating": df["Customer_Rating"], "Driver rating": df["Driver_Ratings"]},
            "Rating distribution"))
    with c2:
        prime = df.loc[df["Vehicle_Type"] == "Prime Sedan", "Driver_Ratings"].dropna()
        if prime.empty:
            st.info("No rated Prime Sedan bookings in the current filters.")
        else:
            show(charts.histogram(prime.to_frame(), "Driver_Ratings",
                                  "Prime Sedan driver rating distribution", nbins=20))


# ---------------------------------------------------------------- Data preview
def render_data_section(df: pd.DataFrame) -> None:
    st.markdown('<div class="section">Data preview</div>', unsafe_allow_html=True)
    with st.expander(f"Explore filtered data ({len(df):,} rows) and SQL view equivalents"):
        tabs = st.tabs(["Filtered data", "Successful bookings", "UPI rides", "Incomplete rides", "Top 5 customers"])
        with tabs[0]:
            st.dataframe(df.drop(columns=["Booking_Date"]).head(1000), hide_index=True, width="stretch")
            st.caption("Showing the first 1,000 rows. Use the sidebar button to download everything as CSV.")
        with tabs[1]:
            st.caption("SQL view: Successfull_Booking")
            st.dataframe(calc.successful(df).drop(columns=["Booking_Date"]).head(1000), hide_index=True, width="stretch")
        with tabs[2]:
            st.caption("SQL view: upi")
            st.dataframe(calc.upi_rides(df).drop(columns=["Booking_Date"]).head(1000), hide_index=True, width="stretch")
        with tabs[3]:
            st.caption("SQL view: incomplete_rides")
            st.dataframe(calc.incomplete_rides(df), hide_index=True, width="stretch")
        with tabs[4]:
            st.caption("SQL view: top5customers")
            st.dataframe(calc.top_customers(df), hide_index=True, width="stretch")
