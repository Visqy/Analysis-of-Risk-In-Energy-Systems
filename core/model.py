"""
ARIES modeling engine — persis sama dengan notebook riset
(docs/Copy_of_draft_awal_dss.ipynb, cell 3 & 5). Jangan ubah formula di
sini tanpa diskusi dengan user.
"""

import numpy as np
from scipy.integrate import odeint

_trapz = getattr(np, "trapezoid", None) or np.trapz
trapz = _trapz  # alias publik untuk dipakai modul lain


def investment_function(t, params):
    """I(t): laju investasi infrastruktur energi."""
    I0 = params["I0"]
    ramp = params.get("I_ramp", 0.0)
    step_t = params.get("I_step_t", None)
    step_val = params.get("I_step_val", 0.0)
    I_t = I0 + ramp * t
    if step_t is not None and t >= step_t:
        I_t += step_val
    return max(I_t, 0.0)


def activity_function(t, params):
    """G(t): tingkat aktivitas ekonomi (pertumbuhan eksponensial)."""
    G0 = params["G0"]
    g_rate = params.get("g_rate", 0.0)
    return G0 * np.exp(g_rate * t)


def energy_economy_ode(y, t, params):
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
    sol = odeint(energy_economy_ode, y0, t, args=(params,))
    E, D, P = sol[:, 0], sol[:, 1], sol[:, 2]
    L = params["kappa"] * np.maximum(0.0, D - E)
    return E, D, P, L


def equilibrium_and_stability(params):
    """Asumsi I(t)=I0, G(t)=G0 konstan (rata-rata jangka panjang)."""
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
    _, _, _, L = simulate(params, y0, t)
    return _trapz(L, t)


def monte_carlo_risk(base_params, y0, t, uncertain, n_sim=500, seed=42):
    rng = np.random.default_rng(seed)
    losses = np.zeros(n_sim)
    for i in range(n_sim):
        p = dict(base_params)
        for name, spec in uncertain.items():
            kind = spec[0]
            if kind == "normal":
                _, mean, std = spec
                p[name] = max(rng.normal(mean, std), 1e-6)
            elif kind == "uniform":
                _, low, high = spec
                p[name] = rng.uniform(low, high)
        losses[i] = total_economic_loss(p, y0, t)
    return losses


def risk_metrics(losses, conf=0.95):
    var = np.percentile(losses, conf * 100)
    tail = losses[losses >= var]
    cvar = tail.mean() if len(tail) > 0 else var
    return var, cvar


def sensitivity_analysis(base_params, y0, t, param_names, pct=0.2):
    base_loss = total_economic_loss(base_params, y0, t)
    results = []
    for name in param_names:
        p_low = dict(base_params); p_low[name] = base_params[name] * (1 - pct)
        p_high = dict(base_params); p_high[name] = base_params[name] * (1 + pct)
        results.append((name, total_economic_loss(p_low, y0, t), base_loss,
                         total_economic_loss(p_high, y0, t)))
    return results
