"""Halaman Analisis Risiko (Monte Carlo).

Bagian utama: VaR, CVaR, total kerugian, dan histogram distribusi kerugian
dengan interpretasi. Detail (pengaturan simulasi dan parameter yang diacak,
statistik lengkap, interval kuantil 95%, diagram tornado sensitivitas) berada
di bagian "Detail analisis Monte Carlo" yang dapat dibuka. Data dari
`last_run`; kosong bila simulasi belum dijalankan.
"""

import numpy as np
import pandas as pd
import streamlit as st

from core.formatting import id_number
from core.inputs import DIST_OPTIONS, DISPLAY_NAME
from core.interpretation import interpret_risk, interpret_tornado
from core.scenarios import PARAM_META, VARIABLE_UNITS
from ui.charts import histogram_chart, tornado_chart
from ui.components import interpretation_card, kpi_cards, prototype_note, require_run

st.header("Analisis Risiko Ekonomi (Monte Carlo)")

run = require_run()
if run is not None:
    cfg = run["config"]
    losses, var, cvar = run["losses"], run["var"], run["cvar"]
    conf_pct = int(round(cfg["conf"] * 100))
    q_low, q_high = np.percentile(losses, [2.5, 97.5])

    kpi_cards([
        ("Total kerugian kumulatif", id_number(run["total_loss"]), VARIABLE_UNITS["L"], None),
        (f"VaR {conf_pct}%", id_number(var), VARIABLE_UNITS["L"], None),
        (f"CVaR {conf_pct}%", id_number(cvar), VARIABLE_UNITS["L"], None),
    ])

    st.markdown("##### Distribusi Total Kerugian Ekonomi (Monte Carlo)")
    st.plotly_chart(histogram_chart(losses, var, cfg["conf"], unit=VARIABLE_UNITS["L"]))
    interpretation_card(interpret_risk(losses, var, cvar, conf_pct))

    with st.expander("Detail analisis Monte Carlo"):
        st.markdown("##### Pengaturan Simulasi")
        st.caption(f"Distribusi ketidakpastian: {DIST_OPTIONS[cfg['dist']]}")
        rows = []
        for name, spec in run["uncertain"].items():
            bounds = (f"{id_number(spec[3], 3)} – {id_number(spec[4], 3)}"
                      if spec[0] == "truncnormal" else "≥ 1e-6")
            rows.append({
                "Parameter": f"{DISPLAY_NAME.get(name, name)} — "
                             f"{PARAM_META[name]['label'].split('(')[-1].rstrip(')')}",
                "μ": id_number(spec[1], 4), "σ": id_number(spec[2], 4), "Rentang": bounds})
        st.dataframe(pd.DataFrame(rows), hide_index=True)

        st.markdown("##### Statistik Distribusi Kerugian")
        kpi_cards([
            ("Rata-rata", id_number(losses.mean()), VARIABLE_UNITS["L"], None),
            ("Median", id_number(np.median(losses)), VARIABLE_UNITS["L"], None),
            ("Simpangan baku", id_number(losses.std()), VARIABLE_UNITS["L"], None),
            ("Interval kuantil 95%", f"{id_number(q_low)} – {id_number(q_high)}",
             VARIABLE_UNITS["L"], None),
        ])
        st.caption("Interval kuantil 95% = persentil ke-2,5 hingga ke-97,5 dari distribusi total "
                   "kerugian hasil Monte Carlo (interval ketidakpastian).")

        st.markdown("##### Sensitivitas Parameter (±20%)")
        st.plotly_chart(tornado_chart(run["sens"], unit=VARIABLE_UNITS["L"]))
        st.caption(interpret_tornado(run["sens"], DISPLAY_NAME))

    prototype_note()
