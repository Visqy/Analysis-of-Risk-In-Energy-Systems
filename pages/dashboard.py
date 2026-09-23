import streamlit as st

from core.model import simulate, equilibrium_and_stability, trapz as _trapz
from core.recommendation import compute_ranking, get_recommendation
from core.scenarios import DEFAULT_Y0, VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number

st.header("Dashboard")

base_params, params, t = get_active_params()
st.markdown(f"Skenario aktif: **{st.session_state['scenario_name']}**")

E, D, P, L = simulate(params, DEFAULT_Y0, t)
total_loss = _trapz(L, t)
stab = equilibrium_and_stability(params)

st.markdown("##### Indikator Utama")
c1, c2, c3 = st.columns(3)
c1.metric(f"Total Kerugian Kumulatif ({VARIABLE_UNITS['L']})", id_number(total_loss))
c2.metric(f"Kapasitas Akhir E(T) ({VARIABLE_UNITS['E']})", id_number(E[-1]))
c3.metric(f"Permintaan Akhir D(T) ({VARIABLE_UNITS['D']})", id_number(D[-1]))

st.markdown("##### Status Risiko")
if stab["status"] == "STABIL":
    st.success(f"Status sistem: {stab['status']}")
elif "MARGINAL" in stab["status"]:
    st.warning(f"Status sistem: {stab['status']}")
else:
    st.error(f"Status sistem: {stab['status']}")

st.markdown("##### Rekomendasi")
rows, _ = compute_ranking(base_params, t)
top, beats_baseline = get_recommendation(rows)
if beats_baseline:
    st.info(
        f"**{top['Skenario']}** — skenario dengan kerugian terendah berdasarkan model saat "
        f"ini ({id_number(top['loss'])} {VARIABLE_UNITS['L']}, turun {id_number(top['pct'])}% "
        f"dari baseline). Lihat halaman **Rekomendasi** untuk detail & batasannya."
    )
else:
    st.info("Tidak ada skenario intervensi yang lebih baik dari baseline berdasarkan "
            "parameter saat ini. Lihat halaman **Rekomendasi** untuk detail.")
