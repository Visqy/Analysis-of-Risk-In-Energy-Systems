import copy

from core.run import MODEL_VERSION, config_key, run_simulation
from tests.conftest import make_config

KEYS = {"config", "config_key", "meta", "t", "E", "D", "P", "L", "total_loss",
        "active_params", "base_params", "stab", "uncertain", "losses", "var", "cvar",
        "sens", "ranking", "baseline_loss"}


def test_snapshot_lengkap(small_run):
    assert KEYS <= set(small_run)
    assert len(small_run["t"]) == len(small_run["E"]) == 300
    assert len(small_run["ranking"]) == 5
    assert small_run["config_key"] == config_key(small_run["config"])


def test_metadata(small_run):
    cfg = small_run["config"]
    assert small_run["meta"]["model_version"] == MODEL_VERSION == "ARIES v0.1"
    assert len(small_run["meta"]["date"]) == 19  # ISO tanpa mikrodetik
    assert cfg["seed"] == 2026 and cfg["n_sim"] == 100
    assert cfg["dist"] == "truncnormal"
    assert cfg["source"]["status"] == "Ilustratif/Asumsi"


def test_config_key_deterministik_dan_sensitif():
    a, b = make_config(), make_config()
    assert config_key(a) == config_key(b)
    assert config_key(make_config(E0="60,5")) != config_key(a)
    assert config_key(make_config(scenario="Subsidi Energi")) != config_key(a)
    assert config_key(make_config(dist="normal")) != config_key(a)
    c = copy.deepcopy(a)
    c["params"]["kappa"] = 3.0
    assert config_key(c) != config_key(a)
    d = copy.deepcopy(a)
    d["source"] = {"status": "Data Aktual", "name": "PLN", "year": "2024"}
    assert config_key(d) != config_key(a)


def test_skenario_intervensi_mengubah_parameter_aktif():
    run = run_simulation(make_config(scenario="Peningkatan Investasi Energi", n_sim=100))
    assert run["active_params"]["I_ramp"] == 0.8 and run["base_params"]["I_ramp"] == 0.0
    assert run["total_loss"] < 221.64


def test_y0_dari_config_dipakai():
    run = run_simulation(make_config(E0="80", n_sim=100))
    assert run["E"][0] == 80.0
