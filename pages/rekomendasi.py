import pandas as pd
import streamlit as st

from core.recommendation import compute_ranking, get_recommendation
from core.scenarios import BASELINE_NAME, VARIABLE_UNITS
from core.state import get_active_params
from core.formatting import id_number

st.header("Rekomendasi")

base_params, _, t = get_active_params()
rows, baseline_loss = compute_ranking(base_params, t)
top, beats_baseline = get_recommendation(rows)

st.markdown("##### Peringkat Skenario")
st.caption("Diurutkan dari total kerugian ekonomi terkecil, dihitung untuk SEMUA skenario "
           "terhadap baseline — terlepas dari skenario yang dipilih di sidebar untuk Section "
           "Perbandingan Skenario.")
ranking_df = pd.DataFrame([
    {
        "Peringkat": r["rank"],
        "Skenario": r["Skenario"],
        f"Total Kerugian ({VARIABLE_UNITS['L']})": id_number(r["loss"]),
        "Penurunan (absolut)": id_number(r["delta"]),
        "Penurunan (%)": f"{id_number(r['pct'])}%",
    }
    for r in rows
])
st.dataframe(ranking_df, hide_index=True, use_container_width=True)

st.markdown("##### Rekomendasi Utama")
if beats_baseline:
    st.success(
        f"**Rekomendasi Utama: {top['Skenario']}**\n\n"
        f"Total kerugian: {id_number(top['loss'])} {VARIABLE_UNITS['L']}. "
        f"Penurunan dibandingkan baseline: {id_number(top['delta'])} atau "
        f"{id_number(top['pct'])}%. Skenario ini merupakan **skenario dengan kerugian "
        f"terendah berdasarkan model saat ini** (dasar: minimum total kerugian ekonomi)."
    )
else:
    st.warning("Tidak terdapat skenario intervensi yang lebih baik daripada baseline "
               "berdasarkan parameter saat ini.")

st.caption(
    "**Catatan:** Rekomendasi prototipe hanya didasarkan pada total kerugian hasil "
    "simulasi. Biaya implementasi, kelayakan teknis, dampak lingkungan, dan faktor "
    "kelembagaan belum diperhitungkan."
)

st.markdown("##### Pertimbangan Implementasi Kebijakan")
st.caption(
    "Pada versi prototipe, peringkat ditentukan berdasarkan total kerugian ekonomi. "
    "Biaya implementasi dan kelayakan kebijakan memerlukan data tambahan dan penilaian "
    "ahli sehingga belum dimasukkan dalam perhitungan."
)
implementasi_df = pd.DataFrame([
    {
        "Skenario": r["Skenario"],
        f"Kerugian ({VARIABLE_UNITS['L']})": id_number(r["loss"]),
        "Biaya Implementasi": "Tidak ada intervensi" if r["Skenario"] == BASELINE_NAME else "Belum dimodelkan",
        "Kelayakan Teknis": "Acuan" if r["Skenario"] == BASELINE_NAME else "Belum dinilai",
    }
    for r in sorted(rows, key=lambda r: r["rank"])
])
st.dataframe(implementasi_df, hide_index=True, use_container_width=True)
