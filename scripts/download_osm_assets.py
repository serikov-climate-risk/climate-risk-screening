"""Download infrastructure assets for the Belgrade case from OpenStreetMap (Overpass)."""
import json
from pathlib import Path
import requests

BBOX = (44.55, 20.0, 45.05, 20.85)  # S, W, N, E
QUERIES = {
    "wastewater_plant": 'nwr["man_made"="wastewater_plant"]',
    "water_works": 'nwr["man_made"="water_works"]',
    "water_tower_pumping": 'nwr["man_made"~"^(pumping_station|water_tower|water_well)$"]',
    "substation": 'nwr["power"="substation"]',
    "power_plant": 'nwr["power"="plant"]',
    "rail_station": 'nwr["railway"="station"]',
    "bus_station": 'nwr["amenity"="bus_station"]',
    "tram_depot": 'nwr["landuse"="depot"]',
    "hospital": 'nwr["amenity"="hospital"]',
    "fuel_storage": 'nwr["industrial"~"^(oil|gas|fuel)$"]',
    "industrial_site": 'nwr["landuse"="industrial"](if: length() >= 0)',
}
out = Path(__file__).resolve().parents[1] / "data" / "raw" / "osm"
out.mkdir(parents=True, exist_ok=True)
s, w, n, e = BBOX
for name, q in QUERIES.items():
    q = q.replace("(if: length() >= 0)", "")
    ql = f"[out:json][timeout:120];({q}({s},{w},{n},{e}););out center tags;"
    for url in ("https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"):
        r = requests.post(url, data={"data": ql}, headers={"User-Agent": "climate-risk-screening/0.1 (research study)"}, timeout=200)
        if r.ok:
            (out / f"{name}.json").write_text(r.text, encoding="utf-8")
            print(name, len(r.json()["elements"]))
            break
        print(name, "failed", url, r.status_code)
