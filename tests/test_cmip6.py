import numpy as np
from crscreen import cmip6


def test_constant_delta_is_a_uniform_shift():
    era5 = np.random.default_rng(0).normal(20, 8, 3000)
    out = cmip6.apply_delta(era5, np.full_like(cmip6.P_GRID, 2.0))
    assert np.allclose(out - era5, 2.0)


def test_upper_tail_delta_moves_hot_days_more():
    rng = np.random.default_rng(1)
    h = rng.normal(20, 8, 20000)
    f = h * 1.1 - 2.0 + 2.0      # variance grows: hot days warm more than cold days
    d = cmip6.quantile_delta(h, f)
    assert d[-5] > d[5]
