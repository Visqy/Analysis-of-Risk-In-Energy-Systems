"""Halaman Dashboard: ringkasan hasil utama.

Menampilkan VaR, CVaR, total kerugian kumulatif, nilai akhir E(T), D(T), P(T),
dan ringkasan peringkat skenario. Data dari `last_run`; kosong bila simulasi
belum dijalankan.
"""

import streamlit as st

from core.formatting import id_number
from core.recommendation import get_recommendation
from core.scenarios import VARIABLE_UNITS
from ui.components import metric_unit, prototype_note, require_run

st.header("Dashboard")

run = require_run()
if run is not None:
    cfg = run["config"]
    conf_txt = int(round(cfg["conf"] * 100))

    st.markdown("##### Ringkasan Hasil Utama")
    c1, c2, c3 = st.columns(3)
    metric_unit(c1, "Total Kerugian Kumulatif", id_number(run["total_loss"]), VARIABLE_UNITS["L"])
    metric_unit(c2, f"VaR {conf_txt}%", id_number(run["var"]), VARIABLE_UNITS["L"])
    metric_unit(c3, f"CVaR {conf_txt}%", id_number(run["cvar"]), VARIABLE_UNITS["L"])
    c4, c5, c6 = st.columns(3)
    metric_unit(c4, "Kapasitas Akhir $E(T)$", id_number(run["E"][-1]), VARIABLE_UNITS["E"])
    metric_unit(c5, "Permintaan Akhir $D(T)$", id_number(run["D"][-1]), VARIABLE_UNITS["D"])
    metric_unit(c6, "Harga Akhir $P(T)$", id_number(run["P"][-1]), VARIABLE_UNITS["P"])

    st.markdown("##### Peringkat Skenario")
    top, beats_baseline = get_recommendation(run["ranking"])
    if beats_baseline:
        st.info(
            f"**{top['Skenario']}** — skenario dengan kerugian terendah berdasarkan model saat "
            f"ini ({id_number(top['loss'])} {VARIABLE_UNITS['L']}, turun {id_number(top['pct'])}% "
            f"dari baseline). Lihat halaman **Peringkat Skenario** untuk detail dan batasannya."
        )
    else:
        st.info("Tidak ada skenario intervensi yang lebih baik dari baseline berdasarkan "
                "parameter saat ini. Lihat halaman **Peringkat Skenario** untuk detail.")

    prototype_note()
