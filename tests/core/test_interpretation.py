import numpy as np
import pytest

from core.inputs import DISPLAY_NAME
from core.interpretation import (
    interpret_comparison, interpret_D, interpret_E, interpret_histogram, interpret_L,
    interpret_P, interpret_perturbation, interpret_tornado,
)

T = np.linspace(0, 15, 300)


def test_jalur_naik_terus():
    y = 50 + 8.74 * (T / 15)
    text = interpret_E(T, y)
    assert "naik dari 50,00 menjadi 58,74 pada tahun ke-15,0" in text


def test_jalur_turun_terus():
    assert "turun dari 60,00 menjadi 40,00" in interpret_E(T, 60 - 20 * (T / 15))


def test_jalur_naik_lalu_turun():
    y = 45 + 26.58 * np.sin(np.pi * T / 15 * 0.55) ** 2
    text = interpret_D(T, y)
    assert "hingga puncak" in text and "lalu turun menjadi" in text


def test_jalur_turun_lalu_naik():
    y = 20 + 31 * ((T - 2) / 13) ** 2 - 0.0
    y[T < 2] = 20 - (T[T < 2] / 2) * 1.9
    text = interpret_P(T, y)
    assert "ke minimum" in text and "lalu naik menjadi" in text


def test_jalur_datar():
    assert "relatif stabil" in interpret_E(T, np.full_like(T, 5.0))


def test_L_rentang_defisit_dan_tanpa_defisit():
    L = np.where((T > 2.2) & (T < 14.1), np.sin(np.pi * (T - 2.2) / 11.9) * 31, 0.0)
    text = interpret_L(T, None, None, L)
    assert "muncul pada tahun ke-2,2" in text and "kembali nol" in text
    assert "tetap nol" in interpret_L(T, None, None, np.zeros_like(T))
    assert "masih berlangsung" in interpret_L(T, None, None, np.where(T > 5, 3.0, 0.0))


def test_histogram_condong_kanan_dan_simetris():
    skew = np.concatenate([np.full(90, 100.0), np.full(10, 900.0)])
    assert "condong ke kanan" in interpret_histogram(skew, 900.0, 900.0, 95)
    sym = np.linspace(90, 110, 100)
    assert "simetris" in interpret_histogram(sym, 108.0, 109.0, 95)


def test_histogram_memuat_interval_var_cvar_format_indonesia():
    text = interpret_histogram(np.linspace(1, 100, 100), 95.05, 98.0, 95)
    assert "95,05" in text and "98,00" in text and "VaR 95%" in text
    assert "antara" in text


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
    text = interpret_comparison(["Baseline", "Subsidi"], [221.64, 148.95], curves, t, 221.64, "Baseline")
    assert "skenario dengan kerugian terendah berdasarkan model saat ini" in text.lower()
    assert "Subsidi" in text and "72,69" in text and "32,80%" in text
    base = interpret_comparison(["Baseline", "Subsidi"], [100.0, 150.0], curves, t, 100.0, "Baseline")
    assert "tidak ada skenario intervensi" in base


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
