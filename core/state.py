"""Session-state defaults untuk parameter sidebar (shared di semua halaman)."""

import numpy as np
import streamlit as st

from core.scenarios import DEFAULT_PARAMS, SCENARIOS

DEFAULTS = {
    "scenario_name": list(SCENARIOS.keys())[0],
    "I0": DEFAULT_PARAMS["I0"],
    "delta": DEFAULT_PARAMS["delta"],
    "alpha": DEFAULT_PARAMS["alpha"],
    "beta": DEFAULT_PARAMS["beta"],
    "gamma": DEFAULT_PARAMS["gamma"],
    "G0": DEFAULT_PARAMS["G0"],
    "g_rate": DEFAULT_PARAMS["g_rate"],
    "kappa": DEFAULT_PARAMS["kappa"],
    "T_end": 15,
    "n_sim": 500,
    "conf": 0.95,
    "delta_std": 0.02,
    "gamma_std": 0.10,
    "I0_std": 1.50,
    "selected_scenarios": list(SCENARIOS.keys()),
}


def init_state():
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def request_reset():
    """Tandai reset tertunda — jangan langsung menulis ke session_state di
    sini karena widget-nya mungkin sudah ter-instansiasi di run ini."""
    st.session_state["_reset_pending"] = True


def request_import(values):
    """Tandai nilai parameter hasil impor xlsx (sudah divalidasi) untuk
    diterapkan di run berikutnya — pola sama seperti request_reset()."""
    st.session_state["_pending_import"] = values


def apply_pending_reset():
    """Panggil di awal script (sebelum widget manapun dibuat) untuk
    menerapkan reset (request_reset()) dan/atau impor parameter
    (request_import()) yang tertunda."""
    if st.session_state.pop("_reset_pending", False):
        for key, value in DEFAULTS.items():
            st.session_state[key] = value
        st.session_state.pop("mc_results", None)

    pending_import = st.session_state.pop("_pending_import", None)
    if pending_import:
        for key, value in pending_import.items():
            st.session_state[key] = value
        st.session_state.pop("mc_results", None)


def get_active_params():
    """Rakit base_params (sidebar only), params (base + skenario aktif), dan
    array waktu t dari nilai sidebar saat ini di st.session_state."""
    s = st.session_state
    base_params = dict(DEFAULT_PARAMS)
    base_params.update({
        "I0": s["I0"], "delta": s["delta"], "alpha": s["alpha"], "beta": s["beta"],
        "gamma": s["gamma"], "G0": s["G0"], "g_rate": s["g_rate"], "kappa": s["kappa"],
    })
    params = dict(base_params)
    params.update(SCENARIOS[s["scenario_name"]])
    t = np.linspace(0, s["T_end"], 300)
    return base_params, params, t
