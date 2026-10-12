"""Penjaga gaya interpretasi: Temuan–Makna–Implikasi, bersyarat, spesifik data."""

import re

import numpy as np
import pytest

from core.inputs import DISPLAY_NAME
from core.interpretation import (
    CATATAN_PROTOTIPE, interpret_capacity_demand, interpret_implications, interpret_loss,
    interpret_price, interpret_risk, interpret_tornado,
)
from tests.conftest import make_config

FORBIDDEN = ("harus ", "wajib", "disarankan", "sebaiknya", "pasti", "dijamin")
TMI = ("**Temuan:**", "**Makna:**", "**Implikasi:**")


def _texts(run):
    t, E, D, P, L = run["t"], run["E"], run["D"], run["P"], run["L"]
    return {
        "kapasitas_permintaan": interpret_capacity_demand(t, E, D),
        "harga": interpret_price(t, P, E, D),
        "kerugian": interpret_loss(t, E, D, L),
        "risiko": interpret_risk(run["losses"], run["var"], run["cvar"], 95),
    }


def test_tiga_bagian_berlabel_dan_bahasa_bersyarat(small_run):
    for name, text in _texts(small_run).items():
        assert all(label in text for label in TMI), name
        implikasi = text.split("**Implikasi:**")[1]
        assert any(k in implikasi for k in ("dipertimbangkan", "dapat digunakan")), name
        for phrase in FORBIDDEN:
            assert phrase not in text.lower(), f"{name}: {phrase!r}"


def test_butir_implikasi_bersyarat(small_run):
    run = small_run
    items = interpret_implications(run["t"], run["E"], run["D"], run["P"], run["L"])
    assert items
    for item in items:
        assert "dipertimbangkan" in item
        assert not any(p in item.lower() for p in FORBIDDEN)


def test_angka_berformat_indonesia(small_run):
    for name, text in _texts(small_run).items():
        assert not re.search(r"\d\.\d", text), f"{name}: desimal bertitik"
    assert not re.search(r"\d\.\d", interpret_tornado(small_run["sens"], DISPLAY_NAME))


def test_interpretasi_berbeda_untuk_hasil_berbeda(small_run):
    from core.run import run_simulation
    lain = run_simulation(make_config(n_sim=100, I0="12", kappa="3"))
    a, b = _texts(small_run), _texts(lain)
    assert a["kapasitas_permintaan"] != b["kapasitas_permintaan"]
    assert a["kerugian"] != b["kerugian"]


def test_cerita_baseline_sesuai_data(small_run):
    texts = _texts(small_run)
    assert "tahun ke-2,3 sampai tahun ke-13,8" in texts["kapasitas_permintaan"]
    assert "minimum 18,12 pada tahun ke-2,1" in texts["harga"]
    assert "memuncak 31,46 pada tahun ke-7,7" in texts["kerugian"]
    assert "VaR 95%" in texts["risiko"]


def test_catatan_prototipe_tetap():
    assert "hasil simulasi prototipe" in CATATAN_PROTOTIPE
    assert "belum dapat diperlakukan sebagai rekomendasi kebijakan nyata" in CATATAN_PROTOTIPE
    assert "validasi menggunakan data empiris" in CATATAN_PROTOTIPE
