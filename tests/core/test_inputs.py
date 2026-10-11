import pytest

from core.inputs import (
    ALL_KEYS, FIELD_SPECS, build_config, default_text, parse_field, validate_all,
)
from tests.conftest import make_config


def test_kosong_ditolak():
    assert parse_field("E0", "")[1] == "Wajib diisi"
    assert parse_field("E0", "   ")[1] == "Wajib diisi"
    assert parse_field("E0", None)[1] == "Wajib diisi"


@pytest.mark.parametrize("raw", ["abc", "1,2,3", "1e3", "--5", "5x"])
def test_bukan_angka(raw):
    assert parse_field("E0", raw)[1] == "Harus berupa angka"


def test_negatif():
    assert parse_field("E0", "-1")[1] == "Tidak boleh negatif"


@pytest.mark.parametrize("key", ["E0", "delta", "alpha", "beta", "kappa", "n_sim", "conf"])
def test_di_luar_rentang(key):
    sp = FIELD_SPECS[key]
    assert "Di luar rentang" in parse_field(key, str(sp["max"] + 1))[1]
    if sp["min"] > 0:
        assert "Di luar rentang" in parse_field(key, str(sp["min"] / 2))[1]


@pytest.mark.parametrize("key", list(FIELD_SPECS))
def test_batas_min_max_diterima(key):
    sp = FIELD_SPECS[key]
    assert parse_field(key, str(sp["min"]))[1] is None
    assert parse_field(key, str(sp["max"]))[1] is None


def test_koma_sama_dengan_titik():
    assert parse_field("delta", "0,08") == parse_field("delta", "0.08") == (0.08, None)


@pytest.mark.parametrize("key", ["seed", "n_sim", "T_end", "conf"])
def test_bilangan_bulat_menolak_desimal(key):
    assert parse_field(key, "10,5")[1] == "Harus bilangan bulat"


def test_nilai_bawaan_valid_semua():
    values, errors = validate_all({k: default_text(k) for k in ALL_KEYS})
    assert errors == {}
    assert set(values) == set(ALL_KEYS)


def test_validate_all_mengumpulkan_banyak_error():
    raw = {k: default_text(k) for k in ALL_KEYS}
    raw["E0"], raw["kappa"] = "abc", ""
    _, errors = validate_all(raw)
    assert set(errors) == {"E0", "kappa"}


def test_build_config():
    cfg = make_config(conf=90, seed=7)
    assert cfg["conf"] == pytest.approx(0.90)
    assert cfg["seed"] == 7
    assert set(cfg["sd"]) == {"delta", "gamma", "I0"}
    assert cfg["source"] == {"status": "Ilustratif/Asumsi", "name": "", "year": ""}
    assert cfg["y0"] == [50.0, 45.0, 20.0]
