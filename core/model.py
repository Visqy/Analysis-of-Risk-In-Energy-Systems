"""Mesin pemodelan ARIES: sistem dinamik energi–ekonomi, analisis kestabilan,
Monte Carlo risiko, dan analisis sensitivitas.

Variabel keadaan (semua dalam unit relatif/indeks, waktu dalam tahun):
    E(t) kapasitas energi, D(t) permintaan energi, P(t) harga energi,
    L(t) kerugian ekonomi (turunan dari D dan E).

Persamaan model:
    dE/dt = I(t) − δ·E
    dD/dt = α·G(t) − β·P
    dP/dt = γ·(D − E)
    L(t)  = κ·max(0, D − E)
    G(t)  = G₀·exp(g·t)

Berkas ini adalah sumber kebenaran rumus; tes regresi
(tests/core/test_model_regression.py) menjaga angka acuannya.
"""

import numpy as np
from scipy.integrate import odeint

_trapz = getattr(np, "trapezoid", None) or np.trapz
trapz = _trapz  # alias publik untuk dipakai modul lain


def investment_function(t, params):
    """Laju investasi infrastruktur energi I(t) pada waktu t (skalar).

    I(t) = I0 + I_ramp·t, ditambah I_step_val bila t >= I_step_t (lonjakan
    sekali waktu). Nilai dibatasi tidak negatif. Kunci opsional di `params`:
    I_ramp, I_step_t, I_step_val (default: tanpa intervensi).
    """
    I0 = params["I0"]
    ramp = params.get("I_ramp", 0.0)
    step_t = params.get("I_step_t", None)
    step_val = params.get("I_step_val", 0.0)
    I_t = I0 + ramp * t
    if step_t is not None and t >= step_t:
        I_t += step_val
    return max(I_t, 0.0)


def activity_function(t, params):
    """Aktivitas ekonomi G(t) = G0·exp(g_rate·t) pada waktu t (skalar)."""
    G0 = params["G0"]
    g_rate = params.get("g_rate", 0.0)
    return G0 * np.exp(g_rate * t)


def energy_economy_ode(y, t, params):
    """Ruas kanan sistem ODE untuk `scipy.integrate.odeint`.

    Args:
        y: [E, D, P] keadaan saat ini.
        t: waktu (tahun).
        params: dict parameter (delta, alpha, beta, gamma, I0, G0, g_rate, ...).

    Returns:
        [dE/dt, dD/dt, dP/dt].
    """
    E, D, P = y
    delta = params["delta"]; alpha = params["alpha"]
    beta = params["beta"]; gamma = params["gamma"]
    I_t = investment_function(t, params)
    G_t = activity_function(t, params)
    dE = I_t - delta * E
    dD = alpha * G_t - beta * P
    dP = gamma * (D - E)
    return [dE, dD, dP]


def simulate(params, y0, t):
    """Simulasikan sistem pada grid waktu `t` dan hitung kerugian L(t).

    Args:
        params: dict parameter model (lihat `energy_economy_ode`) plus `kappa`.
        y0: kondisi awal [E(0), D(0), P(0)].
        t: array waktu menaik (tahun).

    Returns:
        Tuple (E, D, P, L), masing-masing array sepanjang `t`.
    """
    sol = odeint(energy_economy_ode, y0, t, args=(params,))
    E, D, P = sol[:, 0], sol[:, 1], sol[:, 2]
    L = params["kappa"] * np.maximum(0.0, D - E)
    return E, D, P, L


def equilibrium_and_stability(params):
    """Titik ekuilibrium dan kestabilan lokal (berdasarkan linearisasi).

    Dengan asumsi I(t)=I0 dan G(t)=G0 konstan: E* = I0/δ, D* = E*, P* = αG0/β.
    Matriks Jacobian sistem dihitung dan eigenvalue-nya diklasifikasi dengan
    toleransi numerik 1e-9 pada bagian real: seluruhnya negatif → "STABIL";
    maksimum bagian real ≈ 0 → "MARGINAL (osilasi tak teredam)"; positif →
    "TIDAK STABIL". Subsistem (D, P) berosilasi dengan frekuensi ω = √(βγ).

    Returns:
        dict: E_star, D_star, P_star, eigvals, status, osc_freq (ω, 1/tahun),
        jacobian (array 3×3).
    """
    delta, beta, gamma = params["delta"], params["beta"], params["gamma"]
    alpha, G0, I0 = params["alpha"], params["G0"], params["I0"]

    E_star = I0 / delta
    P_star = (alpha * G0) / beta
    D_star = E_star

    J = np.array([[-delta, 0.0, 0.0],
                  [0.0, 0.0, -beta],
                  [-gamma, gamma, 0.0]])
    eigvals = np.linalg.eigvals(J)
    max_real = np.max(eigvals.real)
    if max_real < -1e-9:
        status = "STABIL"
    elif abs(max_real) <= 1e-9:
        status = "MARGINAL (osilasi tak teredam)"
    else:
        status = "TIDAK STABIL"
    return {"E_star": E_star, "D_star": D_star, "P_star": P_star,
            "eigvals": eigvals, "status": status, "osc_freq": np.sqrt(beta * gamma),
            "jacobian": J}


def total_economic_loss(params, y0, t):
    """Total kerugian ekonomi kumulatif: integral L(t) dt (aturan trapesium)."""
    _, _, _, L = simulate(params, y0, t)
    return _trapz(L, t)


def _truncated_normal(rng, mean, std, lo, hi, max_tries=100000):
    """Normal terpotong [lo, hi] lewat resampling (nilai di luar batas diundi ulang).

    Raises:
        ValueError: bila `mean` di luar [lo, hi] sehingga tidak ada undian yang lolos
            dalam `max_tries` percobaan (nilai tidak pernah dipotong ke batas).
    """
    if std <= 0:
        if not lo <= mean <= hi:
            raise ValueError(f"Nilai {mean} di luar rentang [{lo}, {hi}]")
        return mean
    for _ in range(max_tries):
        x = rng.normal(mean, std)
        if lo <= x <= hi:
            return x
    raise ValueError(f"Tidak ada undian dalam rentang [{lo}, {hi}] untuk rata-rata {mean}")


def monte_carlo_risk(base_params, y0, t, uncertain, n_sim=500, seed=42):
    """Distribusi total kerugian lewat simulasi Monte Carlo.

    Tiap iterasi mengacak parameter tidak pasti, menjalankan `simulate`, dan
    mencatat total kerugian. Hasil dapat direplikasi: `seed` yang sama
    menghasilkan urutan acak yang sama.

    Args:
        base_params: dict parameter dasar.
        y0, t: kondisi awal dan grid waktu.
        uncertain: dict nama_parameter -> spesifikasi distribusi:
            ("truncnormal", mean, std, lo, hi)  normal terpotong [lo, hi] (resampling),
            ("normal", mean, std)               normal dengan batas bawah 1e-6,
            ("uniform", low, high).
        n_sim: jumlah iterasi.
        seed: seed generator acak.

    Returns:
        Array total kerugian sepanjang `n_sim`.
    """
    rng = np.random.default_rng(seed)
    losses = np.zeros(n_sim)
    for i in range(n_sim):
        p = dict(base_params)
        for name, spec in uncertain.items():
            kind = spec[0]
            if kind == "truncnormal":
                _, mean, std, lo, hi = spec
                p[name] = _truncated_normal(rng, mean, std, lo, hi)
            elif kind == "normal":
                _, mean, std = spec
                p[name] = max(rng.normal(mean, std), 1e-6)
            elif kind == "uniform":
                _, low, high = spec
                p[name] = rng.uniform(low, high)
        losses[i] = total_economic_loss(p, y0, t)
    return losses


def risk_metrics(losses, conf=0.95):
    """VaR dan CVaR pada tingkat keyakinan `conf` (pecahan, mis. 0,95).

    VaR = persentil ke-`conf` dari `losses`; CVaR = rata-rata kerugian yang
    sama dengan atau melebihi VaR.

    Returns:
        Tuple (VaR, CVaR).
    """
    var = np.percentile(losses, conf * 100)
    tail = losses[losses >= var]
    cvar = tail.mean() if len(tail) > 0 else var
    return var, cvar


def sensitivity_analysis(base_params, y0, t, param_names, pct=0.2):
    """Sensitivitas total kerugian terhadap perubahan satu parameter ±`pct`.

    Tiap parameter diubah sendiri-sendiri (yang lain tetap) menjadi
    (1 − pct) dan (1 + pct) dari nilai dasarnya.

    Returns:
        List tuple (nama, kerugian_pada_−pct, kerugian_dasar, kerugian_pada_+pct).
    """
    base_loss = total_economic_loss(base_params, y0, t)
    results = []
    for name in param_names:
        p_low = dict(base_params); p_low[name] = base_params[name] * (1 - pct)
        p_high = dict(base_params); p_high[name] = base_params[name] * (1 + pct)
        results.append((name, total_economic_loss(p_low, y0, t), base_loss,
                         total_economic_loss(p_high, y0, t)))
    return results
