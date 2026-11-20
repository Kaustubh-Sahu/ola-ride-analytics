import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from modules.data_cleaning import clean_data  # noqa: E402


@pytest.fixture(scope="session")
def raw():
    return pd.read_csv(ROOT / "data" / "OlaData.csv", low_memory=False)


@pytest.fixture(scope="session")
def df(raw):
    return clean_data(raw)[0]
