"""Halaman Data & Parameter: satu-satunya tempat input.

Berisi pilihan skenario dan sumber data, kondisi awal dan horizon, parameter
model, pengaturan analisis risiko (iterasi, tingkat keyakinan, seed,
distribusi, σ), Mode Eksplorasi Cepat (slider tersinkron dengan kotak angka),
panel Konfigurasi Aktif dan Pratinjau Hasil, tombol Jalankan Simulasi dan
Kembalikan ke Nilai Awal, skenario kustom, impor xlsx, serta dokumentasi
parameter. Input divalidasi per field; tombol Jalankan nonaktif bila ada input
yang salah. Nilai kanonik dan key widget dikelola `core.state` (lihat `bind`).
"""

import pandas as pd
import streamlit as st

from core.formatting import id_number
from core.io_xlsx import parse_import_workbook
from core.inputs import (
    DIST_OPTIONS, FIELD_SPECS, HELP, LATEX_LABEL, PARAM_KEYS, SHORT_DESC, SIGMA_KEYS,
    SOURCE_OPTIONS, range_text, scenario_names,
)
from core.scenarios import (
    DATA_TYPE_LABEL, OVERRIDE_LABELS, PARAM_DISCLAIMER, PARAM_META, SCENARIOS,
    SOURCE_LABEL, VARIABLE_UNITS, Y0_META,
)
from core.state import (
    bind, current_config, execute_run, get_run, init_state, request_reset, request_set,
    save_custom_scenario, slider_changed, sync_slider_from_text, ui_status,
)
from ui.components import stepper, tile

init_state()  # aman bila halaman terpanggil sebelum app.py
s = st.session_state
cfg, errors = current_config()
status, n_err = ui_status()


def _flow_html():
    steps = ["Input & validasi", "Simulasi model", "Risiko & skenario", "Rekomendasi"]
    rows = []
    for n, label in enumerate(steps):
        line = ('<div style="width:2px;height:14px;background:#B9C6D6;margin:2px 0 2px 11px"></div>'
                if n < len(steps) - 1 else "")
        rows.append(
            '<div style="display:flex;align-items:center;gap:10px">'
            '<span style="width:24px;height:24px;border-radius:50%;background:#E7F0FF;'
            'border:1px solid #B7CEF7;display:inline-flex;align-items:center;justify-content:center;flex:none">'
            '<span style="width:8px;height:8px;border-radius:50%;background:#1F5FD8"></span></span>'
            f'<span style="font-size:13px;color:#10233B">{label}</span></div>{line}')
    return '<div style="padding:2px 0 4px">' + "".join(rows) + "</div>"


_FLOW = _flow_html()


def field(key):
    """Satu kotak input untuk field `key`: label, tooltip, dan rentang atau pesan error."""
    sp = FIELD_SPECS[key]
    st.text_input(LATEX_LABEL[key], help=f"{SHORT_DESC[key]}\n\n{HELP[key]}", **bind(f"in_{key}"))
    if key in errors:
        st.markdown(f":red[**{errors[key]}**]")
    else:
        st.caption(f"Rentang valid: {range_text(key)}")


def row_of_fields(keys, per_row=4):
    """Susun field `keys` dalam baris berisi `per_row` kolom."""
    for i in range(0, len(keys), per_row):
        cols = st.columns(per_row)
        for col, key in zip(cols, keys[i:i + per_row]):
            with col:
                field(key)


with st.container(key="titlebar"):
    st.title("Data & Parameter Model")
    stepper()
st.caption("Masukkan nilai, periksa konfigurasi, lalu jalankan simulasi.")

if s.pop("_just_ran", False):
    st.success("Simulasi selesai. Buka halaman Dinamika Sistem, Analisis Kestabilan, "
               "Analisis Risiko, Perbandingan Skenario, atau Rekomendasi untuk melihat hasil.")

st.warning(f"**Mode prototipe.** {PARAM_DISCLAIMER}")

_main = st.container(key="maincols")
with _main:
    left, right = st.columns([3, 1.25], gap="small")

with left:
    with st.container(border=True, key="card_skenario"):
        st.subheader("Skenario dan Sumber Data")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("Skenario kebijakan", scenario_names(), **bind("scenario_name"))
            st.caption("Berlaku setelah Jalankan Simulasi ditekan.")
        with c2:
            st.selectbox("Status sumber data", SOURCE_OPTIONS, **bind("source_status"))
            st.caption("Dicatat pada setiap hasil dan laporan.")
        if s["source_status"] == "Data Aktual":
            d1, d2 = st.columns(2)
            d1.text_input("Sumber data", **bind("source_name"))
            d2.text_input("Tahun data", **bind("source_year"))

    with st.container(border=True, key="card_kondisi"):
        st.subheader("Kondisi Awal dan Waktu Analisis")
        st.caption("Nilai awal sistem dan panjang periode analisis.")
        row_of_fields(["E0", "D0", "P0", "T_end"])

    with st.container(border=True, key="card_parameter"):
        st.subheader("Parameter Model")
        st.caption("Definisi simbol tersedia melalui ikon bantuan (?).")
        row_of_fields(PARAM_KEYS)

    with st.container(border=True, key="card_risiko"):
        st.subheader("Pengaturan Analisis Risiko")
        st.caption("Gunakan nilai yang dapat direplikasi.")
        row_of_fields(["n_sim", "conf", "seed"], per_row=3)
        st.selectbox("Distribusi ketidakpastian", list(DIST_OPTIONS.keys()),
                     format_func=lambda k: DIST_OPTIONS[k], **bind("dist_kind"))
        st.caption("Nilai parameter acak tidak negatif dan tetap dalam rentang parameter "
                   "(untuk Normal terpotong).")
        with st.expander("Ketidakpastian parameter (σ)"):
            row_of_fields(SIGMA_KEYS, per_row=3)

        st.divider()
        st.toggle("Mode Eksplorasi Cepat dengan Slider", **bind("quick_mode"),
                  help="Opsional. Slider selalu tersinkron dengan kotak angka; hasil tetap "
                       "dihitung hanya saat Jalankan Simulasi ditekan.")
        if s["quick_mode"]:
            cols = st.columns(2)
            for i, key in enumerate(PARAM_KEYS):
                sp = FIELD_SPECS[key]
                sync_slider_from_text(key)
                with cols[i % 2]:
                    st.slider(f"{sp['label']}", float(sp["min"]), float(sp["max"]),
                              step=float(sp["step"]), key=f"sl_{key}",
                              on_change=slider_changed, args=(key,))

with right:
    with st.container(border=True):
        st.markdown("##### Konfigurasi Aktif")

        def kv(k, v):
            """Baris "nama … nilai" untuk panel Konfigurasi Aktif (HTML)."""
            return ('<div style="display:flex;justify-content:space-between;align-items:baseline;gap:12px;'
                    f'padding:4px 0;font-size:13px"><span style="color:#5C6B80">{k}</span>'
                    f'<strong style="text-align:right">{v}</strong></div>')

        st.markdown(
            kv("Skenario", s["scenario_name"])
            + kv("Periode", f"0–{cfg['T_end']} tahun" if cfg else "—")
            + kv("Iterasi risiko", id_number(cfg["n_sim"], 0) if cfg else "—")
            + kv("Tingkat keyakinan", f"{int(round(cfg['conf'] * 100))}%" if cfg else "—")
            + kv("Sumber data", s["source_status"]),
            unsafe_allow_html=True)

        st.divider()
        st.markdown("##### Cara Kerja")
        st.markdown(_FLOW, unsafe_allow_html=True)

        st.divider()
        st.markdown("##### Pratinjau Hasil")
        run = get_run()
        if run is None:
            st.caption("Hasil muncul setelah simulasi dijalankan, lengkap dengan satuan dan "
                       "skenario aktif.")
            vals = {k: "—" for k in ("var", "cvar", "E", "D", "P")}
            conf_txt = "95"
        else:
            conf_txt = str(int(round(run["config"]["conf"] * 100)))
            vals = {"var": id_number(run["var"]), "cvar": id_number(run["cvar"]),
                    "E": id_number(run["E"][-1]), "D": id_number(run["D"][-1]),
                    "P": id_number(run["P"][-1])}
            if status == "stale":
                st.caption("Hasil usang: input berubah sejak simulasi terakhir.")
            else:
                st.caption(f"Skenario aktif: {run['config']['scenario']} · "
                           f"periode 0–{run['config']['T_end']} tahun")
        L_unit, E_unit = VARIABLE_UNITS["L"], VARIABLE_UNITS["E"]
        tiles = [
            tile("Indeks Risiko", "Belum tersedia", "segera hadir", small=True),
            tile(f"VaR {conf_txt}%", vals["var"], L_unit),
            tile(f"CVaR {conf_txt}%", vals["cvar"], L_unit),
            tile("Energi akhir, E(T)", vals["E"], E_unit),
            tile("Permintaan akhir, D(T)", vals["D"], E_unit),
            tile("Harga akhir, P(T)", vals["P"], VARIABLE_UNITS["P"]),
        ]
        grid = "".join(tiles)
        st.markdown(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));'
                    f'gap:10px;padding-bottom:16px">{grid}</div>', unsafe_allow_html=True)

with st.container(border=True):
    b1, b2, b3 = st.columns([4, 1, 1])
    with b1:
        if errors:
            st.markdown(f":red[**✕ {n_err} input perlu diperbaiki sebelum simulasi dapat dijalankan.**]")
        else:
            st.markdown(":green[**✓ Semua input valid**] · Konfigurasi tersimpan selama sesi")
    reset_clicked = b2.button("Kembalikan ke Nilai Awal", width="stretch")
    run_clicked = b3.button("Jalankan Simulasi", type="primary", width="stretch",
                            disabled=bool(errors))

if reset_clicked:
    request_reset()
    st.rerun()
if run_clicked:
    with st.spinner("Menjalankan simulasi…"):
        execute_run()
    s["_just_ran"] = True
    st.rerun()

with st.expander("💾 Skenario Kustom"):
    new_name = st.text_input("Nama skenario kustom", key="_custom_name")
    if st.button("Simpan setup saat ini", key="_custom_save"):
        if new_name.strip():
            save_custom_scenario(new_name.strip())
            st.success(f"Skenario kustom '{new_name.strip()}' disimpan.")
        else:
            st.error("Nama skenario tidak boleh kosong.")
    saved = s["custom_scenarios"]
    if saved:
        chosen = st.selectbox("Skenario kustom tersimpan", list(saved.keys()), key="_custom_pick")
        m1, m2 = st.columns(2)
        if m1.button("Muat", key="_custom_load", width="stretch"):
            request_set(dict(saved[chosen]))
            st.rerun()
        if m2.button("Hapus", key="_custom_del", width="stretch"):
            del s["custom_scenarios"][chosen]
            st.rerun()
    st.caption("Skenario kustom hidup selama sesi ini saja (hilang kalau server di-restart). "
               "Memuat skenario hanya mengisi input; hasil baru muncul setelah Jalankan Simulasi.")

with st.expander("📥 Impor parameter dari xlsx"):
    st.caption("Gunakan file hasil Unduh Laporan (sheet 'Parameter'). Semua nilai divalidasi; "
               "bila ada yang salah, tidak ada yang diterapkan. Hasil baru muncul setelah Jalankan.")
    up = st.file_uploader("Pilih file .xlsx", type=["xlsx"], key="_import_file")
    if up is not None and st.button("Terapkan impor", key="_import_apply"):
        updates, import_errors = parse_import_workbook(up)
        if import_errors:
            for e in import_errors:
                st.error(e)
        else:
            request_set(updates)
            st.rerun()

with st.expander("📚 Dokumentasi parameter & intervensi skenario"):
    st.markdown("**Nilai awal kondisi**")
    st.dataframe(pd.DataFrame([
        {"Variabel": m["label"], "Nilai Bawaan": id_number(m["default"]), "Satuan": m["unit"],
         "Jenis Data": DATA_TYPE_LABEL, "Sumber": SOURCE_LABEL} for m in Y0_META.values()
    ]), hide_index=True)

    st.markdown("**Parameter model & horizon**")
    rows = []
    for k, m in PARAM_META.items():
        dec = 0 if isinstance(m["default"], int) else (3 if m["default"] < 1 else 2)
        rows.append({"Parameter": m["label"], "Nilai Bawaan": id_number(m["default"], dec),
                     "Satuan": m["unit"], "Rentang Nilai": range_text(k if k in FIELD_SPECS else "T_end"),
                     "Jenis Data": DATA_TYPE_LABEL, "Sumber": SOURCE_LABEL})
    st.dataframe(pd.DataFrame(rows), hide_index=True)

    st.markdown("**Besar intervensi per skenario**")
    inter = []
    for name, override in SCENARIOS.items():
        if not override:
            inter.append({"Skenario": name, "Intervensi": "Tidak ada (baseline)"})
        else:
            parts = [f"{OVERRIDE_LABELS.get(k, k)} = {id_number(v, 0 if isinstance(v, int) else 2)}"
                     for k, v in override.items()]
            inter.append({"Skenario": name, "Intervensi": ", ".join(parts)})
    st.dataframe(pd.DataFrame(inter), hide_index=True)

    st.markdown("**Satuan variabel keadaan**")
    st.dataframe(pd.DataFrame([
        {"Variabel": n, "Satuan": VARIABLE_UNITS[k]}
        for n, k in (("t", "t"), ("E(t)", "E"), ("D(t)", "D"), ("P(t)", "P"), ("L(t)", "L"))
    ]), hide_index=True)
