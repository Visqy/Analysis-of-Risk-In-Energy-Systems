"""Session state ARIES: input, hasil simulasi, dan skenario kustom.

Alur: input (teks mentah per field, key `in_<field>`) -> validasi -> Jalankan
Simulasi -> `last_run` (snapshot hasil). Halaman hasil hanya membaca
`last_run`; mengubah input tidak menghitung ulang apa pun, hanya membuat hasil
berstatus "usang" (`ui_status`).

Kunci state:
    in_<field>, scenario_name, source_*  nilai kanonik input
    w_<nama>      key widget (disalin dari kunci kanonik lewat `bind`)
    last_run      snapshot hasil (`core.run.run_simulation`) atau None
    custom_scenarios, selected_scenarios, quick_mode

Mengapa dua lapis key: Streamlit membuang state widget yang tidak dirender di
halaman aktif, sehingga nilai disimpan di kunci non-widget dan widget memakai
key `w_*`. Widget ber-key juga tidak boleh ditulis setelah dibuat dalam satu
run, jadi reset/impor/muat skenario memakai pola pending (pasang flag, rerun,
diterapkan di awal script lewat `apply_pending_updates`).
"""

import streamlit as st

from core.inputs import (
    ALL_KEYS, FIELD_SPECS, default_text, fmt_input, parse_field, validate_all,
    build_config,
)
from core.run import config_key, run_simulation
from core.scenarios import SCENARIOS

DEFAULT_SCENARIO = list(SCENARIOS.keys())[0]
DEFAULT_DIST = "truncnormal"

# Key state non-field yang ikut disimpan di skenario kustom.
EXTRA_KEYS = ["scenario_name", "source_status", "source_name", "source_year"]


def _defaults():
    d = {f"in_{k}": default_text(k) for k in ALL_KEYS}
    d.update({
        "scenario_name": DEFAULT_SCENARIO,
        "source_status": "Ilustratif/Asumsi",
        "source_name": "",
        "source_year": "",
    })
    return d


def init_state():
    """Isi nilai bawaan untuk semua kunci state yang belum ada (idempoten)."""
    for key, value in _defaults().items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("quick_mode", False)
    st.session_state.setdefault("custom_scenarios", {})
    st.session_state.setdefault("last_run", None)
    st.session_state.setdefault("selected_scenarios", list(SCENARIOS.keys()))


def _sync(name):
    st.session_state[name] = st.session_state[f"w_{name}"]


def bind(name):
    """Kunci widget untuk state kanonik `name`. Streamlit membuang state widget
    yang tidak dirender di halaman aktif, jadi nilai kanonik disimpan di key
    non-widget dan disalin ke key widget `w_<name>` sebelum widget dibuat.
    Pakai: key=bind(n), on_change=_sync, args=(n,) lewat `bound(n)`."""
    if name not in st.session_state:  # halaman terpanggil sebelum app.py (mis. sambung ulang)
        init_state()
    st.session_state[f"w_{name}"] = st.session_state[name]
    return {"key": f"w_{name}", "on_change": _sync, "args": (name,)}


def request_reset():
    """Minta pengembalian semua input ke nilai bawaan pada run berikutnya."""
    st.session_state["_reset_pending"] = True


def request_set(updates):
    """Minta penerapan `updates` (dict kunci-state -> nilai) pada run berikutnya.

    Dipakai impor xlsx dan muat skenario kustom; hasil simulasi tidak berubah.
    """
    st.session_state["_pending_updates"] = updates


def _clear_sliders():
    for k in ALL_KEYS:
        st.session_state.pop(f"sl_{k}", None)


def apply_pending_updates():
    """Terapkan reset/pembaruan yang diminta; panggil di awal script, sebelum widget dibuat."""
    if st.session_state.pop("_reset_pending", False):
        for key, value in _defaults().items():
            st.session_state[key] = value
        _clear_sliders()
    updates = st.session_state.pop("_pending_updates", None)
    if updates:
        for key, value in updates.items():
            st.session_state[key] = value
        _clear_sliders()


def raw_inputs():
    """Teks mentah semua field input (key field -> teks), belum divalidasi."""
    return {k: st.session_state.get(f"in_{k}") for k in ALL_KEYS}


def current_config():
    """Validasi input sekarang dan susun konfigurasi run.

    Returns:
        (cfg, {}) bila semua valid; (None, errors) bila ada input tidak valid,
        dengan `errors` berupa dict field -> pesan.
    """
    values, errors = validate_all(raw_inputs())
    if errors:
        return None, errors
    s = st.session_state
    source = {"status": s["source_status"], "name": s["source_name"].strip(),
              "year": s["source_year"].strip()}
    cfg = build_config(values, s["scenario_name"], DEFAULT_DIST, source)
    return cfg, {}


def get_run():
    """Snapshot hasil simulasi terakhir, atau None bila belum pernah dijalankan."""
    return st.session_state.get("last_run")


def is_stale():
    """True bila input sekarang berbeda dari konfigurasi hasil terakhir."""
    run = get_run()
    if run is None:
        return False
    cfg, _ = current_config()
    return cfg is None or config_key(cfg) != run["config_key"]


def ui_status():
    """Status tampilan: ('invalid'|'ready'|'fresh'|'stale', jumlah_error).

    invalid = ada input salah; ready = valid tetapi belum dijalankan;
    fresh = hasil sesuai input; stale = input berubah sejak hasil terakhir.
    """
    cfg, errors = current_config()
    if errors:
        return "invalid", len(errors)
    run = get_run()
    if run is None:
        return "ready", 0
    return ("fresh" if config_key(cfg) == run["config_key"] else "stale"), 0


def execute_run():
    """Jalankan simulasi dengan input sekarang dan simpan ke `last_run`.

    Returns:
        True bila dijalankan; False bila ada input tidak valid (tidak ada
        yang dihitung).
    """
    cfg, errors = current_config()
    if errors:
        return False
    st.session_state["last_run"] = run_simulation(cfg)
    return True


def save_custom_scenario(name):
    """Simpan snapshot seluruh input sekarang sebagai skenario kustom `name` (hanya sesi ini)."""
    snap = {f"in_{k}": st.session_state[f"in_{k}"] for k in ALL_KEYS}
    snap.update({k: st.session_state[k] for k in EXTRA_KEYS})
    st.session_state["custom_scenarios"][name] = snap


# ---- sinkronisasi slider <-> kotak angka (Mode Eksplorasi Cepat) ----

def slider_changed(key):
    """Callback slider: salin nilai slider `sl_<key>` ke kotak angka `in_<key>`."""
    sp = FIELD_SPECS[key]
    st.session_state[f"in_{key}"] = fmt_input(st.session_state[f"sl_{key}"], sp["dec"])


def sync_slider_from_text(key):
    """Posisikan slider `sl_<key>` sesuai kotak angka; panggil sebelum slider dibuat.

    Teks tidak valid menempatkan slider di batas minimum tanpa error.
    """
    sp = FIELD_SPECS[key]
    v, err = parse_field(key, st.session_state.get(f"in_{key}"))
    val = float(v) if err is None else float(sp["min"])
    if st.session_state.get(f"sl_{key}") != val:
        st.session_state[f"sl_{key}"] = val
