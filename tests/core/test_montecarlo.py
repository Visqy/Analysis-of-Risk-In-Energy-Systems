import numpy as np
import pytest

from core.model import _truncated_normal, monte_carlo_risk, risk_metrics
from core.run import run_simulation
from tests.conftest import make_config


def test_seed_sama_hasil_identik():
    a = run_simulation(make_config(n_sim=100, seed=11))
    b = run_simulation(make_config(n_sim=100, seed=11))
    assert np.array_equal(a["losses"], b["losses"])
    assert a["var"] == b["var"] and a["cvar"] == b["cvar"]


def test_seed_beda_hasil_beda():
    a = run_simulation(make_config(n_sim=100, seed=11))
    b = run_simulation(make_config(n_sim=100, seed=12))
    assert not np.array_equal(a["losses"], b["losses"])


@pytest.mark.parametrize("mean,std,lo,hi", [(0.08, 0.02, 0.01, 0.5), (0.02, 0.5, 0.01, 0.5),
                                              (0.49, 0.2, 0.01, 0.5)])
def test_truncnormal_dalam_batas(mean, std, lo, hi):
    rng = np.random.default_rng(0)
    xs = [_truncated_normal(rng, mean, std, lo, hi) for _ in range(2000)]
    assert min(xs) >= lo and max(xs) <= hi


def test_truncnormal_std_nol_mengembalikan_mean():
    rng = np.random.default_rng(0)
    assert _truncated_normal(rng, 0.08, 0.0, 0.01, 0.5) == 0.08
    assert _truncated_normal(rng, 9.0, 0.0, 0.01, 0.5) == 0.5


def test_parameter_acak_tidak_pernah_nol(small_run):
    # delta tak pernah di bawah batas bawah sehingga I0/delta tidak meledak
    assert np.isfinite(small_run["losses"]).all()


def test_var_cvar_dan_kuantil(small_run):
    losses = small_run["losses"]
    assert small_run["var"] <= small_run["cvar"]
    lo, hi = np.percentile(losses, [2.5, 97.5])
    assert lo <= np.median(losses) <= hi
    assert len(losses) == 100


def test_risk_metrics_conf():
    losses = np.arange(1.0, 101.0)
    var, cvar = risk_metrics(losses, 0.95)
    assert var == pytest.approx(95.05)
    assert cvar == pytest.approx(98.0)


def test_monte_carlo_tanpa_ketidakpastian_konstan(small_run):
    base = small_run["active_params"]
    t = small_run["t"]
    losses = monte_carlo_risk(base, small_run["config"]["y0"], t, {}, n_sim=5, seed=1)
    assert np.allclose(losses, losses[0])
