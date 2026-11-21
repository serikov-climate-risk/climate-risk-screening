import numpy as np
import pytest

from crscreen import risk, tagging
from crscreen.parameters import MEASURES, RETURN_PERIODS, annuity_factor, damage_fraction


def test_dry_asset_has_no_loss():
    assert risk.ead_fraction("hospital", np.zeros(5)) == 0.0


def test_damage_curve_monotone_and_capped():
    d = np.linspace(0, 12, 50)
    for cls in ("hospital", "substation_transmission", "water_works"):
        f = damage_fraction(cls, d)
        assert np.all(np.diff(f) >= -1e-12)
        assert f[-1] == pytest.approx(1.0)


def test_ead_known_value():
    # constant damage fraction 1 at all mapped depths (depth 6 m): integral from 0 to 0.1 equals 0.1
    depths = np.full(5, 6.0)
    assert risk.ead_fraction("hospital", depths) == pytest.approx(0.1)


def test_ead_increases_with_frequency_factor_and_falls_with_height():
    depths = np.array([0.5, 1.0, 1.5, 2.0, 2.5])
    base = risk.ead_fraction("hospital", depths)
    assert risk.ead_fraction("hospital", depths, freq_factor=2.0) > base
    assert risk.ead_fraction("hospital", depths, height_m=1.5) < base
    assert risk.ead_fraction("hospital", depths, height_m=10.0) == 0.0


def test_annuity_factor():
    assert annuity_factor(0.06, 30) == pytest.approx(0.0726489, rel=1e-4)


def test_heat_days():
    t = np.array([30.0, 36.0, 40.0, 34.0])
    y = np.array([2000, 2000, 2001, 2001])
    assert risk.heat_days_per_year(t, y, 0.0, 35.0) == 1.0
    assert risk.heat_days_per_year(t, y, 2.0, 35.0) == 1.5


def test_tagging_rules():
    row = dict(asset=1, asset_class="substation_transmission", measure="flood_wall_1.5m", height_m=1.5,
               capex_meur=1.0, depth_rp100=1.2, depth_rp500=2.0, ead_share_base=0.01)
    assert tagging.tag_measure(row)["tagged_capex_meur"] == 1.0
    row["depth_rp100"] = 2.0  # measure lower than the 1-in-100 depth: partial link, not tagged
    assert tagging.tag_measure(row)["tagged_capex_meur"] == 0.0
    row.update(depth_rp100=0.0, depth_rp500=0.0)  # not exposed
    assert "no context-specific vulnerability" in tagging.tag_measure(row)["decision"]


def test_paris_screen():
    assert tagging.paris_screen(0.0001, 0.0001, "none").startswith("aligned")
    assert tagging.paris_screen(0.01, 0.0001, "flood_wall_1.5m").startswith("aligned if")
    assert tagging.paris_screen(0.01, 0.01, "none").startswith("not aligned")


def test_regret_and_evpi_small_example():
    import pandas as pd
    rows = []
    for sc, ben in {"baseline": 1.0, "moderate": 1.5, "high": 3.0}.items():
        rows.append(dict(asset=0, scenario=sc, measure="none", net=0.0))
        rows.append(dict(asset=0, scenario=sc, measure="local_barrier_0.5m", net=ben - 1.2))
    t = pd.DataFrame(rows)
    reg, plans, summary = risk.regret_plans(t)
    assert plans["opt_high"][0] == "local_barrier_0.5m"
    assert plans["opt_baseline"][0] == "none"
    assert risk.evpi(t) >= 0
