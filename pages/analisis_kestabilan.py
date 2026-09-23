import numpy as np
import pandas as pd
import streamlit as st

from core.model import equilibrium_and_stability, simulate
from core.scenarios import VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number
from ui.charts import line_chart, COLORS

st.header("Analisis Kestabilan")

_, params, t = get_active_params()
stab = equilibrium_and_stability(params)

st.markdown("##### 2.1 Titik Ekuilibrium")
e1, e2, e3 = st.columns(3)
e1.metric(f"E* ({VARIABLE_UNITS['E']})", id_number(stab["E_star"], 3))
e2.metric(f"D* ({VARIABLE_UNITS['D']})", id_number(stab["D_star"], 3))
e3.metric(f"P* ({VARIABLE_UNITS['P']})", id_number(stab["P_star"], 3))

st.markdown("##### 2.2 Matriks Jacobian")
st.caption("Dievaluasi di titik ekuilibrium (E*, D*, P*) — asumsi I(t)=I0, G(t)=G0 konstan.")
J = stab["jacobian"]
st.latex(
    r"J(E^*, D^*, P^*) = \begin{bmatrix}"
    f"{id_number(J[0, 0])} & {id_number(J[0, 1])} & {id_number(J[0, 2])} \\\\ "
    f"{id_number(J[1, 0])} & {id_number(J[1, 1])} & {id_number(J[1, 2])} \\\\ "
    f"{id_number(J[2, 0])} & {id_number(J[2, 1])} & {id_number(J[2, 2])}"
    r"\end{bmatrix}"
)

st.markdown("##### 2.3 Eigenvalue Jacobian")
eig_df = pd.DataFrame({
    "λ": [f"λ{i+1}" for i in range(len(stab["eigvals"]))],
    "Re(λ) (1/tahun)": [id_number(ev.real, 4) for ev in stab["eigvals"]],
    "Im(λ) (1/tahun)": [f"{id_number(ev.imag, 4)}i" for ev in stab["eigvals"]],
})
st.dataframe(eig_df, hide_index=True, use_container_width=True)

st.markdown("##### 2.4 Frekuensi & Periode Osilasi (D–P)")
if stab["osc_freq"] > 0:
    st.latex(r"\omega = \sqrt{\beta \gamma} \qquad\qquad T = \dfrac{2\pi}{\omega}")
    f1, f2 = st.columns(2)
    f1.metric("ω (1/tahun)", id_number(stab["osc_freq"], 4))
    f2.metric("T (tahun)", id_number(2 * np.pi / stab["osc_freq"]))

st.markdown("##### 2.5 Toleransi Numerik")
st.caption(
    "Bagian real eigenvalue dengan |Re(λ)| ≤ 1×10⁻⁹ dianggap nol (batas presisi numerik "
    "komputasi). Eigenvalue dengan Re(λ)=0 (imajiner murni) diklasifikasikan sebagai kondisi "
    "marginal — bukan stabil maupun tidak stabil secara ketat."
)

st.markdown("##### 2.6 Status Sistem")
if stab["status"] == "STABIL":
    st.success(f"Status sistem: {stab['status']}")
elif "MARGINAL" in stab["status"]:
    st.warning(f"Status sistem: {stab['status']}")
    st.caption(
        "Berdasarkan linearisasi lokal, sistem menunjukkan perilaku marginal dengan satu "
        "pasangan eigenvalue imajiner murni. Kesimpulan ini berlaku pada sistem terlinearisasi "
        "dan belum menjadi bukti kestabilan global model nonlinear."
    )
else:
    st.error(f"Status sistem: {stab['status']}")

if stab["osc_freq"] > 0:
    st.markdown("##### 2.7 Simulasi Gangguan Kecil di Sekitar Ekuilibrium")
    st.caption(
        "Simulasi tambahan (I(t)=I0, G(t)=G0 konstan, sesuai asumsi ekuilibrium) untuk "
        "menunjukkan perilaku sistem saat diberi gangguan kecil dari titik ekuilibrium — "
        "osilasi D(t) & P(t) tidak meluruh maupun membesar, konsisten dengan status marginal."
    )
    const_params = dict(params)
    const_params.update({"I_ramp": 0.0, "g_rate": 0.0, "I_step_t": None, "I_step_val": 0.0})
    eps = 0.05 * max(stab["E_star"], 1.0)
    y0_pert = [stab["E_star"] + eps, stab["D_star"] + eps, stab["P_star"] + eps]
    _, D_pert, P_pert, _ = simulate(const_params, y0_pert, t)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(line_chart(t, D_pert, COLORS["D"], y_unit=VARIABLE_UNITS["D"]),
                         use_container_width=True)
        st.caption("D(t) di sekitar D* setelah gangguan kecil")
    with c2:
        st.plotly_chart(line_chart(t, P_pert, COLORS["P"], y_unit=VARIABLE_UNITS["P"]),
                         use_container_width=True)
        st.caption("P(t) di sekitar P* setelah gangguan kecil")
