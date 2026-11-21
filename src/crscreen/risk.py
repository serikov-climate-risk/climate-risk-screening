"""Expected annual loss from flood depths, heat days and adaptation measures; regret and value of information."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .parameters import (ASSET_VALUE_MEUR, HEAT_LOSS_PER_DAY, LIFETIME_YEARS, MEASURES, OPEX_SHARE, RETURN_PERIODS,
                         SCENARIOS, DISCOUNT_RATE, annuity_factor, damage_fraction)


def ead_fraction(asset_class: str, depths_by_rp: np.ndarray, freq_factor: float = 1.0, height_m: float = 0.0,
                 rps=RETURN_PERIODS) -> float:
    """Expected annual damage as a share of asset value.

    depths_by_rp: depths at the asset for the return periods in `rps` (ascending). A measure of height h
    lowers the depth acting on the asset by h. Exceedance probabilities are multiplied by `freq_factor`
    (scenario stress factor). Below the 1-in-10 flood the damage is set to zero (lower bound); the tail beyond
    the 1-in-500 flood carries the 1-in-500 damage (flat extension).
    """
    p = np.minimum(1.0, freq_factor / np.array(rps, dtype=float))
    d = np.maximum(0.0, np.asarray(depths_by_rp, dtype=float) - height_m)
    f = damage_fraction(asset_class, d)
    order = np.argsort(p)
    p, f = p[order], f[order]
    # integrate from probability 0 (flat extension of the 1-in-500 damage) to the most frequent mapped flood;
    # damage from floods more frequent than the 1-in-10 flood is set to zero (lower bound)
    pp = np.concatenate([[0.0], p])
    ff = np.concatenate([[f[0]], f])
    return float(np.trapezoid(ff, pp))


def annual_cost_fraction(cost_share: float) -> float:
    return cost_share * (annuity_factor() + OPEX_SHARE)


def asset_scenario_table(assets: pd.DataFrame, depth_cols: list[str], heat_days: dict[str, float]) -> pd.DataFrame:
    """Per asset, scenario and measure: flood EAL, heat EAL, annual measure cost, net benefit (MEUR per year)."""
    rows = []
    for idx, a in assets.iterrows():
        value = ASSET_VALUE_MEUR[a.asset_class]
        depths = a[depth_cols].to_numpy(dtype=float)
        for sname, s in SCENARIOS.items():
            heat_eal = value * HEAT_LOSS_PER_DAY[a.asset_class] * heat_days[sname]
            for mname, m in MEASURES.items():
                flood = value * ead_fraction(a.asset_class, depths, s["flood_freq_factor"], m["height_m"])
                cost = value * annual_cost_fraction(m["cost_share"])
                rows.append({"asset": idx, "scenario": sname, "measure": mname, "flood_eal": flood,
                             "heat_eal": heat_eal, "annual_cost": cost})
    t = pd.DataFrame(rows)
    base = t[t.measure == "none"].set_index(["asset", "scenario"]).flood_eal
    t["benefit"] = t.apply(lambda r: base[(r.asset, r.scenario)] - r.flood_eal, axis=1)
    t["net"] = t.benefit - t.annual_cost
    return t


def regret_plans(t: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Per asset: best measure per scenario, minimax-regret measure, and portfolio regret of each plan."""
    scen = list(SCENARIOS)
    piv = t.pivot_table(index=["asset", "measure"], columns="scenario", values="net")
    best = piv.groupby(level=0).max()
    regret = best.reindex(piv.index, level=0) - piv
    maxreg = regret.max(axis=1)
    robust = maxreg.groupby(level=0).idxmin().map(lambda x: x[1])
    plans = {f"opt_{s}": piv[s].groupby(level=0).idxmax().map(lambda x: x[1]) for s in scen}
    plans["minimax_regret"] = robust
    plans["none"] = pd.Series("none", index=robust.index)
    res = {}
    for pname, ser in plans.items():
        for s in scen:
            net = sum(piv.loc[(a, m), s] for a, m in ser.items())
            res[(pname, s)] = net
    summary = pd.DataFrame(res, index=["net"]).T["net"].unstack()
    reg = pd.DataFrame({s: best[s].sum() - summary[s] for s in scen})
    reg["max_regret"] = reg.max(axis=1)
    out = pd.DataFrame({"plan": plans}).T
    return reg, plans, summary


def evpi(t: pd.DataFrame) -> float:
    """Value of knowing the scenario (equal weights): E[best net per scenario] - best single plan on expected net, per year."""
    scen = list(SCENARIOS)
    piv = t.pivot_table(index=["asset", "measure"], columns="scenario", values="net")
    perfect = piv.groupby(level=0).max().sum().mean()
    expected = piv.mean(axis=1).groupby(level=0).max().sum()
    return float(perfect - expected)


def heat_days_per_year(tmax_c: np.ndarray, years: np.ndarray, shift_k: float, threshold: float) -> float:
    """Mean number of days per year with maximum temperature above the threshold after a uniform shift (delta method)."""
    n = np.sum((tmax_c + shift_k) > threshold)
    return float(n / len(np.unique(years)))
