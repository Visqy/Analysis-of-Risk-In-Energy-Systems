import pytest

from core.inputs import build_config, validate_all
from core.run import config_key
from core.state import DEFAULT_DIST
from tests.conftest import (
    RESULT_PAGES, click, make_app, open_data_page, page_texts, ran_app, run_button, set_text,
)

pytestmark = pytest.mark.slow


def _no_exception(at):
    assert not at.exception, [e.value for e in at.exception]


def _status(at):
    """'fresh' bila input sekarang sama dengan config run terakhir, selain itu 'stale'."""
    s = at.session_state
    raw = {k[3:]: s[k] for k in s.filtered_state if k.startswith("in_")}
    values, errors = validate_all(raw)
    assert not errors
    source = {"status": s["source_status"], "name": s["source_name"].strip(),
              "year": s["source_year"].strip()}
    cfg = build_config(values, s["scenario_name"], DEFAULT_DIST, source)
    return "fresh" if config_key(cfg) == s["last_run"]["config_key"] else "stale"


@pytest.mark.parametrize("page", RESULT_PAGES)
def test_halaman_hasil_kosong_sebelum_run(page):
    at = make_app().switch_page(page).run()
    _no_exception(at)
    assert any("Belum ada hasil" in i.value for i in at.info)


def test_halaman_data_awal_tanpa_error():
    at = open_data_page(make_app())
    _no_exception(at)
    assert not run_button(at).disabled
    assert at.session_state["last_run"] is None


def test_input_tidak_valid_menonaktifkan_tombol():
    at = open_data_page(make_app())
    set_text(at, "E0", "abc")
    assert run_button(at).disabled
    assert any("Harus berupa angka" in t for t in page_texts(at))
    set_text(at, "E0", "60,5")
    assert not run_button(at).disabled


def test_run_mengisi_semua_halaman():
    at = ran_app()
    _no_exception(at)
    for page in RESULT_PAGES:
        at = at.switch_page(page).run()
        _no_exception(at)
        assert not any("Belum ada hasil" in i.value for i in at.info), page


def test_ubah_input_membuat_hasil_usang_tanpa_mengubah_hasil():
    at = ran_app()
    assert _status(at) == "fresh"
    before = (at.session_state["last_run"]["total_loss"], at.session_state["last_run"]["var"])
    set_text(at, "kappa", "3")
    assert _status(at) == "stale"
    run = at.session_state["last_run"]
    assert (run["total_loss"], run["var"]) == before


def test_dropdown_skenario_tidak_mengubah_hasil_sebelum_run():
    at = ran_app()
    before = at.session_state["last_run"]["config"]["scenario"]
    at.selectbox(key="w_scenario_name").select("Subsidi Energi").run()
    assert at.session_state["scenario_name"] == "Subsidi Energi"
    assert at.session_state["last_run"]["config"]["scenario"] == before
    click(at, "Jalankan")
    assert at.session_state["last_run"]["config"]["scenario"] == "Subsidi Energi"


# Atur Ulang & Muat skenario kustom diuji di tests/core/test_state.py:
# AppTest mempertahankan trigger tombol dan nilai widget saat st.rerun(), sehingga
# kedua alur itu tidak bisa ditiru dengan benar di sini (di browser asli berfungsi).


def test_laporan_punya_tombol_unduh_setelah_run():
    at = ran_app().switch_page("pages/laporan.py").run()
    _no_exception(at)
    assert at.get("download_button")


def test_status_sumber_data_muncul_di_strip_dan_laporan():
    at = open_data_page(make_app())
    assert not any("Tahun data" in x for x in page_texts(at))  # hanya muncul untuk Data Aktual
    at.selectbox(key="w_source_status").select("Data Aktual").run()
    at.text_input(key="w_source_name").set_value("Statistik PLN").run()
    at.text_input(key="w_source_year").set_value("2024").run()
    at.text_input(key="w_in_n_sim").set_value("100").run()
    click(at, "Jalankan")
    src = at.session_state["last_run"]["config"]["source"]
    assert src == {"status": "Data Aktual", "name": "Statistik PLN", "year": "2024"}
    at = at.switch_page("pages/dashboard.py").run()
    teks = " ".join(m.value for m in at.markdown)
    assert "Sumber data" in teks and "Data Aktual (Statistik PLN 2024)" in teks
    assert "ARIES v0.1" not in teks


def test_label_tombol_dan_keterangan_input():
    at = open_data_page(make_app())
    labels = [b.label for b in at.button]
    assert "Jalankan Simulasi" in labels and "Kembalikan ke Nilai Awal" in labels
    captions = [c.value for c in at.caption]
    assert any(c == "Rentang valid: 0,00–500,00" for c in captions)
    # keterangan singkat digabung ke tooltip bersama definisi simbol
    e0 = at.text_input(key="w_in_E0")
    assert "Kapasitas energi pada awal periode" in e0.help and "dE" in e0.help


def test_peringkat_tanpa_kartu_terpisah_dan_tanpa_pilihan_distribusi():
    at = ran_app()
    at = at.switch_page("pages/rekomendasi.py").run()
    teks = " ".join(m.value for m in at.markdown)
    assert "Skenario dengan Kerugian Terendah" not in teks
    assert "skenario dengan kerugian terendah berdasarkan model saat ini" in teks
    assert not at.success
    at = at.switch_page("pages/data_parameter.py").run()
    assert not any(s.label == "Distribusi ketidakpastian" for s in at.selectbox)


def test_peringkat_panel_pertimbangan_expander_tertutup_dan_catatan_baru():
    at = ran_app()
    at = at.switch_page("pages/rekomendasi.py").run()
    ex = [e for e in at.expander if e.label == "Pertimbangan Implementasi Kebijakan"]
    assert len(ex) == 1 and not ex[0].proto.expanded
    teks = " ".join(c.value for c in at.caption)
    assert "dihitung berdasarkan total kerugian dan risiko (CVaR)" in teks
    assert "tidak digunakan dalam pemeringkatan" in teks
    assert "Belum dimodelkan" not in " ".join(str(d.value) for d in at.dataframe)


def test_identitas_institusi_di_footer_dua_kolom():
    at = make_app()
    footer = [m.value for m in at.markdown if "class=\"aries-footer\"" in m.value]
    assert len(footer) == 1
    f = footer[0]
    assert "Logo FMIPA Unpad" in f and "Departemen Matematika" in f
    assert "Fakultas Matematika dan Ilmu Pengetahuan Alam" in f and "Universitas Padjadjaran" in f
    assert "ARIES v0.1 – Prototipe Penelitian" in f
    at = at.switch_page("pages/dashboard.py").run()
    assert not any("aries-institution" in m.value and "aries-footer" not in m.value for m in at.markdown)
