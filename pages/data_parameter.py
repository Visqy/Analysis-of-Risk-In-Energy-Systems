import pandas as pd
import streamlit as st

from core.scenarios import (
    PARAM_META, Y0_META, SCENARIOS, DATA_TYPE_LABEL, SOURCE_LABEL,
    PARAM_DISCLAIMER, VARIABLE_UNITS, OVERRIDE_LABELS,
)
from core.state import request_reset
from core.formatting import id_number

st.header("Data & Parameter")

st.warning(PARAM_DISCLAIMER)

st.markdown("##### Nilai Awal Kondisi")
y0_df = pd.DataFrame([
    {"Variabel": meta["label"], "Nilai Default": id_number(meta["default"]),
     "Satuan": meta["unit"], "Jenis Data": DATA_TYPE_LABEL, "Sumber": SOURCE_LABEL}
    for meta in Y0_META.values()
])
st.dataframe(y0_df, hide_index=True, use_container_width=True)

st.markdown("##### Parameter Model & Horizon Simulasi")
def _default_decimals(value):
    if isinstance(value, int):
        return 0
    return 3 if value < 1 else 2


param_df = pd.DataFrame([
    {"Parameter": meta["label"],
     "Nilai Default": id_number(meta["default"], _default_decimals(meta["default"])),
     "Satuan": meta["unit"],
     "Rentang Nilai": (f"{id_number(meta['min'], 0)} – {id_number(meta['max'], 0)}"
                        if isinstance(meta["min"], int)
                        else f"{id_number(meta['min'], 2)} – {id_number(meta['max'], 2)}"),
     "Jenis Data": DATA_TYPE_LABEL, "Sumber": SOURCE_LABEL}
    for meta in PARAM_META.values()
])
st.dataframe(param_df, hide_index=True, use_container_width=True)
st.caption("Rentang nilai di atas diterapkan langsung lewat slider di sidebar — "
           "nilai tidak bisa kosong atau di luar rentang yang ditentukan.")

st.markdown("##### Besar Intervensi per Skenario")
st.caption("Perubahan parameter relatif terhadap nilai dasar di sidebar, khusus untuk skenario tsb.")
intervensi_rows = []
for name, override in SCENARIOS.items():
    if not override:
        intervensi_rows.append({"Skenario": name, "Intervensi": "Tidak ada (baseline)"})
    else:
        parts = [f"{OVERRIDE_LABELS.get(k, k)} = {id_number(v, 0 if isinstance(v, int) else 2)}"
                 for k, v in override.items()]
        intervensi_rows.append({"Skenario": name, "Intervensi": ", ".join(parts)})
st.dataframe(pd.DataFrame(intervensi_rows), hide_index=True, use_container_width=True)

st.markdown("##### Satuan Variabel Keadaan")
st.dataframe(pd.DataFrame([
    {"Variabel": "t", "Satuan": VARIABLE_UNITS["t"]},
    {"Variabel": "E(t)", "Satuan": VARIABLE_UNITS["E"]},
    {"Variabel": "D(t)", "Satuan": VARIABLE_UNITS["D"]},
    {"Variabel": "P(t)", "Satuan": VARIABLE_UNITS["P"]},
    {"Variabel": "L(t)", "Satuan": VARIABLE_UNITS["L"]},
]), hide_index=True, use_container_width=True)

st.markdown("---")
b1, b2, b3, b4 = st.columns(4)
if b1.button("▶ Jalankan Simulasi", use_container_width=True):
    st.toast("Simulasi dijalankan dengan parameter saat ini.", icon="✅")
    st.switch_page("pages/dinamika_sistem.py")
if b2.button("↺ Kembalikan ke Nilai Awal", use_container_width=True):
    request_reset()
    st.rerun()
if b3.button("⚖ Bandingkan Skenario", use_container_width=True):
    st.switch_page("pages/perbandingan_skenario.py")
if b4.button("📄 Ekspor Hasil", use_container_width=True):
    st.switch_page("pages/laporan.py")
