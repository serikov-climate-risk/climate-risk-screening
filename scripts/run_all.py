"""Run the whole screening: hazard sampling, scenarios, measures, regret, tagging, Paris screen, figures."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from crscreen import risk, tagging
from crscreen.assets import load_assets
from crscreen.heat import load_tmax
from crscreen.hazard import depth_table
from crscreen.parameters import ASSET_VALUE_MEUR, HEAT_THRESHOLD_C, MEASURES, RETURN_PERIODS, SCENARIOS

QC_DEPTH_RP10 = 2.0
RES = ROOT / "results"
RES.mkdir(exist_ok=True)

g = load_assets()
d = depth_table(g)
assets = pd.concat([g.drop(columns="geometry"), d], axis=1)
assets["value_meur"] = assets.asset_class.map(ASSET_VALUE_MEUR)
# The dataset README warns about large depths in channels; assets whose own cell is deep already at 1-in-10 are
# in or on the bank of a channel that the 90 m grid cannot resolve. They are kept in the table but excluded from
# the loss totals, plans and tagging, and listed for site review.
assets["qc_in_channel_flag"] = assets.depth_rp10 >= QC_DEPTH_RP10
depth_cols = [f"depth_rp{rp}" for rp in RETURN_PERIODS]
assets[assets.qc_in_channel_flag].to_csv(RES / "site_review_in_channel.csv", index=False)
flagged = assets[assets.qc_in_channel_flag]
assets_all = assets
assets = assets[~assets.qc_in_channel_flag].copy()

tmax, years = load_tmax()
heat_days = {s: risk.heat_days_per_year(tmax, years, v["warming_k"], HEAT_THRESHOLD_C) for s, v in SCENARIOS.items()}

t = risk.asset_scenario_table(assets, depth_cols, heat_days)
reg, plans, summary = risk.regret_plans(t)
vi = risk.evpi(t)

base = t[t.measure == "none"].pivot_table(index="asset", columns="scenario", values=["flood_eal", "heat_eal"])
assets["flood_eal_baseline_meur"] = base[("flood_eal", "baseline")]
assets["flood_eal_high_meur"] = base[("flood_eal", "high")]
assets["heat_eal_baseline_meur"] = base[("heat_eal", "baseline")]
assets["heat_eal_high_meur"] = base[("heat_eal", "high")]
assets["ead_share_base"] = assets.flood_eal_baseline_meur / assets.value_meur
assets["robust_measure"] = pd.Series(plans["minimax_regret"])
assets.to_csv(RES / "asset_risk.csv", index=False)

rows = []
for idx, a in assets.iterrows():
    m = a.robust_measure
    h = MEASURES[m]["height_m"]
    capex = a.value_meur * MEASURES[m]["cost_share"]
    resid = risk.ead_fraction(a.asset_class, a[depth_cols].to_numpy(float), 1.0, h)
    r = tagging.tag_measure({"asset": idx, "asset_class": a.asset_class, "measure": m, "height_m": h,
                             "capex_meur": capex, "depth_rp100": a.depth_rp100, "depth_rp500": a.depth_rp500,
                             "ead_share_base": a.ead_share_base})
    r["name"] = a["name"]
    r["residual_share"] = resid
    r["paris_screen"] = tagging.paris_screen(a.ead_share_base, resid, m)
    rows.append(r)
tags = pd.DataFrame(rows)
tags.to_csv(RES / "tagging_and_paris_screen.csv", index=False)
reg.to_csv(RES / "plan_regret.csv")
summary.to_csv(RES / "plan_net_benefit.csv")

sens = []
for f in [1.0, 1.3, 1.6, 2.0, 2.5, 3.0]:
    tot = sum(a.value_meur * risk.ead_fraction(a.asset_class, a[depth_cols].to_numpy(float), f) for _, a in assets.iterrows())
    sens.append({"flood_freq_factor": f, "portfolio_flood_eal_meur": tot})
pd.DataFrame(sens).to_csv(RES / "sensitivity_flood_frequency.csv", index=False)

by_class = assets.groupby("asset_class").agg(
    n=("name", "size"), value_meur=("value_meur", "sum"),
    flood_eal_baseline=("flood_eal_baseline_meur", "sum"), flood_eal_high=("flood_eal_high_meur", "sum"),
    heat_eal_baseline=("heat_eal_baseline_meur", "sum"), heat_eal_high=("heat_eal_high_meur", "sum"))
by_class.to_csv(RES / "risk_by_class.csv")

out = {
    "n_assets": int(len(assets)),
    "total_value_meur": float(assets.value_meur.sum()),
    "heat_days_per_year": heat_days,
    "flood_eal_meur": {s: float(t[(t.measure == "none") & (t.scenario == s)].flood_eal.sum()) for s in SCENARIOS},
    "heat_eal_meur": {s: float(t[(t.measure == "none") & (t.scenario == s)].heat_eal.sum()) for s in SCENARIOS},
    "n_exposed_rp100": int((assets.depth_rp100 >= tagging.EXPOSED_DEPTH_RP100).sum()),
    "n_excluded_in_channel": int(len(flagged)),
    "plan_counts": {k: v.value_counts().to_dict() for k, v in plans.items()},
    "plan_net_benefit_meur_per_year": summary.round(3).to_dict(),
    "max_regret_meur_per_year": reg.max_regret.round(3).to_dict(),
    "evpi_meur_per_year": vi,
    "capex_robust_plan_meur": float(tags.capex_meur.sum()),
    "tagged_adaptation_capex_meur": float(tags.tagged_capex_meur.sum()),
    "paris_screen_counts": tags.paris_screen.str.split(":").str[0].value_counts().to_dict(),
}
(RES / "summary.json").write_text(json.dumps(out, indent=2, default=float), encoding="utf-8")
print(json.dumps(out, indent=2, default=float))

fig, ax = plt.subplots(figsize=(6, 4))
by_class[["flood_eal_baseline", "flood_eal_high"]].sort_values("flood_eal_baseline").plot.barh(ax=ax)
ax.set_xlabel("Expected annual flood loss, million EUR (assumed values)")
ax.set_title("Flood loss by asset class", fontsize=10)
fig.tight_layout(); fig.savefig(RES / "fig_flood_eal_by_class.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(5.5, 5))
sc = ax.scatter(assets.lon, assets.lat, c=assets.depth_rp100.clip(0, 4), cmap="Blues",
                s=10 + 25 * (assets.depth_rp100 > 0.1), edgecolor="grey", linewidth=0.3)
plt.colorbar(sc, label="1-in-100 flood depth at asset, m (capped at 4)")
ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude"); ax.set_title("Assets and 1-in-100 flood depth (JRC maps)")
fig.tight_layout(); fig.savefig(RES / "fig_asset_map.png", dpi=150); plt.close(fig)

fig, ax = plt.subplots(figsize=(5.5, 3.6))
reg.max_regret.sort_values().plot.barh(ax=ax)
ax.set_xlabel("Maximum regret over scenarios, million EUR per year")
ax.set_title("Regret of adaptation plans")
fig.tight_layout(); fig.savefig(RES / "fig_plan_regret.png", dpi=150); plt.close(fig)
