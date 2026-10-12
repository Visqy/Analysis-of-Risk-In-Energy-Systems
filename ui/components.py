"""Komponen UI bersama: header, stepper, tile, strip metadata hasil, dan keadaan kosong."""

import base64
import html
import re
from pathlib import Path

import streamlit as st

from core.interpretation import CATATAN_PROTOTIPE
from core.state import execute_run, get_run, is_stale, ui_status

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


_TMI_RE = re.compile(
    r"\*\*(Temuan|Makna|Implikasi):\*\*\s*(.*?)(?=\n\n\*\*(?:Temuan|Makna|Implikasi):\*\*|\Z)", re.S)


def interpretation_card(text):
    """Tampilkan satu interpretasi (Temuan/Makna/Implikasi) dalam satu card.

    Tiap bagian diberi label kecil berwarna dan garis pemisah. Bila teks tidak
    berformat tiga bagian, ditampilkan apa adanya sebagai markdown.

    Args:
        text: keluaran `interpret_*` berformat tiga bagian berlabel Temuan, Makna, Implikasi.
    """
    parts = {k: v.strip() for k, v in _TMI_RE.findall(text)}
    with st.container(border=True):
        if set(parts) != {"Temuan", "Makna", "Implikasi"}:
            st.markdown(text)
            return
        rows = "".join(
            '<div style="padding:10px 0;border-top:1px solid #E3E8EF">'
            f'<div style="font-size:11px;font-weight:700;letter-spacing:.06em;color:#1F5FD8">{k.upper()}</div>'
            f'<div style="font-size:14px;color:#2B3A4F;line-height:1.55;padding-top:4px">{html.escape(parts[k])}</div></div>'
            for k in ("Temuan", "Makna", "Implikasi"))
        st.markdown(
            '<div style="font-size:15px;font-weight:700;color:#10233B">Interpretasi hasil</div>'
            '<div style="font-size:12px;color:#5C6B80;padding:2px 0 8px">Temuan · Makna · Implikasi</div>'
            f"{rows}", unsafe_allow_html=True)


def decision_box(text):
    """Kotak hijau "Untuk pengambil keputusan" berisi satu kalimat bersyarat `text`."""
    st.markdown(
        '<div style="background:#E8F5EE;border-radius:8px;padding:12px 14px;margin:2px 0 10px;'
        'font-size:13.5px;line-height:1.5;color:#17694A">'
        f'<strong style="color:#10233B">Untuk pengambil keputusan:</strong> {html.escape(text)}</div>',
        unsafe_allow_html=True)


def prototype_note():
    """Catatan tetap di akhir halaman hasil: hasil prototipe, bukan rekomendasi kebijakan nyata."""
    st.caption(CATATAN_PROTOTIPE)


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


_HERO_CSS = """<style>
.st-key-hero { background: linear-gradient(135deg, #0F2A47 0%, #1D4A73 100%); border-radius: 14px;
  padding: 28px 28px 24px; margin-bottom: 14px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.st-key-hero p, .st-key-hero div[data-testid="stMarkdownContainer"] { color: #FFFFFF; }
.st-key-hero button, .st-key-hero a[data-testid="stPageLink-NavLink"] { height: 42px; min-height: 42px;
  padding: 0 18px; font-size: 14px; border-radius: 8px; display: inline-flex; align-items: center; gap: 6px; }
.st-key-hero button { background: #FFFFFF; color: #10233B; border: 1px solid #FFFFFF; font-weight: 600; }
.st-key-hero button p, .st-key-hero button span { color: #10233B; }
.st-key-hero button:disabled { background: #FFFFFF !important; border-color: #FFFFFF !important; opacity: 1 !important; }
.st-key-hero button:disabled p, .st-key-hero button:disabled span { color: #17694A !important; }
.st-key-hero a[data-testid="stPageLink-NavLink"] { background: rgba(255,255,255,0.14); color: #FFFFFF;
  border: 1px solid rgba(255,255,255,0.35); border-radius: 8px; font-weight: 600; }
.st-key-hero a[data-testid="stPageLink-NavLink"] p,
.st-key-hero a[data-testid="stPageLink-NavLink"] span { color: #FFFFFF !important; }
.st-key-hero a[data-testid="stPageLink-NavLink"]:hover { background: rgba(255,255,255,0.24); }
</style>"""


def hero():
    """Banner pembuka Dashboard: judul, deskripsi, tombol "Jalankan demo" dan tautan input.

    Tombol menjalankan simulasi dengan input sekarang (callback `execute_run`);
    label mengikuti status: "Jalankan demo", "Demo selesai" (hasil terbaru, tombol
    nonaktif), "Jalankan ulang" (hasil usang). Nonaktif bila input tidak valid.
    """
    status, _ = ui_status()
    label, disabled = {
        "invalid": ("Jalankan demo", True), "ready": ("Jalankan demo", False),
        "fresh": ("Demo selesai", True), "stale": ("Jalankan ulang", False),
    }[status]
    st.markdown(_HERO_CSS, unsafe_allow_html=True)
    with st.container(key="hero"):
        st.markdown(
            '<div style="font-size:12px;letter-spacing:.08em;color:#B8C9DE;font-weight:600">'
            "DECISION SUPPORT SYSTEM · PROTOTIPE PENELITIAN</div>"
            '<div style="font-size:30px;font-weight:700;color:#FFFFFF;line-height:1.25;padding:6px 0">'
            "Analysis of Risk in Energy Systems</div>"
            '<div style="font-size:14.5px;color:#DCE7F4;line-height:1.55;max-width:640px;padding-bottom:16px">'
            "Eksplorasi hubungan kapasitas, permintaan, harga, kerugian ekonomi, dan risiko untuk "
            "membandingkan alternatif skenario energi.</div>", unsafe_allow_html=True)
        with st.container(horizontal=True, key="hero_actions"):
            st.button(label, key="hero_run", on_click=execute_run, disabled=disabled,
                      icon=":material/check:" if status == "fresh" else None)
            st.page_link("pages/data_parameter.py", label="Masukkan data sendiri",
                         icon=":material/edit:")


def overview_steps():
    """Empat langkah alur kerja: Isi data, Jalankan, Bandingkan, Interpretasikan."""
    done = 2 if get_run() is not None else 0
    steps = [("Isi data", "Parameter model"), ("Jalankan", "Simulasi sistem"),
             ("Bandingkan", "Skenario energi"), ("Interpretasikan", "Risiko & implikasi")]
    cells = "".join(
        '<div style="flex:1 1 150px;display:flex;align-items:center;gap:10px;padding:12px 14px;'
        'border-right:1px solid #E3E8EF">'
        f'<span style="width:26px;height:26px;min-width:26px;border-radius:50%;display:inline-flex;'
        f'align-items:center;justify-content:center;font-size:12px;font-weight:700;'
        f'background:{"#1F5FD8" if i <= done else "#E7F0FF"};color:{"#fff" if i <= done else "#1F5FD8"}">{i}</span>'
        f'<span><div style="font-size:13.5px;font-weight:600;color:#10233B">{a}</div>'
        f'<div style="font-size:12px;color:#5C6B80">{b}</div></span></div>'
        for i, (a, b) in enumerate(steps, 1))
    st.markdown(
        '<div style="display:flex;flex-wrap:wrap;border:1px solid #E3E8EF;border-radius:12px;'
        f'background:#fff;overflow:hidden;margin-bottom:14px">{cells}</div>', unsafe_allow_html=True)


_KPI_CSS = """<style>
.aries-kpi-wrap { container-type: inline-size; }
.aries-kpi-grid { display: grid; gap: 12px; grid-template-columns: 1fr; margin-bottom: 14px; }
@container (min-width: 420px) { .aries-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@container (min-width: 420px) { .aries-kpi-grid[data-n="1"] { grid-template-columns: 1fr; } }
@container (min-width: 640px) { .aries-kpi-grid[data-n="3"] { grid-template-columns: repeat(3, 1fr); } }
@container (min-width: 880px) { .aries-kpi-grid[data-n="4"] { grid-template-columns: repeat(4, 1fr); } }
</style>"""


def kpi_cards(cards):
    """Deret kartu ringkas; jumlah kolom mengikuti lebar kontainer dan jumlah kartu.

    Args:
        cards: list (label, nilai, subjudul, delta); `delta` teks hijau opsional (None bila tidak ada).
    """
    def card(label, value, sub, delta):
        extra = (f'<div style="font-size:12.5px;color:#17694A;padding-top:2px">{html.escape(delta)}</div>'
                 if delta else "")
        return ('<div class="aries-kpi-card" style="background:#fff;border:1px solid #E3E8EF;'
                'border-radius:12px;padding:14px 16px;min-width:0">'
                f'<div style="font-size:12.5px;color:#5C6B80">{html.escape(label)}</div>'
                f'<div style="font-size:26px;font-weight:600;color:#10233B;line-height:1.3;padding:4px 0">{value}</div>'
                f'<div style="font-size:12.5px;color:#5C6B80">{html.escape(sub)}</div>{extra}</div>')
    st.markdown(
        _KPI_CSS + '<div class="aries-kpi-wrap">'
        f'<div class="aries-kpi-grid" data-n="{len(cards)}">'
        + "".join(card(*c) for c in cards) + "</div></div>", unsafe_allow_html=True)
