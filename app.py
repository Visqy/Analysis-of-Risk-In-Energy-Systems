"""
ARIES — Analysis of Risk In Energy Systems
Entry point: page config, print CSS, session-state init, sidebar parameter
controls (shared di semua halaman), dan navigasi multipage.

Jalankan dengan:
    streamlit run app.py
"""

import streamlit as st

from core.scenarios import SCENARIOS
from core.state import init_state, apply_pending_reset, request_reset

st.set_page_config(page_title="ARIES — Energy Risk DSS", layout="wide")

# Sembunyikan chrome Streamlit (toolbar, menu, ikon mode-bar chart, dsb) saat print/ekspor PDF.
st.markdown("""
<style>
@media print {
    header[data-testid="stHeader"],
    div[data-testid="stToolbar"],
    div[data-testid="stDecoration"],
    div[data-testid="stStatusWidget"],
    #MainMenu,
    footer,
    .modebar {
        display: none !important;
    }
}
</style>
""", unsafe_allow_html=True)

init_state()
apply_pending_reset()

st.title("⚡ ARIES")
st.caption("**A**nalysis of **R**isk **I**n **E**nergy **S**ystems — "
           "Decision Support System berbasis Mathematical Modeling & System Dynamics")

# ---------------- SIDEBAR: INPUT (Expert Mode, persist ke session_state) ----------------
st.sidebar.header("⚙️ Input Skenario & Parameter")

st.sidebar.selectbox("Pilih Skenario Kebijakan", list(SCENARIOS.keys()), key="scenario_name")

st.sidebar.markdown("---")
st.sidebar.subheader("Adjust Parameter Manual")
st.sidebar.slider("I0 (investasi dasar)", 0.0, 20.0, step=0.5, key="I0")
st.sidebar.slider("δ (depresiasi infrastruktur)", 0.01, 0.5, step=0.01, key="delta")
st.sidebar.slider("α (elastisitas demand thd ekonomi)", 0.1, 3.0, step=0.1, key="alpha")
st.sidebar.slider("β (sensitivitas demand thd harga)", 0.1, 3.0, step=0.1, key="beta")
st.sidebar.slider("γ (sensitivitas harga thd gap)", 0.05, 2.0, step=0.05, key="gamma")
st.sidebar.slider("G0 (aktivitas ekonomi awal)", 1.0, 30.0, step=1.0, key="G0")
st.sidebar.slider("g (laju pertumbuhan ekonomi)", 0.0, 0.2, step=0.01, key="g_rate")
st.sidebar.slider("κ (nilai ekonomi dari shortage)", 0.1, 10.0, step=0.1, key="kappa")
st.sidebar.slider("Horizon Simulasi (tahun)", 5, 60, step=1, key="T_end")

if st.sidebar.button("↺ Kembalikan ke Nilai Awal"):
    request_reset()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("Pengaturan Monte Carlo")
st.sidebar.slider("Jumlah simulasi", 100, 3000, step=100, key="n_sim")
st.sidebar.slider("Confidence level", 0.80, 0.99, step=0.01, key="conf")
st.sidebar.slider("std(δ)", 0.0, 0.1, step=0.005, key="delta_std")
st.sidebar.slider("std(γ)", 0.0, 0.5, step=0.01, key="gamma_std")
st.sidebar.slider("std(I0)", 0.0, 5.0, step=0.10, key="I0_std")

st.sidebar.markdown("---")
st.sidebar.subheader("Perbandingan Skenario")
st.sidebar.multiselect("Pilih skenario yang dibandingkan", list(SCENARIOS.keys()),
                        key="selected_scenarios")

# ---------------- NAVIGASI ----------------
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
pg.run()

st.markdown("---")
st.caption("ARIES v0.1 – Prototipe Penelitian")
