"""Regresi: key widget dibuang Streamlit saat halaman lain aktif; nilai input harus bertahan."""

import pytest

from tests.conftest import make_app, open_data_page, ran_app, set_text

pytestmark = pytest.mark.slow


def test_input_bertahan_saat_pindah_halaman():
    at = open_data_page(make_app())
    set_text(at, "E0", "60,5")
    at = at.switch_page("pages/dashboard.py").run()
    assert at.session_state["in_E0"] == "60,5"
    at = at.switch_page("pages/data_parameter.py").run()
    assert at.text_input(key="w_in_E0").value == "60,5"


def test_pilihan_dropdown_dan_sumber_bertahan():
    at = open_data_page(make_app())
    at.selectbox(key="w_scenario_name").select("Subsidi Energi").run()
    at.selectbox(key="w_source_status").select("Data Aktual").run()
    at = at.switch_page("pages/rekomendasi.py").run()
    at = at.switch_page("pages/data_parameter.py").run()
    assert at.selectbox(key="w_scenario_name").value == "Subsidi Energi"
    assert at.selectbox(key="w_source_status").value == "Data Aktual"


def test_tidak_usang_setelah_pindah_halaman_tanpa_ubah_input():
    at = ran_app(E0="60,5")
    for page in ("pages/dashboard.py", "pages/dinamika_sistem.py", "pages/data_parameter.py"):
        at = at.switch_page(page).run()
    assert at.session_state["in_E0"] == "60,5"
    assert not any("berubah sejak" in w.value for w in at.warning)


def test_slider_dan_kotak_angka_sinkron_tanpa_run():
    at = open_data_page(make_app())
    at.toggle(key="w_quick_mode").set_value(True).run()
    at.slider(key="sl_I0").set_value(7.0).run()
    assert at.session_state["in_I0"] == "7,00"
    set_text(at, "I0", "12")
    assert at.slider(key="sl_I0").value == 12.0
    assert at.session_state["last_run"] is None


def test_filter_skenario_perbandingan_bertahan_saat_pindah_halaman():
    at = ran_app().switch_page("pages/perbandingan_skenario.py").run()
    pilihan = ["Baseline (Business as Usual)", "Subsidi Energi"]
    at.multiselect(key="w_selected_scenarios").set_value(pilihan).run()
    assert at.session_state["selected_scenarios"] == pilihan
    at = at.switch_page("pages/rekomendasi.py").run()
    at = at.switch_page("pages/perbandingan_skenario.py").run()
    assert at.multiselect(key="w_selected_scenarios").value == pilihan
