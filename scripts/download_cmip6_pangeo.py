"""CMIP6 daily maximum near-surface air temperature at the grid cell nearest to Belgrade from the Pangeo cloud archive (no CDS queue).

Experiments: historical 1995-2014, ssp245 and ssp585 2041-2060. Models: those with all three experiments, first member
(r1i1p1f1 where available), up to 4 (the link is slow). Output: data/raw/cmip6_pangeo/tmax_<model>_<experiment>.csv (daily series at the nearest cell)."""
import sys
from pathlib import Path

import pandas as pd
import xarray as xr
import gcsfs

LAT, LON = 44.8, 20.5
OUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "cmip6_pangeo"
OUT.mkdir(parents=True, exist_ok=True)
cat_f = OUT / "pangeo-cmip6.csv"
if not cat_f.exists():
    pd.read_csv("https://storage.googleapis.com/cmip6/pangeo-cmip6.csv").to_csv(cat_f, index=False)
c = pd.read_csv(cat_f, low_memory=False)
c = c[(c.variable_id == "tasmax") & (c.table_id == "day") & c.experiment_id.isin(["historical", "ssp245", "ssp585"])]
have = c.groupby("source_id").experiment_id.nunique()
models = sorted(have[have == 3].index)
fs = gcsfs.GCSFileSystem(token="anon")
done = []
for m in models:
    if len(done) >= 4:
        break
    ok = True
    for exp, (y0, y1) in (("historical", (1995, 2014)), ("ssp245", (2041, 2060)), ("ssp585", (2041, 2060))):
        f = OUT / f"tmax_{m}_{exp}.csv"
        if f.exists():
            continue
        r = c[(c.source_id == m) & (c.experiment_id == exp)].sort_values("member_id")
        if r.empty:
            ok = False
            break
        row = r[r.member_id.str.startswith("r1i1p1")].iloc[0] if r.member_id.str.startswith("r1i1p1").any() else r.iloc[0]
        try:
            ds = xr.open_zarr(fs.get_mapper(row.zstore), consolidated=True)
            lon = LON if float(ds.lon.max()) > 180 else LON
            x = ds.tasmax.sel(lat=LAT, lon=lon, method="nearest").sel(time=slice(f"{y0}-01-01", f"{y1}-12-31")).load()
            x.to_series().rename("tasmax_K").to_csv(f)
            print(m, exp, row.member_id, len(x), flush=True)
        except Exception as e:
            print("FAILED", m, exp, repr(e)[:150], flush=True)
            ok = False
            break
    if ok:
        done.append(m)
print("models complete:", done)
