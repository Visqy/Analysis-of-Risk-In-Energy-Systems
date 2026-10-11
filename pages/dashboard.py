"""Halaman Dashboard: ringkasan hasil utama.

Menampilkan Indeks Risiko (belum tersedia), VaR, CVaR, nilai akhir E(T), D(T),
P(T), total kerugian kumulatif, status sistem, dan skenario rekomendasi. Data
dari `last_run`; kosong bila simulasi belum dijalankan.
"""

import streamlit as st

from core.formatting import id_number
from core.recommendation import get_recommendation
from core.scenarios import VARIABLE_UNITS
from ui.components import require_run

st.header("Dashboard")

run = require_run()
if run is not None:
    cfg = run["config"]
    conf_txt = int(round(cfg["conf"] * 100))

    st.markdown("##### Ringkasan Hasil Utama")
    c1, c2, c3 = st.columns(3)
    c1.metric("Indeks Risiko", "Belum tersedia",
              help="Indeks risiko segera hadir pada versi berikutnya.")
    c2.metric(f"VaR {conf_txt}% ({VARIABLE_UNITS['L']})", id_number(run["var"]))
    c3.metric(f"CVaR {conf_txt}% ({VARIABLE_UNITS['L']})", id_number(run["cvar"]))
    c4, c5, c6 = st.columns(3)
    c4.metric(f"$E(T)$ ({VARIABLE_UNITS['E']})", id_number(run["E"][-1]))
    c5.metric(f"$D(T)$ ({VARIABLE_UNITS['D']})", id_number(run["D"][-1]))
    c6.metric(f"$P(T)$ ({VARIABLE_UNITS['P']})", id_number(run["P"][-1]))
    st.metric(f"Total Kerugian Kumulatif ({VARIABLE_UNITS['L']})", id_number(run["total_loss"]))

    st.markdown("##### Status Risiko")
    stab = run["stab"]
    if stab["status"] == "STABIL":
        st.success(f"Status sistem: {stab['status']}")
    elif "MARGINAL" in stab["status"]:
        st.warning(f"Status sistem: {stab['status']} — analisis kestabilan lokal berdasarkan linearisasi")
    else:
        st.error(f"Status sistem: {stab['status']}")

    st.markdown("##### Rekomendasi")
    top, beats_baseline = get_recommendation(run["ranking"])
    if beats_baseline:
        st.info(
            f"**{top['Skenario']}** — skenario dengan kerugian terendah berdasarkan model saat "
            f"ini ({id_number(top['loss'])} {VARIABLE_UNITS['L']}, turun {id_number(top['pct'])}% "
            f"dari baseline). Lihat halaman **Rekomendasi** untuk detail & batasannya."
        )
    else:
        st.info("Tidak ada skenario intervensi yang lebih baik dari baseline berdasarkan "
                "parameter saat ini. Lihat halaman **Rekomendasi** untuk detail.")
