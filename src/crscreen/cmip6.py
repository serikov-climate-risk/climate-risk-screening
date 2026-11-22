"""Heat scenarios from CMIP6 by the quantile delta method.

For each model the change between its historical run (1995-2014) and a scenario run (2041-2060) is taken per quantile of
daily maximum temperature at the nearest grid cell, and added to the ERA5 daily maxima (1991-2020) at the same quantile.
Hot days shift by their own quantile change, not by one number for all days (the previous screening used a uniform shift).
Daily series come from the Pangeo CMIP6 archive (scripts/download_cmip6_pangeo.py). One grid cell per model (50 to 200 km),
first ensemble member, no bias correction beyond the quantile shift; the model's own bias against ERA5 is reported.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "data" / "raw" / "cmip6_pangeo"
P_GRID = np.concatenate([np.linspace(0.005, 0.995, 199)])


def load_series(model: str, exp: str) -> np.ndarray:
    df = pd.read_csv(DIR / f"tmax_{model}_{exp}.csv")
    return df["tasmax_K"].to_numpy(float) - 273.15


def models_complete() -> list[str]:
    out = []
    for f in sorted(DIR.glob("tmax_*_historical.csv")):
        m = f.name[len("tmax_"):-len("_historical.csv")]
        if all((DIR / f"tmax_{m}_{e}.csv").exists() for e in ("ssp245", "ssp585")):
            out.append(m)
    return out


def quantile_delta(hist: np.ndarray, fut: np.ndarray) -> np.ndarray:
    return np.quantile(fut, P_GRID) - np.quantile(hist, P_GRID)


def apply_delta(era5: np.ndarray, delta: np.ndarray) -> np.ndarray:
    """Add the quantile delta to ERA5 values: the delta at the empirical quantile of each value (linear interpolation)."""
    ranks = (np.argsort(np.argsort(era5)) + 0.5) / len(era5)
    return era5 + np.interp(ranks, P_GRID, delta)


def heat_days_table(era5: np.ndarray, years: np.ndarray, threshold: float) -> pd.DataFrame:
    """Days per year above the threshold: ERA5 baseline and each model and scenario, plus the model's own historical value."""
    ny = len(np.unique(years))
    rows = [{"model": "ERA5", "scenario": "baseline", "days_per_year": float((era5 > threshold).sum() / ny), "model_hist_days_per_year": np.nan,
             "mean_warming_k": 0.0}]
    for m in models_complete():
        h = load_series(m, "historical")
        h_days = float((h > threshold).sum() / (len(h) / 365.25))
        for exp in ("ssp245", "ssp585"):
            f = load_series(m, exp)
            d = quantile_delta(h, f)
            shifted = apply_delta(era5, d)
            rows.append({"model": m, "scenario": exp, "days_per_year": float((shifted > threshold).sum() / ny),
                         "model_hist_days_per_year": h_days, "mean_warming_k": float(f.mean() - h.mean())})
    return pd.DataFrame(rows)


def scenario_days(table: pd.DataFrame) -> dict[str, float]:
    """Baseline = ERA5; moderate = median over models of SSP2-4.5 2041-2060; high = median over models of SSP5-8.5 2041-2060."""
    t = table[table.model != "ERA5"]
    return {"baseline": float(table.loc[table.model == "ERA5", "days_per_year"].iloc[0]),
            "moderate": float(t[t.scenario == "ssp245"].days_per_year.median()),
            "high": float(t[t.scenario == "ssp585"].days_per_year.median())}
