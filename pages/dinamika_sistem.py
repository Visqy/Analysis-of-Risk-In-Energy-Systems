"""Halaman Dinamika Sistem: kapasitas dan permintaan, harga, dan kerugian ekonomi.

Bagian "Ringkasan" di atas memuat kartu total kerugian serta nilai akhir E(T)
dan D(T), lalu "Implikasi bagi Pengambil Keputusan". Di bawahnya tiga grafik
(kapasitas dan permintaan, harga P(t), kerugian L(t)) masing-masing dengan
interpretasi Temuan–Makna–Implikasi dalam satu card.
Data dari `last_run`; kosong bila simulasi belum dijalankan.
"""

import streamlit as st

from core.formatting import id_number
from core.interpretation import (
    interpret_capacity_demand, interpret_implications, interpret_loss, interpret_price,
)
from core.scenarios import VARIABLE_UNITS
from ui.charts import COLORS, line_chart, multi_line_chart
from ui.components import interpretation_card, metric_unit, prototype_note, require_run

st.header("Dinamika Sistem Energi–Ekonomi")

run = require_run()
if run is not None:
    t, E, D, P, L = run["t"], run["E"], run["D"], run["P"], run["L"]

    st.markdown("##### Ringkasan")
    c1, c2, c3 = st.columns(3)
    metric_unit(c1, "Total Kerugian Kumulatif", id_number(run["total_loss"]), VARIABLE_UNITS["L"])
    metric_unit(c2, "Kapasitas Akhir $E(T)$", id_number(E[-1]), VARIABLE_UNITS["E"])
    metric_unit(c3, "Permintaan Akhir $D(T)$", id_number(D[-1]), VARIABLE_UNITS["D"])

    st.markdown("##### Implikasi bagi Pengambil Keputusan")
    for item in interpret_implications(t, E, D, P, L):
        st.markdown(f"- {item}")

    st.markdown("##### Kapasitas $E(t)$ dan Permintaan Energi $D(t)$")
    st.plotly_chart(multi_line_chart(
        t, [("Kapasitas E(t)", E, COLORS["E"]), ("Permintaan D(t)", D, COLORS["D"])],
        y_unit=VARIABLE_UNITS["E"]))
    interpretation_card(interpret_capacity_demand(t, E, D))

    st.markdown("##### Harga Energi $P(t)$")
    st.plotly_chart(line_chart(t, P, COLORS["P"], y_unit=VARIABLE_UNITS["P"]))
    interpretation_card(interpret_price(t, P, E, D))

    st.markdown("##### Kerugian Ekonomi $L(t)$")
    st.plotly_chart(line_chart(t, L, COLORS["L"], fill=True, y_unit=VARIABLE_UNITS["L"]))
    interpretation_card(interpret_loss(t, E, D, L))

    prototype_note()
