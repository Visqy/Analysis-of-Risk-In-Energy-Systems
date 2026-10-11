"""Alarm bila rumus model berubah: angka acuan model riset awal dan contoh uji peringkat."""

import numpy as np
import pytest

from core.model import equilibrium_and_stability
from core.recommendation import compute_ranking, get_recommendation
from core.run import run_simulation
from core.scenarios import DEFAULT_PARAMS
from tests.conftest import make_config


def test_total_kerugian_baseline():
    assert run_simulation(make_config(n_sim=100))["total_loss"] == pytest.approx(221.64, abs=0.005)


def test_ranking_skenario():
    run = run_simulation(make_config(n_sim=100))
    losses = [round(r["loss"], 2) for r in run["ranking"]]
    assert losses == [122.35, 148.95, 149.88, 178.92, 221.64]
    assert [r["rank"] for r in run["ranking"]] == [1, 2, 3, 4, 5]
    top, beats = get_recommendation(run["ranking"])
    assert beats and top["Skenario"] == "Peningkatan Investasi Energi"
    assert round(top["delta"], 2) == 99.29 and round(top["pct"], 2) == 44.80


def test_var_cvar_metode_lama():
    """Normal lama, n=500, seed=42 = angka acuan model riset awal."""
    run = run_simulation(make_config(dist="normal", n_sim=500, seed=42))
    assert run["var"] == pytest.approx(519.22, abs=0.01)
    assert run["cvar"] == pytest.approx(730.27, abs=0.01)
    assert run["losses"].mean() == pytest.approx(268.61, abs=0.01)


def test_kestabilan_marginal():
    stab = equilibrium_and_stability(DEFAULT_PARAMS)
    p = DEFAULT_PARAMS
    assert stab["status"].startswith("MARGINAL")
    assert stab["osc_freq"] == pytest.approx(np.sqrt(p["beta"] * p["gamma"]))
    imag = sorted(stab["eigvals"], key=lambda z: z.imag)
    assert imag[0].imag == pytest.approx(-stab["osc_freq"])
    assert imag[-1].imag == pytest.approx(stab["osc_freq"])
    assert stab["E_star"] == pytest.approx(p["I0"] / p["delta"])
    assert stab["P_star"] == pytest.approx(p["alpha"] * p["G0"] / p["beta"])


def test_ranking_pakai_y0_dari_config():
    t = np.linspace(0, 15, 300)
    base = dict(DEFAULT_PARAMS)
    r_default, base_default = compute_ranking(base, t)
    r_lain, base_lain = compute_ranking(base, t, [80.0, 45.0, 20.0])
    assert base_lain != pytest.approx(base_default)
