"""Heat exposure: daily maximum temperature from ERA5 (point near Belgrade) and delta-method warming scenarios."""
from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ERA5 = ROOT / "data" / "raw" / "era5" / "era5_t2m_belgrade_1991_2020.zip"


def load_tmax(path: Path = ERA5) -> tuple[np.ndarray, np.ndarray]:
    """Daily maximum 2 m temperature (deg C) and the year of each day, from the hourly CDS point series (CSV in a zip)."""
    with zipfile.ZipFile(path) as z:
        name = [n for n in z.namelist() if n.endswith(".csv")][0]
        df = pd.read_csv(z.open(name))
    tcol = [c for c in df.columns if "time" in c.lower()][0]
    vcol = [c for c in df.columns if c.lower().startswith(("t2m", "2m_t", "temperature"))][0]
    df[tcol] = pd.to_datetime(df[tcol])
    s = df.set_index(tcol)[vcol] - 273.15
    daily = s.resample("D").max().dropna()
    return daily.to_numpy(), daily.index.year.to_numpy()
