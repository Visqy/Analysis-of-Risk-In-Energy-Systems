"""Halaman Laporan: unduh laporan xlsx dan informasi versi model.

Tombol unduh membangun laporan dari `last_run` (`core.io_xlsx.build_export_workbook`).
Kosong bila simulasi belum dijalankan.
"""

import streamlit as st

from core.io_xlsx import build_export_workbook
from ui.components import require_run

st.header("Laporan")

run = require_run()
if run is not None:
    st.markdown("##### Unduh Laporan")
    st.caption("Berisi input, asumsi, metadata reproduksibilitas (skenario, parameter, iterasi, "
               "seed, tanggal analisis, versi model), hasil simulasi, perbandingan skenario, "
               "ringkasan Monte Carlo, dan grafik dalam satu file .xlsx.")
    date_tag = run["meta"]["date"][:10]
    st.download_button(
        "📄 Unduh Laporan (.xlsx)", data=build_export_workbook(run),
        file_name=f"aries_laporan_{date_tag}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    st.info("Sistem ini masih berupa **prototipe penelitian** dan nilai bawaan masih bersifat "
            "ilustratif.")

