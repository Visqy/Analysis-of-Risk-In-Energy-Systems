"""Penjaga gaya interpretasi: deskriptif (bercerita tentang data), bukan saran."""

import re

import numpy as np
import pytest

from core.inputs import DISPLAY_NAME
from core.interpretation import (
    interpret_D, interpret_E, interpret_histogram, interpret_L, interpret_P,
    interpret_perturbation, interpret_tornado,
)
from core.model import simulate

FORBIDDEN = ("perlu ", "sebaiknya", "misalnya lewat", "diprioritaskan", "diantisipasi",
             "pengambil keputusan", "disarankan", "harus ", "tidak kembali")


def _all_texts(run):
    t = run["t"]
    st = run["stab"]
    p = dict(run["active_params"])
    p.update({"I_ramp": 0.0, "g_rate": 0.0, "I_step_t": None, "I_step_val": 0.0})
    eps = 0.05 * st["E_star"]
    _, D, P, _ = simulate(p, [st["E_star"], st["D_star"] + eps, st["P_star"] + eps], t)
    return {
        "E": interpret_E(t, run["E"]), "D": interpret_D(t, run["D"]),
        "P": interpret_P(t, run["P"]), "L": interpret_L(t, run["E"], run["D"], run["L"]),
        "hist": interpret_histogram(run["losses"], run["var"], run["cvar"], 95),
        "tornado": interpret_tornado(run["sens"], DISPLAY_NAME),
        "perturb": interpret_perturbation(t, D, P, st["D_star"], st["P_star"], p["beta"],
                                          p["gamma"], st["osc_freq"]),
    }


def test_tanpa_frasa_saran_dan_maksimal_dua_kalimat(small_run):
    for name, text in _all_texts(small_run).items():
        low = text.lower()
        for phrase in FORBIDDEN:
            assert phrase not in low, f"{name}: {phrase!r}"
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
        assert 1 <= len(sentences) <= 2, f"{name}: {len(sentences)} kalimat"


def test_angka_berformat_indonesia(small_run):
    for name, text in _all_texts(small_run).items():
        assert not re.search(r"\d\.\d", text), f"{name}: desimal bertitik"


def test_gangguan_kecil_data_asli_tidak_meluruh_maupun_membesar(small_run):
    assert "tidak meluruh maupun membesar" in _all_texts(small_run)["perturb"]


def test_cerita_baseline_sesuai_data(small_run):
    texts = _all_texts(small_run)
    assert "naik dari 50,00 menjadi 58,74" in texts["E"]
    assert "puncak 71,58 pada tahun ke-8,1" in texts["D"]
    assert "minimum 18,12 pada tahun ke-2,1" in texts["P"]
    assert "memuncak 31,46 pada tahun ke-7,7" in texts["L"]
    assert texts["tornado"].split(": ")[1].startswith("β")
