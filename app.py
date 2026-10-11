"""ARIES — Analysis of Risk In Energy Systems: titik masuk aplikasi Streamlit.

Menyiapkan konfigurasi halaman, CSS global (tata letak responsif berbasis lebar
kontainer, satuan di dalam kotak input, latar bar atas, aturan cetak A4
landscape beserta footer), inisialisasi state, header (skenario dan status),
navigasi 8 halaman, dan penjaga error: kesalahan di halaman ditampilkan sebagai
pesan ramah, bukan traceback mentah. Semua input ada di halaman Data & Parameter;
sidebar hanya navigasi.

Jalankan dengan:
    streamlit run app.py
"""

import streamlit as st
from streamlit.runtime.scriptrunner_utils.exceptions import ScriptControlException

from core.state import init_state, apply_pending_updates
from core.inputs import SHORT_UNIT
from ui.components import header

st.set_page_config(page_title="ARIES — Energy Risk DSS", layout="wide")

# Sembunyikan chrome Streamlit (toolbar, menu, ikon mode-bar chart, dsb) saat print/ekspor PDF.
st.markdown("""
<style>
/* Samakan tinggi label kotak angka agar input dalam satu baris sejajar. */
@media (min-width: 992px) {
    [class*="st-key-w_in_"] label[data-testid="stWidgetLabel"] { min-height: 3.4em; align-items: flex-start; }
}
/* Responsif berdasarkan lebar kontainer (bukan viewport): sidebar terbuka/tertutup tetap rapi. */
div[data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
div[data-testid="stColumn"] { min-width: min(100%, 150px); }
.st-key-maincols, [class*="st-key-card_"] { container-type: inline-size; }
.st-key-maincols div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(1)
    { flex: 3 1 440px; min-width: min(100%, 440px); }
.st-key-maincols div[data-testid="stHorizontalBlock"] > div[data-testid="stColumn"]:nth-child(2)
    { flex: 1.25 1 270px; min-width: min(100%, 270px); }
@container (max-width: 820px) {
    [class*="st-key-card_"] div[data-testid="stHorizontalBlock"] { display: grid; grid-template-columns: 1fr 1fr; }
    [class*="st-key-card_"] div[data-testid="stColumn"] { flex: unset; width: auto; min-width: 0; }
}
@container (max-width: 440px) {
    [class*="st-key-card_"] div[data-testid="stHorizontalBlock"] { grid-template-columns: 1fr; }
}
.st-key-titlebar { flex-direction: row; flex-wrap: wrap; align-items: flex-end;
    justify-content: space-between; gap: 0.5rem 1.5rem; }
.st-key-titlebar div[data-testid="stElementContainer"] { width: auto; }
.st-key-titlebar div[data-testid="stElementContainer"]:first-child { flex: 1 1 320px; }
.st-key-titlebar div[data-testid="stElementContainer"]:last-child { flex: 0 1 auto; padding-bottom: 0.9rem; }
/* Bar atas Streamlit: latar putih solid agar konten yang di-scroll tidak tembus pandang. */
header[data-testid="stHeader"] { background: #FFFFFF !important; box-shadow: 0 1px 0 #E3E8EF; }
@page { size: A4 landscape; margin: 10mm 10mm 16mm;
    @bottom-center { content: "ARIES v0.1 – Prototipe Penelitian"; font-size: 9pt; color: #5C6B80; } }
@media print {
    html, body, .stApp, div[data-testid="stAppViewContainer"],
    section[data-testid="stMain"], div[data-testid="stMainBlockContainer"] {
        height: auto !important;
        min-height: 0 !important;
        overflow: visible !important;
    }
    div[data-testid="stMainBlockContainer"] { padding-bottom: 0 !important; }
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    section[data-testid="stSidebar"],
    #MainMenu,
    footer,
    .st-key-appfooter,
    .modebar {
        display: none !important;
    }
    div[data-testid="stAlert"],
    div[data-testid="stPlotlyChart"],
    div[data-testid="stDataFrame"],
    div[data-testid="stMetric"],
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h5 {
        break-inside: avoid;
    }
    div[data-testid="stMarkdownContainer"] h3,
    div[data-testid="stMarkdownContainer"] h5 {
        break-after: avoid;
    }
}
</style>
""", unsafe_allow_html=True)

# Satuan ringkas di dalam kotak input (rata kanan), dibangkitkan dari SHORT_UNIT.
_unit_css = "".join(
    f'.st-key-w_in_{k} [data-testid="stTextInputRootElement"] {{ position: relative; }}'
    f'.st-key-w_in_{k} [data-testid="stTextInputRootElement"]::after {{ content: "{u}"; position: absolute;'
    f' right: 12px; top: 50%; transform: translateY(-50%); font-size: 12px; color: #5C6B80;'
    f' pointer-events: none; }}'
    f'.st-key-w_in_{k} input {{ padding-right: calc({len(u)} * 0.6em + 1.6rem); }}'
    for k, u in SHORT_UNIT.items() if u
)
st.markdown(f"<style>{_unit_css}</style>", unsafe_allow_html=True)

init_state()
apply_pending_updates()

st.logo("ui/assets/logo.svg", icon_image="ui/assets/logo_icon.svg", size="large")

pg = st.navigation([
    st.Page("pages/dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/data_parameter.py", title="Data & Parameter", icon="🗂️"),
    st.Page("pages/dinamika_sistem.py", title="Dinamika Sistem", icon="📈"),
    st.Page("pages/analisis_kestabilan.py", title="Analisis Kestabilan", icon="🧮"),
    st.Page("pages/analisis_risiko.py", title="Analisis Risiko", icon="🎲"),
    st.Page("pages/perbandingan_skenario.py", title="Perbandingan Skenario", icon="⚖️"),
    st.Page("pages/rekomendasi.py", title="Rekomendasi", icon="✅"),
    st.Page("pages/laporan.py", title="Laporan", icon="📄"),
])

st.sidebar.markdown(
    """<div style="margin-top:24px;padding:14px;border:1px solid #2C4D74;border-radius:10px;background:#143559">
<div style="font-size:13px;font-weight:600;color:#fff;margin-bottom:6px">Prototipe penelitian</div>
<div style="font-size:12px;line-height:1.5;color:#B8C9DE">Nilai bawaan masih ilustratif. Setiap hasil menyimpan skenario,
parameter, iterasi, seed, tanggal analisis, dan versi model.</div></div>""",
    unsafe_allow_html=True,
)

header()
try:
    pg.run()
except ScriptControlException:
    raise  # rerun / stop / switch_page: alur kontrol normal Streamlit
except Exception as exc:  # jangan tampilkan traceback mentah ke pengguna
    import logging
    logging.getLogger("aries").exception("Kesalahan di halaman %s", pg.title)
    st.error("Halaman ini gagal ditampilkan. Muat ulang halaman (F5); bila berulang, kembali ke "
             "**Data & Parameter** lalu jalankan ulang simulasi.")
    with st.expander("Detail teknis"):
        st.code(f"{type(exc).__name__}: {exc}")

with st.container(key="appfooter"):
    st.markdown("---")
    st.caption("ARIES v0.1 – Prototipe Penelitian")
