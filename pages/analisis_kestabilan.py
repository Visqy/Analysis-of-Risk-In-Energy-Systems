"""Halaman Analisis Kestabilan.

Menampilkan titik ekuilibrium (E*, D*, P*), matriks Jacobian di titik itu,
eigenvalue (bagian real dan imajiner), frekuensi dan periode osilasi, toleransi
numerik, status sistem, dan simulasi gangguan kecil di sekitar ekuilibrium.
Hasil berupa analisis kestabilan lokal berdasarkan linearisasi. Data dari
`last_run["stab"]`; sebelum simulasi dijalankan halaman menampilkan keadaan kosong.
"""

import numpy as np
import pandas as pd
import streamlit as st

from core.formatting import id_number
from core.interpretation import interpret_perturbation
from core.model import simulate
from core.scenarios import VARIABLE_UNITS
from ui.charts import COLORS, line_chart
from ui.components import require_run

st.header("Analisis Kestabilan")
st.caption("Hasil merupakan **analisis kestabilan lokal berdasarkan linearisasi**.")

run = require_run()
if run is not None:
    stab = run["stab"]
    params = run["active_params"]
    t = run["t"]
    y0 = run["config"]["y0"]

    st.markdown("##### Titik Ekuilibrium")
    e1, e2, e3 = st.columns(3)
    e1.metric(f"$E^*$ ({VARIABLE_UNITS['E']})", id_number(stab["E_star"], 3))
    e2.metric(f"$D^*$ ({VARIABLE_UNITS['D']})", id_number(stab["D_star"], 3))
    e3.metric(f"$P^*$ ({VARIABLE_UNITS['P']})", id_number(stab["P_star"], 3))

    st.markdown("##### Matriks Jacobian")
    st.caption("Dievaluasi di titik ekuilibrium (E*, D*, P*) — asumsi I(t)=I0, G(t)=G0 konstan.")
    J = stab["jacobian"]
    st.latex(
        r"J(E^*, D^*, P^*) = \begin{bmatrix}"
        f"{id_number(J[0, 0])} & {id_number(J[0, 1])} & {id_number(J[0, 2])} \\\\ "
        f"{id_number(J[1, 0])} & {id_number(J[1, 1])} & {id_number(J[1, 2])} \\\\ "
        f"{id_number(J[2, 0])} & {id_number(J[2, 1])} & {id_number(J[2, 2])}"
        r"\end{bmatrix}"
    )

    st.markdown("##### Eigenvalue Jacobian")
    st.dataframe(pd.DataFrame({
        "λ": [f"λ{i+1}" for i in range(len(stab["eigvals"]))],
        "Re(λ) (1/tahun)": [id_number(ev.real, 4) for ev in stab["eigvals"]],
        "Im(λ) (1/tahun)": [f"{id_number(ev.imag, 4)}i" for ev in stab["eigvals"]],
    }), hide_index=True)

    st.markdown("##### Frekuensi & Periode Osilasi (D–P)")
    if stab["osc_freq"] > 0:
        st.latex(r"\omega = \sqrt{\beta \gamma} \qquad\qquad T = \dfrac{2\pi}{\omega}")
        f1, f2 = st.columns(2)
        f1.metric(r"$\omega$ (1/tahun)", id_number(stab["osc_freq"], 4))
        f2.metric(r"$T$ (tahun)", id_number(2 * np.pi / stab["osc_freq"]))

    st.markdown("##### Toleransi Numerik")
    st.caption(
        "Bagian real eigenvalue dengan |Re(λ)| ≤ 1×10⁻⁹ dianggap nol (batas presisi numerik "
        "komputasi). Eigenvalue dengan Re(λ)=0 (imajiner murni) diklasifikasikan sebagai kondisi "
        "marginal — bukan stabil maupun tidak stabil secara ketat."
    )

    st.markdown("##### Status Sistem")
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
        st.markdown("##### Simulasi Gangguan Kecil di Sekitar Ekuilibrium")
        st.caption(
            "Simulasi tambahan dengan I(t)=I0 dan G(t)=G0 konstan (asumsi ekuilibrium), "
            "diberi gangguan kecil pada D dan P dari titik ekuilibrium."
        )
        const_params = dict(params)
        const_params.update({"I_ramp": 0.0, "g_rate": 0.0, "I_step_t": None, "I_step_val": 0.0})
        eps = 0.05 * max(stab["E_star"], 1.0)
        y0_pert = [stab["E_star"], stab["D_star"] + eps, stab["P_star"] + eps]
        _, D_pert, P_pert, _ = simulate(const_params, y0_pert, t)

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(line_chart(t, D_pert, COLORS["D"], y_unit=VARIABLE_UNITS["D"]))
            st.caption("D(t) di sekitar D* setelah gangguan kecil")
        with c2:
            st.plotly_chart(line_chart(t, P_pert, COLORS["P"], y_unit=VARIABLE_UNITS["P"]))
            st.caption("P(t) di sekitar P* setelah gangguan kecil")
        st.caption(interpret_perturbation(
            t, D_pert, P_pert, stab["D_star"], stab["P_star"], const_params["beta"],
            const_params["gamma"], stab["osc_freq"]))
