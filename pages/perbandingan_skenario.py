import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core.model import simulate, trapz as _trapz
from core.scenarios import DEFAULT_Y0, SCENARIOS, VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number
from ui.charts import line_chart, CHART_HEIGHT, CHART_MARGIN, COLORS

st.header("Perbandingan Skenario Kebijakan")

base_params, _, t = get_active_params()
selected_scenarios = st.session_state["selected_scenarios"]

if not selected_scenarios:
    st.info("Pilih minimal satu skenario di sidebar untuk membandingkan.")
elif len(selected_scenarios) == 1:
    name = selected_scenarios[0]
    p = dict(base_params); p.update(SCENARIOS[name])
    _, _, _, L_i = simulate(p, DEFAULT_Y0, t)
    loss_i = _trapz(L_i, t)

    st.markdown(f"Skenario terpilih: **{name}**")
    st.markdown("##### 4.1 Kerugian Ekonomi L(t)")
    st.plotly_chart(line_chart(t, L_i, COLORS["L"], fill=True, y_unit=VARIABLE_UNITS["L"]),
                     use_container_width=True)
    st.metric(f"Total Kerugian Kumulatif ({VARIABLE_UNITS['L']})", id_number(loss_i))
    st.caption("Pilih 2+ skenario untuk grafik perbandingan.")
else:
    bar_names, bar_losses = [], []
    fig_cmp = go.Figure()
    for name in selected_scenarios:
        p = dict(base_params); p.update(SCENARIOS[name])
        _, _, _, L_i = simulate(p, DEFAULT_Y0, t)
        fig_cmp.add_trace(go.Scatter(x=t, y=L_i, mode="lines", name=name))
        bar_names.append(name); bar_losses.append(_trapz(L_i, t))

    st.markdown("##### 4.1 Kerugian Ekonomi L(t) per Skenario")
    fig_cmp.update_layout(xaxis_title="t (tahun)", yaxis_title=VARIABLE_UNITS["L"],
                           height=CHART_HEIGHT, margin=CHART_MARGIN,
                           legend=dict(font=dict(size=12)))
    st.plotly_chart(fig_cmp, use_container_width=True)

    st.markdown("##### 4.2 Total Kerugian Ekonomi Kumulatif")
    fig_bar = go.Figure(go.Bar(x=bar_names, y=bar_losses, marker_color="#F4A261"))
    fig_bar.update_layout(height=CHART_HEIGHT, margin=CHART_MARGIN,
                           yaxis_title=VARIABLE_UNITS["L"],
                           xaxis=dict(tickfont=dict(size=9)))
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("**Ringkasan Total Kerugian**")
    st.dataframe(pd.DataFrame({"Skenario": bar_names,
                                f"Total Kerugian ({VARIABLE_UNITS['L']})":
                                    [id_number(v) for v in bar_losses]}),
                 hide_index=True, use_container_width=True)
