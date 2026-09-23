import streamlit as st

from core.model import simulate, trapz as _trapz
from core.recommendation import compute_ranking
from core.scenarios import DEFAULT_Y0
from core.state import get_active_params, request_import
from core.io_xlsx import build_export_workbook, parse_import_workbook, APP_VERSION

st.header("Laporan")

s = st.session_state
base_params, params, t = get_active_params()
E, D, P, L = simulate(params, DEFAULT_Y0, t)
total_loss = _trapz(L, t)
ranking_rows, _ = compute_ranking(base_params, t)
mc_results = s.get("mc_results")

st.markdown("##### Ekspor Hasil")
st.caption("Berisi parameter aktif, hasil simulasi skenario aktif, peringkat skenario, dan "
           "ringkasan Monte Carlo (kalau sudah dijalankan) dalam satu file .xlsx.")
workbook_bytes = build_export_workbook(
    s["scenario_name"], s, t, E, D, P, L, total_loss, ranking_rows, mc_results,
)
st.download_button(
    "📄 Unduh Laporan (.xlsx)", data=workbook_bytes,
    file_name="aries_laporan.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

st.markdown("---")
st.markdown("##### Impor Parameter")
st.caption("Upload file .xlsx dengan sheet 'Parameter' (format sama seperti hasil Ekspor "
           "Hasil di atas). Nilai kosong atau di luar rentang akan ditolak seluruhnya.")
uploaded = st.file_uploader("Pilih file .xlsx", type=["xlsx"])
if uploaded is not None:
    values, errors = parse_import_workbook(uploaded)
    if errors:
        st.error("File ditolak:\n\n" + "\n".join(f"- {e}" for e in errors))
    else:
        st.success(f"{len(values)} parameter valid ditemukan.")
        if st.button("Terapkan Parameter Ini"):
            request_import(values)
            st.rerun()

st.markdown("---")
st.markdown("##### Informasi Versi Model")
st.caption(APP_VERSION)
