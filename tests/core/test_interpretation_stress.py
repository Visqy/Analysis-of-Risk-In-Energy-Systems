"""Stress test interpretasi: kombinasi parameter di tepi rentang dan kasus tepi sintetis."""

import re

import numpy as np
import pytest

from core.inputs import FIELD_SPECS, PARAM_KEYS, fmt_input
from core.interpretation import (
    interpret_capacity_demand, interpret_implications, interpret_loss, interpret_price,
    interpret_risk,
)
from core.run import run_simulation
from core.scenarios import SCENARIOS
from tests.conftest import make_config

pytestmark = pytest.mark.slow

TMI = ("**Temuan:**", "**Makna:**", "**Implikasi:**")


def _cfg_edge(which, T_end, scenario):
    """Config dengan semua parameter model di batas `which` ("min"/"max"/"mix"); T_end horizon."""
    over = {"n_sim": 100, "T_end": T_end}
    for i, k in enumerate(PARAM_KEYS):
        sp = FIELD_SPECS[k]
        pick = which if which != "mix" else ("min" if i % 2 == 0 else "max")
        over[k] = fmt_input(sp[pick], sp["dec"])
    return make_config(scenario=scenario, **over)


def _all_texts(run):
    t, E, D, P, L = run["t"], run["E"], run["D"], run["P"], run["L"]
    texts = [
        interpret_capacity_demand(t, E, D),
        interpret_price(t, P, E, D),
        interpret_loss(t, E, D, L),
        interpret_risk(run["losses"], run["var"], run["cvar"], 95),
    ]
    return texts, interpret_implications(t, E, D, P, L)


def _check(texts, items, horizon):
    for text in texts:
        assert all(label in text for label in TMI), text
        assert not re.search(r"\bnan\b|\binf\b", text.lower()), text
        for part in text.split("**")[2::2]:
            assert part.strip(" :").strip(), text
        for y in re.findall(r"tahun ke-(\d+(?:,\d+)?)", text):
            assert 0 <= float(y.replace(",", ".")) <= horizon + 1e-9, (y, text)
    for it in items:
        assert not re.search(r"\bnan\b|\binf\b", it.lower()), it
        for y in re.findall(r"tahun ke-(\d+(?:,\d+)?)", it):
            assert 0 <= float(y.replace(",", ".")) <= horizon + 1e-9, (y, it)


@pytest.mark.parametrize("which", ["min", "max", "mix"])
@pytest.mark.parametrize("T_end", [5, 60])
def test_tepi_rentang_semua_interpretasi_wajar(which, T_end):
    scenario = list(SCENARIOS)[(len(which) + T_end) % len(SCENARIOS)]
    run = run_simulation(_cfg_edge(which, T_end, scenario))
    texts, items = _all_texts(run)
    _check(texts, items, T_end)


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_semua_skenario_bawaan(scenario):
    run = run_simulation(make_config(scenario=scenario, n_sim=100))
    texts, items = _all_texts(run)
    _check(texts, items, run["config"]["T_end"])


def _grid(n=61, T=15.0):
    return np.linspace(0.0, T, n)


def test_kurva_datar_dan_nol():
    t = _grid()
    z = np.zeros_like(t)
    flat = np.full_like(t, 50.0)
    texts = [interpret_capacity_demand(t, flat, flat), interpret_price(t, flat, flat, flat),
             interpret_loss(t, flat, flat, z)]
    items = interpret_implications(t, flat, flat, flat, z)
    _check(texts, items, 15)
    assert "tidak melampaui" in texts[0]


def test_nilai_sangat_besar_dan_kecil_tetap_berformat():
    t = _grid()
    E = np.full_like(t, 1e-9)
    D = np.full_like(t, 1e9)
    L = D - E
    texts = [interpret_capacity_demand(t, E, D), interpret_loss(t, E, D, L)]
    items = interpret_implications(t, E, D, D, L)
    _check(texts, items, 15)


def test_satu_titik_waktu_tidak_error():
    t = np.array([0.0])
    y = np.array([10.0])
    texts = [interpret_capacity_demand(t, y, y + 5), interpret_loss(t, y, y + 5, np.array([5.0]))]
    _check(texts, interpret_implications(t, y, y + 5, y, np.array([5.0])), 0)


def test_kerugian_nol_di_semua_periode_dan_defisit_di_akhir_saja():
    t = _grid()
    E = np.full_like(t, 50.0)
    D = np.where(t > 14, 80.0, 40.0)
    L = np.where(t > 14, 30.0, 0.0)
    texts = [interpret_capacity_demand(t, E, D), interpret_loss(t, E, D, L)]
    _check(texts, interpret_implications(t, E, D, D, L), 15)
    assert "sampai tahun ke-15" in texts[0]
