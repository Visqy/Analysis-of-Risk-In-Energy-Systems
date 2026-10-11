"""Halaman Dinamika Sistem: grafik E(t), D(t), P(t), dan L(t).

Tiap grafik disertai interpretasi singkat, lalu kartu total kerugian kumulatif
serta nilai akhir E(T) dan D(T). Data dari `last_run`; kosong bila simulasi
belum dijalankan.
"""

import streamlit as st

from core.formatting import id_number
from core.interpretation import interpret_D, interpret_E, interpret_L, interpret_P
from core.scenarios import VARIABLE_UNITS
from ui.charts import COLORS, line_chart
from ui.components import require_run, unit_note

st.header("Dinamika Sistem Energi–Ekonomi")

run = require_run()
if run is not None:
    t, E, D, P, L = run["t"], run["E"], run["D"], run["P"], run["L"]
    unit_note()

    st.markdown("##### Kapasitas Energi $E(t)$")
    st.plotly_chart(line_chart(t, E, COLORS["E"], y_unit=VARIABLE_UNITS["E"]))
    st.caption(interpret_E(t, E))

    st.markdown("##### Permintaan Energi $D(t)$")
    st.plotly_chart(line_chart(t, D, COLORS["D"], y_unit=VARIABLE_UNITS["D"]))
    st.caption(interpret_D(t, D))

    st.markdown("##### Harga Energi $P(t)$")
    st.plotly_chart(line_chart(t, P, COLORS["P"], y_unit=VARIABLE_UNITS["P"]))
    st.caption(interpret_P(t, P))

    st.markdown("##### Kerugian Ekonomi $L(t)$")
    st.plotly_chart(line_chart(t, L, COLORS["L"], fill=True, y_unit=VARIABLE_UNITS["L"]))
    st.caption(interpret_L(t, E, D, L))

    c1, c2, c3 = st.columns(3)
    c1.metric(f"Total Kerugian Kumulatif ({VARIABLE_UNITS['L']})", id_number(run["total_loss"]))
    c2.metric(f"Kapasitas Akhir $E(T)$ ({VARIABLE_UNITS['E']})", id_number(E[-1]))
    c3.metric(f"Permintaan Akhir $D(T)$ ({VARIABLE_UNITS['D']})", id_number(D[-1]))
