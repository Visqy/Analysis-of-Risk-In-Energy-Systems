"""Tampilan hasil utama: judul peringkat, tanpa indeks risiko, catatan prototipe, implikasi."""

from pathlib import Path

import pytest

from core.interpretation import CATATAN_PROTOTIPE
from tests.conftest import RESULT_PAGES, ROOT, page_texts, ran_app

pytestmark = pytest.mark.slow

PAGES_DENGAN_CATATAN = ["pages/dashboard.py", "pages/dinamika_sistem.py",
                        "pages/analisis_risiko.py", "pages/perbandingan_skenario.py",
                        "pages/rekomendasi.py"]


def test_navigasi_peringkat_skenario_tanpa_kestabilan():
    app = Path(ROOT, "app.py").read_text(encoding="utf-8")
    nav = app[app.index("st.navigation"):app.index("st.sidebar.markdown")]
    assert 'title="Peringkat Skenario"' in nav and "Rekomendasi" not in nav
    assert "analisis_kestabilan" not in nav


def test_judul_halaman_peringkat():
    at = ran_app().switch_page("pages/rekomendasi.py").run()
    assert [h.value for h in at.header] == ["Peringkat Skenario Berdasarkan Total Kerugian"]


def test_tidak_ada_indeks_risiko_atau_segera_hadir():
    at = ran_app()
    for page in ("pages/data_parameter.py", *RESULT_PAGES):
        at = at.switch_page(page).run()
        text = " ".join(page_texts(at)).lower()
        assert "indeks risiko" not in text and "segera hadir" not in text, page


def test_catatan_prototipe_di_halaman_hasil():
    at = ran_app()
    for page in PAGES_DENGAN_CATATAN:
        at = at.switch_page(page).run()
        assert any(CATATAN_PROTOTIPE in c.value for c in at.caption), page


def test_bagian_implikasi_di_dinamika_sistem():
    at = ran_app().switch_page("pages/dinamika_sistem.py").run()
    assert any("Implikasi bagi Pengambil Keputusan" in m.value for m in at.markdown)
    isi = " ".join(m.value for m in at.markdown)
    assert "**Temuan:**" in isi and "**Makna:**" in isi and "**Implikasi:**" in isi


def test_ringkasan_dan_implikasi_di_atas_grafik_dinamika():
    at = ran_app().switch_page("pages/dinamika_sistem.py").run()
    judul = [m.value for m in at.markdown if m.value.startswith("#####")]
    assert judul[0] == "##### Ringkasan"
    assert judul[1] == "##### Implikasi bagi Pengambil Keputusan"
    assert judul.index("##### Implikasi bagi Pengambil Keputusan") < next(
        i for i, j in enumerate(judul) if "Kapasitas" in j and "Permintaan" in j)
    assert len(at.metric) == 3


def test_interpretasi_dalam_card_tiga_baris_terpisah():
    at = ran_app().switch_page("pages/dinamika_sistem.py").run()
    isi = [m.value for m in at.markdown if m.value.startswith("**Temuan:**")]
    assert len(isi) == 3
    for teks in isi:
        bagian = teks.split("\n\n")
        assert [b.split(":**")[0] for b in bagian] == ["**Temuan", "**Makna", "**Implikasi"]


def test_dua_tabel_peringkat_berjudul_jelas():
    at = ran_app().switch_page("pages/rekomendasi.py").run()
    judul = [m.value for m in at.markdown if m.value.startswith("#####")]
    assert "##### Peringkat Berdasarkan Total Kerugian" in judul
    assert "##### Peringkat Berdasarkan Risiko (CVaR 95%)" in judul
    assert judul.index("##### Peringkat Berdasarkan Total Kerugian") < judul.index(
        "##### Peringkat Berdasarkan Risiko (CVaR 95%)")
    assert len(at.dataframe) == 3  # total kerugian, risiko, pertimbangan implementasi
    assert any(m.value.startswith("**Temuan:**") for m in at.markdown)
