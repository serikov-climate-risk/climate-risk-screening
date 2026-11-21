"""Flood depth at assets from the JRC / CEMS GloFAS global river flood hazard maps (3 arc seconds, v2.1.2)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import Window

from .parameters import RETURN_PERIODS

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
TILE = "ID134_N50_E20"


def sample_depth(gdf, rp: int, half_window: int = 1, raw: Path = RAW) -> np.ndarray:
    """Maximum depth (m) in a (2*half_window+1)^2 pixel window around each asset (about 90 m per pixel).

    The default is the pixel containing the asset (half_window 0). A larger window is conservative but picks up
    river-channel cells next to bank assets; it is used as a sensitivity only. Nodata is treated as dry land. Depths above 10 m are the known artefact class of the dataset and are capped at 10.
    """
    path = raw / f"{TILE}_RP{rp}_depth.tif"
    out = np.zeros(len(gdf))
    with rasterio.open(path) as src:
        for i, (x, y) in enumerate(zip(gdf.geometry.x, gdf.geometry.y)):
            r, c = src.index(x, y)
            w = Window(c - half_window, r - half_window, 2 * half_window + 1, 2 * half_window + 1)
            a = src.read(1, window=w, boundless=True, fill_value=src.nodata)
            a = np.where((a == src.nodata) | ~np.isfinite(a), 0.0, a)
            out[i] = min(float(a.max()), 10.0)
    return out


def depth_table(gdf, rps=RETURN_PERIODS, half_window: int = 0, raw: Path = RAW) -> pd.DataFrame:
    return pd.DataFrame({f"depth_rp{rp}": sample_depth(gdf, rp, half_window, raw=raw) for rp in rps}, index=gdf.index)
