# Ola Ride Booking Analytics: SQL + Power BI + Streamlit

End-to-end analytics project: **MySQL queries → Power BI dashboard → interactive Streamlit web app**.

- `sql/` – MySQL database setup and the 10 analysis views
- `powerbi/` – the original Power BI dashboard (`OlaDashboard.pbix`, open with Power BI Desktop)
- the Streamlit app (this folder's root) – web version of the dashboard

An interactive analytics app built from an existing **SQL + Power BI** project on Ola ride-booking data
(103,024 bookings, July 2024). It keeps the five report pages of the Power BI dashboard
(Overall, Vehicle Type, Revenue, Cancellations, Ratings) and reproduces every SQL view in Pandas.

## Features
- Sidebar navigation (5 pages) and filters: **date range, vehicle type, booking status, payment method**, with a **Clear filters** button. Every KPI and chart reacts to the filters.
- Data from the **bundled dataset**, an **uploaded CSV / Excel** file, or **MySQL**.
- Data cleaning (whitespace, `null` / `#NAME?` placeholders, types, invalid dates, duplicates) with a data-quality report.
- **Download filtered data as CSV**, plus a data preview with the SQL view equivalents (successful bookings, UPI rides, incomplete rides, top 5 customers).
- Dark UI, interactive Plotly charts with hover details.

## Where the data comes from
The dataset was **extracted from your `OlaDashboard.pbix`** (the `OlaData` table is embedded in it) and saved as
`data/OlaData.csv`. Nothing is generated or simulated. Two empty columns from the Power BI model
(`Vehicle Images` = `#NAME?`, `Column1`) were dropped.

## Calculation rules (same as the SQL / DAX)
| Metric | Rule |
|---|---|
| Revenue / total booking value | `SUM(Booking_Value)` where `Booking_Status = 'Success'` only. Cancelled and unfulfilled bookings also carry a fare in the data (about ₹2.15 Cr), so they must not be counted. |
| Cancellation % | (Canceled by Customer + Canceled by Driver) ÷ all bookings, as in the Power BI `CanceledPercentage` measure. `Driver Not Found` is shown separately. |
| Average ride distance (SQL view) | Average over **all** bookings, including cancelled ones with 0 km. The app also shows the average over successful rides. |
| AVG / MAX / MIN | Ignore missing values, like SQL. |

`tests/test_sql_parity.py` runs your real `.sql` file against the data (in SQLite) and checks that every view matches the app's numbers.

## Project structure
```
ola-ride-analytics/
├── app.py                      # Streamlit entry point
├── requirements.txt
├── README.md
├── data/
│   └── OlaData.csv             # dataset extracted from the PBIX
├── modules/                    # app code
│   ├── data_loader.py          # bundled CSV / upload / MySQL (cached)
│   ├── data_cleaning.py
│   ├── calculations.py         # all metrics (mirror the SQL views)
│   ├── charts.py               # Plotly figures
│   ├── filters.py              # sidebar filters
│   ├── ui.py                   # KPI cards, formatting
│   └── views.py                # the 5 pages + data preview
├── assets/style.css
├── sql/
│   └── OlaDataSQLqueries.sql   # database, table views and analysis queries
├── powerbi/
│   └── OlaDashboard.pbix       # original Power BI report
├── scripts/load_csv_to_mysql.py
├── tests/                      # SQL-parity + app smoke tests
├── docs/screenshots/           # add screenshots here
└── .streamlit/config.toml      # dark theme
```

## Setup on Windows (VS Code)
Open the project folder in VS Code, then open a terminal (**Terminal → New Terminal**, PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```
If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use Command Prompt
(`.venv\Scripts\activate.bat`). In VS Code press `Ctrl+Shift+P` → *Python: Select Interpreter* → pick `.venv`.
The app opens at http://localhost:8501.

## Using your own dataset
Sidebar → **Data source → Upload CSV / Excel** → drop a `.csv` or `.xlsx` with the same columns as the `OlaData` table:
`Date, Booking_ID, Booking_Status, Customer_ID, Vehicle_Type, Canceled_Rides_by_Customer, Canceled_Rides_by_Driver,
Incomplete_Rides, Incomplete_Rides_Reason, Booking_Value, Payment_Method, Ride_Distance, Driver_Ratings, Customer_Rating`.
A clear message is shown if a column is missing. To change the default, replace `data/OlaData.csv`.

## Connecting MySQL
1. Install MySQL and create the data. Either run your own import, or use the helper:
   ```powershell
   python scripts/load_csv_to_mysql.py --user root --password YOUR_PASSWORD
   ```
   Then run `sql/OlaDataSQLqueries.sql` in MySQL Workbench to create the views.
2. In the app: **Data source → MySQL database**, enter host / port / user / password / database (`OLA`) / table (`OlaData`) and press **Connect**.
3. Optional: pre-fill the form by copying `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` (git-ignored).

## Tests
```powershell
pip install -r requirements-dev.txt
pytest
```

## Interview talking points
- Revenue is limited to successful rides; the fares of cancelled bookings are deliberately excluded.
- The SQL average distance includes 0-km cancelled bookings; the app shows both versions.
- Power BI's cancellation % excludes "Driver Not Found"; the app keeps that definition and reports it separately.
