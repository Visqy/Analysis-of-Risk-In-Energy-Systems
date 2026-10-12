"""Komponen UI bersama: header, stepper, tile, strip metadata hasil, dan keadaan kosong."""

import base64
from pathlib import Path

import streamlit as st

from core.interpretation import CATATAN_PROTOTIPE
from core.state import get_run, is_stale, ui_status

_BADGES = {
    "invalid": ("Input belum valid", "#FDECEA", "#8F1D15", "#F2B8B2"),
    "ready": ("Model siap", "#E6F6EE", "#17694A", "#A9DBC4"),
    "fresh": ("Hasil terbaru", "#E7F0FF", "#1F4FB8", "#B7CEF7"),
    "stale": ("Hasil usang — jalankan ulang", "#FFF6DC", "#7A5200", "#EBCB76"),
}


def header():
    """Chip skenario + badge status, dipasang di bar atas Streamlit (fixed).
    Brand ARIES ada di sidebar lewat st.logo (app.py)."""
    status, _ = ui_status()
    text, bg, fg, bd = _BADGES[status]
    scenario = st.session_state["scenario_name"]
    st.markdown(
        f"""
<style>
.aries-topbar {{ position: fixed; top: 0.6rem; right: 4.2rem; z-index: 1000000;
  display: flex; align-items: center; gap: 10px; max-width: calc(100vw - 9rem); }}
.aries-topbar .chip {{ padding: 6px 12px; border-radius: 8px; font-size: 13px; white-space: nowrap;
  overflow: hidden; text-overflow: ellipsis; }}
div[data-testid="stElementContainer"]:has(.aries-topbar) {{ position: absolute; height: 0; margin: 0; }}
@media (max-width: 760px) {{
  .aries-topbar .chip-scn {{ display: none; }}
  .aries-topbar {{ right: 3.4rem; }}
}}
@media print {{ .aries-topbar {{ position: static; margin-bottom: 8px; }}
  div[data-testid="stElementContainer"]:has(.aries-topbar) {{ position: static; height: auto; }} }}
</style>
<div class="aries-topbar">
  <div class="chip chip-scn" style="border:1px solid #DCE3EC;background:#fff;color:#5C6B80">
    Skenario: <strong style="color:#10233B">{scenario}</strong></div>
  <div class="chip" style="border-radius:999px;font-weight:600;border:1px solid {bd};background:{bg};color:{fg}">{text}</div>
</div>""",
        unsafe_allow_html=True,
    )


def stepper():
    """Indikator tahap Input – Simulasi – Hasil (tahap Hasil aktif bila hasil terbaru)."""
    status, _ = ui_status()
    now = 3 if status == "fresh" else 1

    def circle(i):
        base = ("width:26px;height:26px;min-width:26px;border-radius:50%;display:inline-flex;"
                "align-items:center;justify-content:center;font-size:12px;font-weight:700;flex:none;")
        if i == now:
            return base + "background:#1F5FD8;color:#fff;border:1px solid #1F5FD8"
        if i < now:
            return base + "background:#fff;color:#1F5FD8;border:1px solid #1F5FD8"
        return base + "background:#fff;color:#5C6B80;border:1px solid #B9C6D6"

    def step(i, text):
        weight = "font-weight:700" if i == now else "font-weight:500;color:#5C6B80"
        return (f'<span style="display:inline-flex;align-items:center;gap:6px;flex:none;white-space:nowrap">'
                f'<span style="{circle(i)}">{i}</span><span style="{weight}">{text}</span></span>')

    line = '<span style="flex:0 1 36px;min-width:8px;height:1px;background:#B9C6D6"></span>'
    st.markdown(
        f"""<div style="display:flex;align-items:center;gap:8px;font-size:13px;flex-wrap:nowrap">
{step(1, "Input")}{line}{step(2, "Simulasi")}{line}{step(3, "Hasil")}</div>""",
        unsafe_allow_html=True,
    )


def tile(label, value, unit, small=False):
    """Kembalikan HTML satu kartu ringkas (label, nilai, satuan) untuk Pratinjau Hasil."""
    size = 14 if small else 20
    color = "#10233B" if value != "—" else "#8A97A8"
    return (f'<div style="padding:10px 12px;border-radius:8px;background:#F3F6FA">'
            f'<div style="font-size:11px;color:#5C6B80">{label}</div>'
            f'<div style="font-size:{size}px;font-weight:700;color:{color};line-height:1.35;'
            f'min-height:27px">{value}</div>'
            f'<div style="font-size:10px;color:#5C6B80">{unit}</div></div>')


def require_run():
    """Kembalikan record hasil terakhir, atau tampilkan keadaan kosong (None)."""
    run = get_run()
    if run is None:
        st.info("Belum ada hasil. Buka halaman **Data & Parameter**, periksa input, "
                "lalu klik **Jalankan**.")
        st.page_link("pages/data_parameter.py", label="Buka Data & Parameter")
        return None
    result_strip(run)
    return run


def chips(items):
    """Baris item metadata: label kecil abu-abu di atas, nilai tebal di bawah.

    Args:
        items: list (label, nilai); item dibungkus per item pada layar sempit.
    """
    cells = "".join(
        '<div style="min-width:0">'
        f'<div style="font-size:11px;color:#5C6B80;line-height:1.3">{label}</div>'
        f'<div style="font-size:13px;font-weight:600;color:#10233B;line-height:1.4">{value}</div>'
        "</div>"
        for label, value in items)
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;gap:8px 28px;padding:2px 0 14px">'
        f"{cells}</div>", unsafe_allow_html=True)


def result_strip(run):
    """Strip metadata di atas hasil: skenario, periode, iterasi, seed, tanggal
    analisis, dan sumber data (versi model ada di footer); plus peringatan bila
    input berubah sejak hasil."""
    cfg = run["config"]
    src = cfg["source"]
    src_txt = src["status"]
    detail = " ".join(x for x in (src["name"], src["year"]) if x)
    if src["status"] == "Data Aktual" and detail:
        src_txt += f" ({detail})"
    chips([
        ("Skenario aktif", cfg["scenario"]),
        ("Periode analisis", f"0–{cfg['T_end']} tahun"),
        ("Iterasi", cfg["n_sim"]),
        ("Seed", cfg["seed"]),
        ("Dijalankan", run["meta"]["date"].replace("T", " ")),
        ("Sumber data", src_txt),
    ])
    if is_stale():
        st.warning("Input berubah sejak simulasi terakhir — hasil di bawah masih memakai "
                   "konfigurasi sebelumnya. Jalankan ulang di halaman Data & Parameter.")


def interpretation_card(text):
    """Tampilkan satu interpretasi (Temuan/Makna/Implikasi) dalam satu card netral."""
    with st.container(border=True):
        st.markdown(text)


def prototype_note():
    """Catatan tetap di akhir halaman hasil: hasil prototipe, bukan rekomendasi kebijakan nyata."""
    st.caption(CATATAN_PROTOTIPE)


def metric_unit(container, label, value, unit):
    """Kartu angka `container.metric(label, value)` dengan satuan sebagai keterangan kecil di bawahnya."""
    container.metric(label, value)
    container.caption(unit)


_LOGO_PATH = Path(__file__).parent / "assets" / "logo_fmipa_unpad.webp"
INSTITUTION_LINES = (
    "Departemen Matematika",
    "Fakultas Matematika dan Ilmu Pengetahuan Alam",
    "Universitas Padjadjaran",
)


@st.cache_resource
def _logo_data_uri():
    """Logo FMIPA Unpad sebagai data URI (dibaca sekali, dipakai ulang di tiap run)."""
    return "data:image/webp;base64," + base64.b64encode(_LOGO_PATH.read_bytes()).decode()


def institution_footer(version_text):
    """Footer dua kolom: kartu identitas institusi (kiri) dan teks versi (kanan).

    Kartu berisi logo dan tiga baris nama institusi; pada lebar sempit teks turun
    di bawah logo dan kedua kolom bertumpuk. Teks versi disembunyikan saat cetak
    karena footer cetak (`@page`) sudah memuatnya.

    Args:
        version_text: teks versi yang ditampilkan di kolom kanan.
    """
    lines = "".join(
        f'<div style="font-size:{14 if i == 0 else 12.5}px;font-weight:{700 if i == 0 else 500};'
        f'color:{"#10233B" if i == 0 else "#5C6B80"};line-height:1.45">{x}</div>'
        for i, x in enumerate(INSTITUTION_LINES))
    st.markdown(
        '<div class="aries-footer" style="display:flex;flex-wrap:wrap;align-items:center;'
        'justify-content:space-between;gap:12px 24px">'
        '<div class="aries-institution" style="display:flex;flex-wrap:wrap;align-items:center;'
        'gap:10px 20px;padding:12px 16px;border:1px solid #DCE3EC;border-radius:10px;'
        'background:#FFFFFF;flex:0 1 auto;min-width:0">'
        f'<img src="{_logo_data_uri()}" alt="Logo FMIPA Unpad" '
        'style="width:170px;max-width:100%;height:auto">'
        f'<div style="min-width:0">{lines}</div></div>'
        f'<div class="aries-footer-version" style="font-size:13px;color:#5C6B80">{version_text}</div>'
        "</div>",
        unsafe_allow_html=True)
