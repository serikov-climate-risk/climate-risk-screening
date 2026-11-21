"""Download the JRC / CEMS GloFAS global river flood hazard tile covering Belgrade (ID134_N50_E20) for five return periods."""
from pathlib import Path
import requests

BASE = "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/CEMS-GLOFAS/flood_hazard"
OUT = Path(__file__).resolve().parents[1] / "data" / "raw"
OUT.mkdir(parents=True, exist_ok=True)
for rp in (10, 50, 100, 200, 500):
    name = f"ID134_N50_E20_RP{rp}_depth.tif"
    f = OUT / name
    if f.exists():
        continue
    with requests.get(f"{BASE}/RP{rp}/{name}", stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(f, "wb") as fh:
            for chunk in r.iter_content(1 << 20):
                fh.write(chunk)
    print("downloaded", name)
for name in ("README.txt", "copyright.txt"):
    f = OUT / name
    if not f.exists():
        f.write_bytes(requests.get(f"{BASE}/{name}", timeout=60).content)
