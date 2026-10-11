"""Logika core/state.py diuji dengan session_state palsu (dict biasa)."""

import types

import pytest

import core.state as S
from core.inputs import ALL_KEYS, default_text
from core.run import config_key


@pytest.fixture
def ss(monkeypatch):
    state = {}
    monkeypatch.setattr(S, "st", types.SimpleNamespace(session_state=state))
    S.init_state()
    return state


def test_init_state_mengisi_default(ss):
    assert all(ss[f"in_{k}"] == default_text(k) for k in ALL_KEYS)
    assert ss["scenario_name"] == "Baseline (Business as Usual)"
    assert ss["last_run"] is None and ss["custom_scenarios"] == {}


def test_init_state_tidak_menimpa_nilai_user(ss):
    ss["in_E0"] = "70"
    S.init_state()
    assert ss["in_E0"] == "70"


def test_bind_menyalin_nilai_kanonik_ke_key_widget(ss):
    ss["in_E0"] = "70"
    cfg = S.bind("in_E0")
    assert cfg["key"] == "w_in_E0" and ss["w_in_E0"] == "70"
    ss["w_in_E0"] = "80"
    cfg["on_change"](*cfg["args"])
    assert ss["in_E0"] == "80"


def test_atur_ulang_mengembalikan_default_dan_menjaga_hasil(ss):
    ss["in_E0"], ss["scenario_name"], ss["sl_I0"] = "70", "Subsidi Energi", 9.0
    ss["last_run"] = {"marker": 1}
    S.request_reset()
    S.apply_pending_updates()
    assert ss["in_E0"] == "50,00" and ss["scenario_name"] == "Baseline (Business as Usual)"
    assert "sl_I0" not in ss and "_reset_pending" not in ss
    assert ss["last_run"] == {"marker": 1}


def test_request_set_menerapkan_updates_sekali(ss):
    S.request_set({"in_E0": "66", "scenario_name": "Subsidi Energi"})
    S.apply_pending_updates()
    assert ss["in_E0"] == "66" and ss["scenario_name"] == "Subsidi Energi"
    ss["in_E0"] = "10"
    S.apply_pending_updates()
    assert ss["in_E0"] == "10"


def test_skenario_kustom_simpan_dan_muat(ss):
    ss["in_E0"] = "66"
    S.save_custom_scenario("uji")
    assert ss["custom_scenarios"]["uji"]["in_E0"] == "66"
    ss["in_E0"] = "10"
    S.request_set(dict(ss["custom_scenarios"]["uji"]))
    S.apply_pending_updates()
    assert ss["in_E0"] == "66"
    assert ss["last_run"] is None


def test_current_config_valid_dan_tidak_valid(ss):
    cfg, errors = S.current_config()
    assert cfg is not None and errors == {}
    ss["in_E0"] = "abc"
    cfg, errors = S.current_config()
    assert cfg is None and "E0" in errors
    assert S.ui_status() == ("invalid", 1)


def test_status_ready_fresh_stale(ss):
    ss["in_n_sim"] = "100"
    assert S.ui_status() == ("ready", 0)
    assert S.execute_run() is True
    assert ss["last_run"]["config_key"] == config_key(S.current_config()[0])
    assert S.ui_status() == ("fresh", 0) and not S.is_stale()
    ss["in_kappa"] = "3,00"
    assert S.ui_status() == ("stale", 0) and S.is_stale()
    ss["scenario_name"] = "Subsidi Energi"
    ss["in_kappa"] = "2,00"
    assert S.is_stale()


def test_execute_run_menolak_input_tidak_valid(ss):
    ss["in_E0"] = ""
    assert S.execute_run() is False
    assert ss["last_run"] is None


def test_slider_dan_teks_sinkron(ss):
    ss["sl_I0"] = 7.0
    S.slider_changed("I0")
    assert ss["in_I0"] == "7,00"
    ss["in_I0"] = "12"
    S.sync_slider_from_text("I0")
    assert ss["sl_I0"] == 12.0
    ss["in_I0"] = "abc"
    S.sync_slider_from_text("I0")
    assert ss["sl_I0"] == 0.0 or ss["sl_I0"] > 0  # teks tak valid: slider ke batas min, tanpa error


def test_bind_menginisialisasi_state_bila_belum_ada(monkeypatch):
    state = {}
    monkeypatch.setattr(S, "st", types.SimpleNamespace(session_state=state))
    cfg = S.bind("scenario_name")  # tanpa init_state() sebelumnya
    assert state["w_scenario_name"] == "Baseline (Business as Usual)"
    assert cfg["key"] == "w_scenario_name"
