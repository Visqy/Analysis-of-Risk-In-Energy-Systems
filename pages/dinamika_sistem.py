import streamlit as st

from core.model import simulate, trapz as _trapz
from core.scenarios import DEFAULT_Y0, VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number
from core.interpretation import interpret_E, interpret_D, interpret_P, interpret_L
from ui.charts import line_chart, COLORS

st.header("Dinamika Sistem Energi–Ekonomi")

base_params, params, t = get_active_params()
st.markdown(f"Skenario aktif: **{st.session_state['scenario_name']}**")

E, D, P, L = simulate(params, DEFAULT_Y0, t)
total_loss = _trapz(L, t)

st.markdown("##### 1.1 Kapasitas Energi E(t)")
st.plotly_chart(line_chart(t, E, COLORS["E"], y_unit=VARIABLE_UNITS["E"]), use_container_width=True)
st.caption(interpret_E(t, E))

st.markdown("##### 1.2 Permintaan Energi D(t)")
st.plotly_chart(line_chart(t, D, COLORS["D"], y_unit=VARIABLE_UNITS["D"]), use_container_width=True)
st.caption(interpret_D(t, D))

st.markdown("##### 1.3 Harga Energi P(t)")
st.plotly_chart(line_chart(t, P, COLORS["P"], y_unit=VARIABLE_UNITS["P"]), use_container_width=True)
st.caption(interpret_P(t, P))

st.markdown("##### 1.4 Kerugian Ekonomi L(t)")
st.plotly_chart(line_chart(t, L, COLORS["L"], fill=True, y_unit=VARIABLE_UNITS["L"]),
                 use_container_width=True)
st.caption(interpret_L(t, E, D, L))

c1, c2, c3 = st.columns(3)
c1.metric(f"Total Kerugian Kumulatif ({VARIABLE_UNITS['L']})", id_number(total_loss))
c2.metric(f"Kapasitas Akhir E(T) ({VARIABLE_UNITS['E']})", id_number(E[-1]))
c3.metric(f"Permintaan Akhir D(T) ({VARIABLE_UNITS['D']})", id_number(D[-1]))
