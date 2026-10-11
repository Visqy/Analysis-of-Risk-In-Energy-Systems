"""Validasi perhitungan manual: hasil program sesuai hitungan tangan pada satu contoh uji.

Contoh uji (parameter bawaan, skenario Baseline, T = 15 tahun):
    E(t) = I0/δ + (E(0) − I0/δ)·e^(−δt), dengan I0/δ = 5/0,08 = 62,5
    E(15) = 62,5 − 12,5·e^(−1,2) = 62,5 − 12,5 × 0,301194 = 58,7351 ≈ 58,74
    E* = 62,5; P* = αG0/β = 1,2·10/0,5 = 24
    ω = √(βγ) = √0,15 = 0,3873 per tahun; periode 2π/ω = 16,22 tahun
"""

import numpy as np
import pytest

from core.model import equilibrium_and_stability, simulate
from core.scenarios import DEFAULT_PARAMS, DEFAULT_Y0

P = DEFAULT_PARAMS  # I0=5, delta=0,08, alpha=1,2, beta=0,5, gamma=0,3, G0=10, g=0,05, kappa=2


def closed_form_E(t, E0=DEFAULT_Y0[0]):
    """dE/dt = I0 - delta*E  ->  E(t) = I0/delta + (E0 - I0/delta) * exp(-delta*t)."""
    e_star = P["I0"] / P["delta"]
    return e_star + (E0 - e_star) * np.exp(-P["delta"] * t)


def test_E_sama_dengan_solusi_tertutup():
    t = np.linspace(0, 15, 300)
    E, *_ = simulate(P, DEFAULT_Y0, t)
    assert np.allclose(E, closed_form_E(t), rtol=1e-5, atol=1e-6)


def test_hitung_tangan_E_tahun_ke_15():
    # E(15) = 62,5 - 12,5 * e^(-1,2) = 62,5 - 12,5 * 0,301194 = 58,7351
    manual = 62.5 - 12.5 * 0.301194
    t = np.linspace(0, 15, 300)
    E, *_ = simulate(P, DEFAULT_Y0, t)
    assert E[-1] == pytest.approx(manual, abs=1e-3)
    assert round(float(E[-1]), 2) == 58.74  # angka yang tampil di aplikasi


def test_hitung_tangan_ekuilibrium_dan_frekuensi():
    stab = equilibrium_and_stability(P)
    assert stab["E_star"] == pytest.approx(5 / 0.08)            # 62,5
    assert stab["P_star"] == pytest.approx(1.2 * 10 / 0.5)      # 24
    omega = (0.5 * 0.3) ** 0.5                                   # 0,3873
    assert stab["osc_freq"] == pytest.approx(omega)
    assert 2 * np.pi / omega == pytest.approx(16.22, abs=0.005)  # periode (tahun)


def test_kerugian_nol_saat_kapasitas_selalu_melebihi_permintaan():
    # L = kappa * max(0, D - E): E0 besar & permintaan kecil -> tidak ada defisit di awal
    t = np.linspace(0, 2, 50)
    _, D, _, L = simulate(P, [500.0, 1.0, 0.0], t)
    assert np.all(L == 0.0) and np.all(D < 500.0)
