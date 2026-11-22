"""Download CMIP6 daily maximum near-surface air temperature for the Belgrade area from the CDS (historical, SSP2-4.5, SSP5-8.5)."""
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import cdsapi

out = Path(__file__).resolve().parents[1] / "data" / "raw" / "cmip6"
out.mkdir(parents=True, exist_ok=True)
MODELS = ["mpi_esm1_2_lr", "ec_earth3", "ipsl_cm6a_lr"]
JOBS = []
for m in MODELS:
    JOBS.append((m, "historical", list(range(1995, 2015))))
    for exp in ("ssp2_4_5", "ssp5_8_5"):
        JOBS.append((m, exp, list(range(2041, 2061))))

def fetch(job):
    model, exp, years = job
    f = out / f"tmax_{model}_{exp}_{years[0]}_{years[-1]}.zip"
    if f.exists():
        return
    try:
        cdsapi.Client().retrieve(
            "projections-cmip6",
            {
                "temporal_resolution": "daily",
                "experiment": exp,
                "variable": "daily_maximum_near_surface_air_temperature",
                "model": model,
                "year": [str(y) for y in years],
                "month": [f"{m:02d}" for m in range(1, 13)],
                "day": [f"{d:02d}" for d in range(1, 32)],
                "area": [45.5, 20.0, 44.0, 21.0],
                "data_format": "netcdf",
            },
            str(f),
        )
    except Exception as e:
        print("FAILED", job[:2], e, file=sys.stderr)

for j in JOBS:   # the CDS accepts few queued requests per dataset: one at a time, retry when rejected
    for attempt in range(40):
        fetch(j)
        if (out / f"tmax_{j[0]}_{j[1]}_{j[2][0]}_{j[2][-1]}.zip").exists():
            break
        time.sleep(180)
print("done")
