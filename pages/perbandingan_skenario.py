"""Halaman Perbandingan Skenario.

Menampilkan kurva L(t) per skenario, total kerugian kumulatif per skenario, dan
ringkasan tabel. Pilihan "Skenario yang ditampilkan" hanya memfilter tampilan;
seluruh skenario sudah dihitung saat simulasi dijalankan. Data dari `last_run`
(parameter dasar, kondisi awal, grid waktu, kerugian baseline).
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.formatting import id_number
from core.interpretation import interpret_comparison
from core.model import simulate, trapz
from core.scenarios import BASELINE_NAME, SCENARIOS, VARIABLE_UNITS
from core.state import bind
from ui.charts import CHART_HEIGHT, CHART_MARGIN, COLORS, SCENARIO_COLORS, line_chart, localize
from ui.components import interpretation_card, metric_unit, prototype_note, require_run

st.header("Perbandingan Skenario Kebijakan")

run = require_run()
if run is not None:
    base = run["base_params"]
    y0 = run["config"]["y0"]
    t = run["t"]

    st.multiselect("Skenario yang ditampilkan", list(SCENARIOS.keys()),
                   **bind("selected_scenarios"),
                   help="Hanya memilih tampilan; seluruh skenario sudah dihitung saat Jalankan.")
    selected = st.session_state["selected_scenarios"]

    if not selected:
        st.info("Pilih minimal satu skenario untuk ditampilkan.")
    elif len(selected) == 1:
        name = selected[0]
        p = dict(base); p.update(SCENARIOS[name])
        _, _, _, L_i = simulate(p, y0, t)
        st.markdown(f"Skenario terpilih: **{name}**")
        st.markdown("##### Kerugian Ekonomi $L(t)$")
        st.plotly_chart(line_chart(t, L_i, COLORS["L"], fill=True, y_unit=VARIABLE_UNITS["L"]))
        metric_unit(st, "Total Kerugian Kumulatif", id_number(trapz(L_i, t)), VARIABLE_UNITS["L"])
        st.caption("Pilih 2+ skenario untuk grafik perbandingan.")
    else:
        names, losses, curves = [], [], {}
        fig_cmp = go.Figure()
        for name in selected:
            p = dict(base); p.update(SCENARIOS[name])
            _, _, _, L_i = simulate(p, y0, t)
            color = SCENARIO_COLORS[list(SCENARIOS).index(name) % len(SCENARIO_COLORS)]
            fig_cmp.add_trace(go.Scatter(x=t, y=L_i, mode="lines", name=name,
                                         line=dict(color=color)))
            names.append(name); losses.append(trapz(L_i, t)); curves[name] = L_i

        st.markdown("##### Kerugian Ekonomi $L(t)$ per Skenario")
        fig_cmp.update_layout(xaxis_title="t (tahun)", yaxis_title=VARIABLE_UNITS["L"],
                              height=CHART_HEIGHT, margin=CHART_MARGIN,
                              legend=dict(font=dict(size=12)))
        localize(fig_cmp, x_hover=".1f", y_hover=".2f")
        st.plotly_chart(fig_cmp)
        interpretation_card(interpret_comparison(
            names, losses, curves, t, run["baseline_loss"], BASELINE_NAME))

        st.markdown("##### Total Kerugian Ekonomi Kumulatif")
        fig_bar = go.Figure(go.Bar(x=names, y=losses, marker_color="#F4A261"))
        fig_bar.update_layout(height=CHART_HEIGHT, margin=CHART_MARGIN,
                              yaxis_title=VARIABLE_UNITS["L"], xaxis=dict(tickfont=dict(size=9)))
        localize(fig_bar, y_hover=".2f")
        st.plotly_chart(fig_bar)

        st.markdown("**Ringkasan Total Kerugian**")
        st.dataframe(pd.DataFrame({"Skenario": names,
                                   f"Total Kerugian ({VARIABLE_UNITS['L']})":
                                       [id_number(v) for v in losses]}),
                     hide_index=True)

    prototype_note()
