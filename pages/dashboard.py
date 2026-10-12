"""Halaman Dashboard: ringkasan hasil utama.

Banner pembuka dengan tombol demo, empat langkah alur kerja, kartu total
kerugian, VaR, CVaR dan skenario kerugian terendah, grafik ringkasan dinamika
dengan interpretasinya, dan catatan prototipe. Data dari `last_run`; kosong
bila simulasi belum dijalankan.
"""

import streamlit as st

from core.formatting import id_number
from core.interpretation import (
    capacity_gap_periods, decision_hint, interpret_capacity_demand,
)
from core.recommendation import get_recommendation
from core.scenarios import BASELINE_NAME, VARIABLE_UNITS
from ui.charts import overview_chart
from ui.components import (
    decision_box, hero, interpretation_card, kpi_cards, overview_steps, prototype_note,
    require_run,
)

hero()
overview_steps()

run = require_run()
if run is not None:
    cfg = run["config"]
    conf_txt = int(round(cfg["conf"] * 100))
    L_UNIT = VARIABLE_UNITS["L"]
    top, beats_baseline = get_recommendation(run["ranking"])
    if beats_baseline:
        low_sub, low_delta = L_UNIT, f"{top['Skenario']} · −{id_number(top['pct'], 1)}%"
    else:
        low_sub, low_delta = f"{top['Skenario']} (baseline)", None
    kpi_cards([
        ("Total kerugian", id_number(run["total_loss"]), L_UNIT, None),
        (f"VaR {conf_txt}%", id_number(run["var"]), "ambang kerugian", None),
        (f"CVaR {conf_txt}%", id_number(run["cvar"]), "rata-rata kondisi ekstrem", None),
        ("Skenario kerugian terendah", id_number(top["loss"]), low_sub, low_delta),
    ])

    t, E, D, P = run["t"], run["E"], run["D"], run["P"]
    st.markdown("##### Dinamika kapasitas, permintaan, dan harga")
    st.caption(f"Horizon simulasi 0–{cfg['T_end']} tahun")
    st.plotly_chart(overview_chart(
        t, E, D, P, capacity_gap_periods(t, E, D),
        y_unit=VARIABLE_UNITS["E"], p_unit=VARIABLE_UNITS["P"]))
    interpretation_card(interpret_capacity_demand(t, E, D))
    decision_box(decision_hint(run["ranking"], run["ranking_risk"], BASELINE_NAME))

    prototype_note()
