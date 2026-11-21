"""Asset inventory from OpenStreetMap extracts (Overpass JSON files in data/raw/osm)."""
from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = ROOT / "data" / "raw" / "osm"

# OSM layer file -> (asset class, sector). Industrial land-use polygons are not used as assets.
LAYERS = {
    "wastewater_plant": ("wastewater_plant", "water"),
    "water_works": ("water_works", "water"),
    "water_tower_pumping": ("pumping_station", "water"),
    "substation": ("substation", "energy"),
    "power_plant": ("power_plant", "energy"),
    "rail_station": ("rail_station", "transport"),
    "bus_station": ("bus_station", "transport"),
    "hospital": ("hospital", "social"),
    "fuel_storage": ("fuel_storage", "energy"),
}


def _voltage_kv(tags: dict) -> float:
    v = tags.get("voltage", "")
    vals = []
    for part in str(v).replace(",", ";").split(";"):
        try:
            vals.append(float(part) / 1000.0)
        except ValueError:
            pass
    return max(vals) if vals else float("nan")


def load_assets(osm_dir: Path = OSM_DIR) -> gpd.GeoDataFrame:
    rows = []
    for layer, (cls, sector) in LAYERS.items():
        f = osm_dir / f"{layer}.json"
        if not f.exists():
            continue
        for el in json.loads(f.read_text(encoding="utf-8"))["elements"]:
            if el["type"] == "node":
                lat, lon = el["lat"], el["lon"]
            elif "center" in el:
                lat, lon = el["center"]["lat"], el["center"]["lon"]
            else:
                continue
            tags = el.get("tags", {})
            c = cls
            if cls == "substation":
                kv = _voltage_kv(tags)
                c = "substation_transmission" if kv >= 110 else "substation_distribution"
            # power plants without any generator source are skipped later by the value table if unknown
            rows.append({
                "osm_id": f'{el["type"][0]}{el["id"]}',
                "name": tags.get("name", ""),
                "asset_class": c,
                "sector": sector,
                "lat": lat,
                "lon": lon,
            })
    df = pd.DataFrame(rows).drop_duplicates(subset=["osm_id"])
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.lon, df.lat), crs="EPSG:4326")
