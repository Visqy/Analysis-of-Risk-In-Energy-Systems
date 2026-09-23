import numpy as np
import pandas as pd
import streamlit as st

from core.model import monte_carlo_risk, risk_metrics, sensitivity_analysis
from core.scenarios import DEFAULT_Y0, VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number
from ui.charts import histogram_chart, tornado_chart

st.header("Analisis Risiko Ekonomi (Monte Carlo)")

s = st.session_state
_, params, t = get_active_params()

mc_inputs = {
    "scenario_name": s["scenario_name"], "T_end": s["T_end"], "n_sim": s["n_sim"],
    "conf": s["conf"], "delta_std": s["delta_std"], "gamma_std": s["gamma_std"],
    "I0_std": s["I0_std"], "params": params,
}

run_mc = st.button("▶ Jalankan Monte Carlo")
if run_mc:
    uncertain = {
        "delta": ("normal", params["delta"], s["delta_std"]),
        "gamma": ("normal", params["gamma"], s["gamma_std"]),
        "I0": ("normal", params["I0"], s["I0_std"]),
    }
    losses = monte_carlo_risk(params, DEFAULT_Y0, t, uncertain, n_sim=s["n_sim"])
    var, cvar = risk_metrics(losses, s["conf"])
    sens = sensitivity_analysis(params, DEFAULT_Y0, t,
                                 ["delta", "alpha", "beta", "gamma", "kappa", "I0", "g_rate"])
    st.session_state["mc_results"] = {
        "losses": losses, "var": var, "cvar": cvar, "sens": sens, "inputs": mc_inputs,
        "uncertain": uncertain,
    }

mc_results = st.session_state.get("mc_results")

if mc_results is None:
    st.info("Klik tombol **Jalankan Monte Carlo** di atas untuk menghitung VaR/CVaR "
            "dan sensitivity analysis.")
else:
    if mc_results["inputs"] != mc_inputs:
        st.caption("⚠️ Parameter berubah — klik ulang untuk memperbarui.")

    losses, var, cvar, sens = (mc_results["losses"], mc_results["var"],
                                mc_results["cvar"], mc_results["sens"])
    mc_conf = mc_results["inputs"]["conf"]
    mc_n_sim = mc_results["inputs"]["n_sim"]
    ci_low, ci_high = np.percentile(losses, [2.5, 97.5])

    st.markdown("##### 3.1 Pengaturan Simulasi")
    st.caption(f"Jumlah iterasi: {mc_n_sim}")
    uncertain_df = pd.DataFrame([
        {"Parameter": name, "Distribusi": "Normal",
         "Rata-rata (μ)": id_number(spec[1], 4), "Simpangan Baku (σ)": id_number(spec[2], 4)}
        for name, spec in mc_results["uncertain"].items()
    ])
    st.dataframe(uncertain_df, hide_index=True, use_container_width=True)

    st.markdown("##### 3.2 Statistik Distribusi Kerugian")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Rata-rata ({VARIABLE_UNITS['L']})", id_number(losses.mean()))
    c2.metric(f"Median ({VARIABLE_UNITS['L']})", id_number(np.median(losses)))
    c3.metric(f"Simpangan Baku ({VARIABLE_UNITS['L']})", id_number(losses.std()))
    c4, c5, c6 = st.columns(3)
    c4.metric(f"VaR {int(mc_conf*100)}% ({VARIABLE_UNITS['L']})", id_number(var))
    c5.metric(f"CVaR {int(mc_conf*100)}% ({VARIABLE_UNITS['L']})", id_number(cvar))
    c6.metric("Interval Kepercayaan 95%", f"{id_number(ci_low)} – {id_number(ci_high)}")

    st.markdown("##### 3.3 Distribusi Total Kerugian Ekonomi (Monte Carlo)")
    st.plotly_chart(histogram_chart(losses, var, mc_conf, unit=VARIABLE_UNITS["L"]),
                     use_container_width=True)

    st.markdown("##### 3.4 Sensitivitas Parameter (±20%)")
    st.plotly_chart(tornado_chart(sens, unit=VARIABLE_UNITS["L"]), use_container_width=True)
