"""Halaman Peringkat Skenario Berdasarkan Total Kerugian.

Menampilkan dua tabel peringkat terpisah: berdasarkan total kerugian
(pengurangan dan persentase penurunan terhadap baseline; `last_run["ranking"]`)
dan berdasarkan risiko, yaitu CVaR dari Monte Carlo tiap skenario
(`last_run["ranking_risk"]`), disertai interpretasi perbandingan keduanya.
Interpretasi menyatakan skenario dengan kerugian terendah berdasarkan model saat
ini (atau bahwa tidak ada skenario yang lebih baik dari baseline), lalu catatan
batasan dan tabel pertimbangan implementasi (biaya dan kelayakan belum
dimodelkan).
"""

import pandas as pd
import streamlit as st

from core.formatting import id_number
from core.interpretation import interpret_ranking_basis
from core.scenarios import BASELINE_NAME, VARIABLE_UNITS
from ui.components import interpretation_card, prototype_note, require_run

st.header("Peringkat Skenario Berdasarkan Total Kerugian")

run = require_run()
if run is not None:
    rows = run["ranking"]

    conf_pct = int(round(run["config"]["conf"] * 100))
    L_UNIT = VARIABLE_UNITS["L"]

    st.markdown("##### Peringkat Berdasarkan Total Kerugian")
    st.caption("Diurutkan dari total kerugian ekonomi terkecil, dihitung untuk SEMUA skenario "
               "terhadap baseline pada konfigurasi yang dijalankan.")
    st.dataframe(pd.DataFrame([
        {
            "Peringkat": r["rank"],
            "Skenario": r["Skenario"],
            f"Total Kerugian ({VARIABLE_UNITS['L']})": id_number(r["loss"]),
            "Penurunan (absolut)": id_number(r["delta"]),
            "Penurunan (%)": f"{id_number(r['pct'])}%",
        } for r in rows
    ]), hide_index=True)

    st.markdown(f"##### Peringkat Berdasarkan Risiko (CVaR {conf_pct}%)")
    st.caption(f"Diurutkan dari CVaR {conf_pct}% terkecil, yaitu rata-rata kerugian pada kondisi "
               "terburuk dari simulasi Monte Carlo yang dijalankan untuk tiap skenario "
               "(iterasi, seed, dan distribusi sama dengan analisis utama).")
    rows_risk = run["ranking_risk"]
    st.dataframe(pd.DataFrame([
        {
            "Peringkat": r["rank"],
            "Skenario": r["Skenario"],
            f"CVaR {conf_pct}% ({L_UNIT})": id_number(r["cvar"]),
            f"VaR {conf_pct}% ({L_UNIT})": id_number(r["var"]),
            "Penurunan CVaR (%)": f"{id_number(r['cvar_pct'])}%",
        } for r in rows_risk
    ]), hide_index=True)
    interpretation_card(interpret_ranking_basis(rows, rows_risk, conf_pct, BASELINE_NAME))

    st.caption(
        "**Catatan:** Peringkat ini hanya didasarkan pada total kerugian hasil simulasi. "
        "Biaya implementasi, kelayakan teknis, dampak lingkungan, dan faktor kelembagaan "
        "belum diperhitungkan, dan hasilnya belum menjadi rekomendasi kebijakan nyata."
    )

    st.markdown("##### Pertimbangan Implementasi Kebijakan")
    st.caption(
        "Pada versi prototipe, peringkat ditentukan berdasarkan total kerugian ekonomi. "
        "Biaya implementasi dan kelayakan kebijakan memerlukan data tambahan dan penilaian "
        "ahli sehingga belum dimasukkan dalam perhitungan."
    )
    st.dataframe(pd.DataFrame([
        {
            "Skenario": r["Skenario"],
            f"Kerugian ({VARIABLE_UNITS['L']})": id_number(r["loss"]),
            "Biaya Implementasi": "Tidak ada intervensi" if r["Skenario"] == BASELINE_NAME else "Belum dimodelkan",
            "Kelayakan Teknis": "Acuan" if r["Skenario"] == BASELINE_NAME else "Belum dinilai",
        } for r in sorted(rows, key=lambda r: r["rank"])
    ]), hide_index=True)

    prototype_note()
