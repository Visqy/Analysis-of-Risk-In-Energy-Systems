"""Halaman Analisis Risiko (Monte Carlo).

Menampilkan pengaturan simulasi dan parameter yang diacak (distribusi, μ, σ,
batas, satuan), statistik total kerugian (rata-rata, median, simpangan baku,
VaR, CVaR, interval kuantil 95%), histogram distribusi, dan diagram tornado
sensitivitas ±20%, masing-masing dengan interpretasi singkat. Data dari
`last_run`; kosong bila simulasi belum dijalankan.
"""

import numpy as np
import pandas as pd
import streamlit as st

from core.formatting import id_number
from core.inputs import DIST_OPTIONS, DISPLAY_NAME
from core.interpretation import interpret_histogram, interpret_tornado
from core.scenarios import PARAM_META, VARIABLE_UNITS
from ui.charts import histogram_chart, tornado_chart
from ui.components import require_run, unit_note

st.header("Analisis Risiko Ekonomi (Monte Carlo)")

run = require_run()
if run is not None:
    cfg = run["config"]
    losses, var, cvar = run["losses"], run["var"], run["cvar"]
    conf_pct = int(round(cfg["conf"] * 100))
    q_low, q_high = np.percentile(losses, [2.5, 97.5])
    unit_note()

    st.markdown("##### Pengaturan Simulasi")
    st.caption(f"Jumlah iterasi: {cfg['n_sim']} · Seed acak: {cfg['seed']} · "
               f"Distribusi: {DIST_OPTIONS[cfg['dist']]}")
    rows = []
    for name, spec in run["uncertain"].items():
        row = {"Parameter": f"{DISPLAY_NAME.get(name, name)} — {PARAM_META[name]['label'].split('(')[-1].rstrip(')')}",
               "Satuan": PARAM_META[name]["unit"], "Distribusi": "Normal terpotong" if spec[0] == "truncnormal" else "Normal",
               "Rata-rata (μ)": id_number(spec[1], 4), "Simpangan Baku (σ)": id_number(spec[2], 4)}
        if spec[0] == "truncnormal":
            row["Batas bawah"] = id_number(spec[3], 3)
            row["Batas atas"] = id_number(spec[4], 3)
        else:
            row["Batas bawah"] = "1e-6"
            row["Batas atas"] = "—"
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    st.markdown("##### Statistik Distribusi Kerugian")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Rata-rata ({VARIABLE_UNITS['L']})", id_number(losses.mean()))
    c2.metric(f"Median ({VARIABLE_UNITS['L']})", id_number(np.median(losses)))
    c3.metric(f"Simpangan Baku ({VARIABLE_UNITS['L']})", id_number(losses.std()))
    c4, c5, c6 = st.columns(3)
    c4.metric(f"VaR {conf_pct}% ({VARIABLE_UNITS['L']})", id_number(var))
    c5.metric(f"CVaR {conf_pct}% ({VARIABLE_UNITS['L']})", id_number(cvar))
    c6.metric("Interval kuantil 95%", f"{id_number(q_low)} – {id_number(q_high)}",
              help="Persentil 2,5% sampai 97,5% dari distribusi kerugian hasil simulasi — "
                   "interval ketidakpastian, bukan interval kepercayaan statistik.")
    st.caption("Interval kuantil 95% = persentil ke-2,5 hingga ke-97,5 dari distribusi total "
               "kerugian hasil Monte Carlo (interval ketidakpastian).")

    st.markdown("##### Distribusi Total Kerugian Ekonomi (Monte Carlo)")
    st.plotly_chart(histogram_chart(losses, var, cfg["conf"], unit=VARIABLE_UNITS["L"]))
    st.caption(interpret_histogram(losses, var, cvar, conf_pct))

    st.markdown("##### Sensitivitas Parameter (±20%)")
    st.plotly_chart(tornado_chart(run["sens"], unit=VARIABLE_UNITS["L"]))
    st.caption(interpret_tornado(run["sens"], DISPLAY_NAME))
