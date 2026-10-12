import numpy as np
import pytest

from core.inputs import DISPLAY_NAME
from core.interpretation import (
    interpret_capacity_demand, interpret_comparison, interpret_implications, interpret_loss,
    interpret_perturbation, interpret_price, interpret_risk, interpret_tornado,
)

T = np.linspace(0, 15, 300)


def _tmi_parts(text):
    assert text.startswith("**Temuan:**") and "**Makna:**" in text and "**Implikasi:**" in text
    return text


def test_kapasitas_permintaan_rentang_defisit():
    E = np.full_like(T, 50.0)
    D = 40 + 20 * np.sin(np.pi * T / 15)          # melampaui E di tengah horizon
    text = _tmi_parts(interpret_capacity_demand(T, E, D))
    assert "melampaui kapasitas E(t) pada tahun ke-" in text and " sampai tahun ke-" in text
    assert "sebelum tahun ke-" in text and "dapat dipertimbangkan" in text


def test_kapasitas_permintaan_dua_periode_dengan_pemulihan():
    T2 = np.linspace(0, 15, 151)
    E = np.full_like(T2, 100.0)
    D = np.where(T2 < 2, 90.0, np.where(T2 < 6, 106.0, np.where(T2 < 12, 90.0, 90.0 + 12 * (T2 - 12))))
    text = _tmi_parts(interpret_capacity_demand(T2, E, D))
    assert "tahun ke-2 sampai tahun ke-5,9 dan tahun ke-13 sampai tahun ke-15" in text
    assert "sebelum tahun ke-2 dapat dipertimbangkan" in text


def test_selisih_sangat_kecil_diabaikan():
    E = np.full_like(T, 100.0)
    assert "tidak melampaui" in interpret_capacity_demand(T, E, E * 1.005)


def test_kapasitas_permintaan_tanpa_defisit_sejak_awal_dan_sampai_akhir():
    E = np.full_like(T, 50.0)
    assert "tidak melampaui" in interpret_capacity_demand(T, E, np.full_like(T, 40.0))
    sejak_awal = interpret_capacity_demand(T, E, np.full_like(T, 60.0))
    assert "sejak awal horizon" in sejak_awal
    assert "sesegera mungkin" in sejak_awal


def test_harga_jalur_dan_tekanan_pasokan():
    E = np.full_like(T, 50.0)
    D = np.where(T > 3, 60.0, 40.0)
    P = 20 + 30 * (T / 15)
    text = _tmi_parts(interpret_price(T, P, E, D))
    assert "tekanan harga" in text and "perlu dipertimbangkan sebelum kenaikan harga" in text
    datar = interpret_price(T, np.full_like(T, 20.0), E, np.full_like(T, 40.0))
    assert "relatif stabil" in datar and "pemantauan harga" in datar


def test_kerugian_muncul_puncak_dan_kembali_nol():
    L = np.where((T > 2.2) & (T < 14.1), np.sin(np.pi * (T - 2.2) / 11.9) * 31, 0.0)
    text = _tmi_parts(interpret_loss(T, None, None, L))
    assert "muncul pada tahun ke-2,2" in text and "kembali nol" in text
    assert "batas waktu persiapan" in text


def test_kerugian_nol_dan_berlanjut():
    assert "tetap nol" in interpret_loss(T, None, None, np.zeros_like(T))
    assert "masih berlangsung" in interpret_loss(T, None, None, np.where(T > 5, 3.0, 0.0))
    assert "sejak awal horizon" in interpret_loss(T, None, None, np.full_like(T, 3.0))


def test_risiko_var_cvar_format_indonesia():
    text = _tmi_parts(interpret_risk(np.linspace(1, 100, 100), 95.05, 98.0, 95))
    assert "VaR 95% bernilai 95,05" in text and "CVaR bernilai 98,00" in text
    assert "5% kondisi terburuk" in text and "cadangan" in text


def test_tornado_urutan_tiga_teratas():
    sens = [("delta", 90, 100, 110), ("beta", 60, 100, 160), ("kappa", 95, 100, 105),
            ("gamma", 70, 100, 100)]
    text = interpret_tornado(sens, DISPLAY_NAME)
    assert text.index("β") < text.index("γ") < text.index("δ")
    assert "κ" not in text and "kenaikan 20% menaikkan" in text
    assert "menurunkan" in interpret_tornado([("beta", 140, 100, 60)], DISPLAY_NAME)


def test_perbandingan_skenario_terendah_dan_baseline():
    t = np.linspace(0, 15, 4)
    curves = {"Baseline": np.array([0, 5, 9, 2.0]), "Subsidi": np.array([0, 2, 3, 1.0])}
    text = _tmi_parts(interpret_comparison(
        ["Baseline", "Subsidi"], [221.64, 148.95], curves, t, 221.64, "Baseline"))
    assert "skenario dengan kerugian terendah berdasarkan model saat ini" in text.lower()
    assert "Subsidi" in text and "72,69" in text and "32,80%" in text
    assert "analisis biaya, kelayakan teknis, dan dampak lainnya" in text
    base = interpret_comparison(["Baseline", "Subsidi"], [100.0, 150.0], curves, t, 100.0, "Baseline")
    assert "tidak ada skenario intervensi" in base and "dapat dipertimbangkan" in base


def test_butir_implikasi_spesifik_data():
    E = np.full_like(T, 50.0)
    D = 40 + 20 * np.sin(np.pi * T / 15)
    L = np.maximum(0.0, D - E) * 2
    P = 20 + 30 * (T / 15)
    items = interpret_implications(T, E, D, P, L)
    assert len(items) == 3
    assert all("dipertimbangkan" in i for i in items)
    assert any("tahun ke-" in i for i in items)
    assert len(interpret_implications(T, E, np.full_like(T, 40.0), np.full_like(T, 20.0),
                                      np.zeros_like(T))) == 1


def _osc(decay=0.0, growth=0.0, beta=0.5, gamma=0.3):
    w = (beta * gamma) ** 0.5
    env = np.exp(-decay * T) * np.exp(growth * T)
    dD = 3.0 * env * np.cos(w * T)
    dP = 3.0 * env * (gamma / beta) ** 0.5 * np.sin(w * T)
    return 62.5 + dD, 24.0 + dP, w, beta, gamma


@pytest.mark.parametrize("kw,expected", [
    (dict(), "tidak meluruh maupun membesar"),
    (dict(decay=0.3), "meluruh"),
    (dict(growth=0.3), "membesar"),
])
def test_gangguan_kecil_tiga_kasus(kw, expected):
    D, P, w, beta, gamma = _osc(**kw)
    text = interpret_perturbation(T, D, P, 62.5, 24.0, beta, gamma, w)
    assert text.rstrip(".").endswith(expected)
    assert "16,2 tahun" in text
    assert "tidak kembali" not in text
