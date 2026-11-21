"""Assumed parameters. All values are illustrative screening assumptions, listed in data/sources.csv.

Nothing here is an EBRD, MDB or client figure. The depth-damage curves have the shape of generic
infrastructure curves (damage fraction rising with depth to total loss at about 6 m) but are not copied
from a published table; replace them with a published set before any use beyond screening.
"""
from __future__ import annotations

import numpy as np

# Replacement value per asset in million EUR (assumed)
ASSET_VALUE_MEUR = {
    "wastewater_plant": 40.0,
    "water_works": 25.0,
    "pumping_station": 2.0,
    "substation_transmission": 12.0,
    "substation_distribution": 1.5,
    "power_plant": 20.0,
    "rail_station": 5.0,
    "bus_station": 3.0,
    "hospital": 15.0,
    "fuel_storage": 20.0,
}

# Depth-damage curve family per asset class: (depths in m, damage fraction of value). Assumed.
CURVES = {
    "buildings": ([0.0, 0.3, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0], [0.0, 0.08, 0.15, 0.27, 0.40, 0.52, 0.70, 0.85, 1.0]),
    "process_plant": ([0.0, 0.3, 1.0, 2.0, 3.0, 6.0], [0.0, 0.10, 0.30, 0.50, 0.65, 1.0]),
    "electrical": ([0.0, 0.2, 0.5, 1.0, 2.0, 6.0], [0.0, 0.15, 0.40, 0.65, 0.85, 1.0]),
}
CURVE_OF = {
    "wastewater_plant": "process_plant",
    "water_works": "process_plant",
    "pumping_station": "electrical",
    "substation_transmission": "electrical",
    "substation_distribution": "electrical",
    "power_plant": "process_plant",
    "rail_station": "buildings",
    "bus_station": "buildings",
    "hospital": "buildings",
    "fuel_storage": "process_plant",
}

RETURN_PERIODS = [10, 50, 100, 200, 500]
MAX_DEPTH_M = 6.0

# Adaptation measures: protected height in m (depth reduction) and capital cost as share of asset value (assumed)
MEASURES = {
    "none": {"height_m": 0.0, "cost_share": 0.0},
    "local_barrier_0.5m": {"height_m": 0.5, "cost_share": 0.03},
    "flood_wall_1.5m": {"height_m": 1.5, "cost_share": 0.08},
    "elevate_critical_equipment_3m": {"height_m": 3.0, "cost_share": 0.18},
}
DISCOUNT_RATE = 0.06
LIFETIME_YEARS = 30
OPEX_SHARE = 0.01  # annual operation and maintenance as share of capital cost (assumed)

# Scenarios (stress factors, assumptions, not projections)
SCENARIOS = {
    "baseline": {"flood_freq_factor": 1.0, "warming_k": 0.0},
    "moderate": {"flood_freq_factor": 1.3, "warming_k": 1.5},
    "high": {"flood_freq_factor": 2.0, "warming_k": 3.0},
}

# Heat: loss fraction of asset value per day with maximum temperature above the threshold (assumed)
HEAT_THRESHOLD_C = 35.0
HEAT_LOSS_PER_DAY = {
    "substation_transmission": 0.0004,
    "substation_distribution": 0.0004,
    "power_plant": 0.0003,
    "wastewater_plant": 0.0001,
    "water_works": 0.0001,
    "pumping_station": 0.0002,
    "rail_station": 0.0001,
    "bus_station": 0.0,
    "hospital": 0.0001,
    "fuel_storage": 0.0001,
}


def annuity_factor(rate: float = DISCOUNT_RATE, years: int = LIFETIME_YEARS) -> float:
    return rate / (1 - (1 + rate) ** (-years))


def damage_fraction(asset_class: str, depth: np.ndarray | float) -> np.ndarray:
    x, y = CURVES[CURVE_OF[asset_class]]
    return np.interp(np.clip(depth, 0, MAX_DEPTH_M), x, y)
