"""Peringkat berdasarkan risiko (CVaR) untuk semua skenario."""

import numpy as np
import pytest

from core.interpretation import interpret_ranking_basis
from core.run import run_simulation
from core.scenarios import BASELINE_NAME, SCENARIOS
from tests.conftest import make_config


def test_semua_skenario_diurutkan_menurut_cvar(small_run):
    rows = small_run["ranking_risk"]
    assert {r["Skenario"] for r in rows} == set(SCENARIOS)
    cvars = [r["cvar"] for r in rows]
    assert cvars == sorted(cvars)
    assert [r["rank"] for r in rows] == [1, 2, 3, 4, 5]
    assert all(r["var"] <= r["cvar"] for r in rows)


def test_skenario_aktif_identik_dengan_hasil_utama():
    for nama in (BASELINE_NAME, "Subsidi Energi"):
        run = run_simulation(make_config(scenario=nama, n_sim=100))
        aktif = next(r for r in run["ranking_risk"] if r["Skenario"] == nama)
        assert aktif["cvar"] == pytest.approx(run["cvar"])
        assert aktif["var"] == pytest.approx(run["var"])


def test_penurunan_cvar_terhadap_baseline(small_run):
    rows = {r["Skenario"]: r for r in small_run["ranking_risk"]}
    base = rows[BASELINE_NAME]
    assert base["cvar_pct"] == pytest.approx(0.0) and base["cvar_delta"] == pytest.approx(0.0)
    assert small_run["baseline_cvar"] == pytest.approx(base["cvar"])
    for r in rows.values():
        assert r["cvar_delta"] == pytest.approx(base["cvar"] - r["cvar"])


def test_reproduksibel_dengan_seed_sama():
    a = run_simulation(make_config(n_sim=100, seed=5))["ranking_risk"]
    b = run_simulation(make_config(n_sim=100, seed=5))["ranking_risk"]
    assert [(r["Skenario"], r["cvar"]) for r in a] == [(r["Skenario"], r["cvar"]) for r in b]


def test_interpretasi_urutan_berbeda_dan_sama():
    loss = [{"Skenario": "A", "loss": 100.0, "delta": 20.0, "pct": 16.67},
            {"Skenario": "Base", "loss": 120.0, "delta": 0.0, "pct": 0.0}]
    beda = [{"Skenario": "Base", "cvar": 200.0}, {"Skenario": "A", "cvar": 300.0}]
    teks = interpret_ranking_basis(loss, beda, 95, "Base")
    assert "A merupakan skenario dengan kerugian terendah berdasarkan model saat ini" in teks
    assert "Berdasarkan risiko, Base terendah" in teks and "CVaR 95% 200,00 dibanding 300,00" in teks
    sama = [{"Skenario": "A", "cvar": 150.0}, {"Skenario": "Base", "cvar": 250.0}]
    teks2 = interpret_ranking_basis(loss, sama, 95, "Base")
    assert "juga memiliki risiko terendah" in teks2 and "analisis biaya" in teks2
    base_best = [{"Skenario": "Base", "loss": 100.0, "delta": 0.0, "pct": 0.0},
                 {"Skenario": "A", "loss": 120.0, "delta": -20.0, "pct": -20.0}]
    teks3 = interpret_ranking_basis(base_best, sama[::-1], 95, "Base")
    assert "Tidak terdapat skenario intervensi yang lebih baik daripada baseline" in teks3
