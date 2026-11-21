"""Download ERA5 hourly 2 m temperature at a point near Belgrade, 1991-2020, from the CDS point time-series dataset."""
from pathlib import Path
import cdsapi

out = Path(__file__).resolve().parents[1] / "data" / "raw" / "era5"
out.mkdir(parents=True, exist_ok=True)
f = out / "era5_t2m_belgrade_1991_2020.zip"
if not f.exists():
    cdsapi.Client().retrieve(
        "reanalysis-era5-single-levels-timeseries",
        {
            "variable": ["2m_temperature"],
            "location": {"longitude": 20.45, "latitude": 44.8},
            "date": ["1991-01-01/2020-12-31"],
            "data_format": "csv",
        },
        str(f),
    )
print("done")
