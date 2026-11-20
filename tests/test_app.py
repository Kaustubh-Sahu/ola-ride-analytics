"""Smoke tests: every page renders, every filter works, no exceptions."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parent.parent / "app.py")
PAGES = ["Overall", "Vehicle Type", "Revenue", "Cancellations", "Ratings"]


def run():
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    return at


@pytest.mark.parametrize("page", PAGES)
def test_each_page_renders(page):
    at = run()
    at.sidebar.radio(key="page").set_value(page).run()
    assert not at.exception, [e.value for e in at.exception]
    assert not at.error


def test_filters_update_kpis():
    at = run()
    base = at.markdown[[("Total Bookings" in m.value) for m in at.markdown].index(True)].value
    vehicle = next(w for w in at.sidebar.multiselect if w.label == "Vehicle type")
    vehicle.set_value(["Auto"]).run()
    assert not at.exception
    filtered = next(m.value for m in at.markdown if "Total Bookings" in m.value)
    assert filtered != base


def test_empty_filter_result_shows_warning():
    at = run()
    next(w for w in at.sidebar.multiselect if w.label == "Vehicle type").set_value(["Auto"]).run()
    next(w for w in at.sidebar.multiselect if w.label == "Booking status").set_value(["Driver Not Found"]).run()
    next(w for w in at.sidebar.multiselect if w.label == "Payment method").set_value(["UPI"]).run()
    assert not at.exception
    assert at.warning, "expected the 'no bookings match' warning"
