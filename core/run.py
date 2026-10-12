"""Satu kali "Jalankan Simulasi": hitung semua hasil dalam satu snapshot.

Snapshot (`run_simulation`) memuat hasil simulasi, kestabilan, Monte Carlo,
sensitivitas, peringkat skenario, serta metadata reproduksibilitas (skenario,
parameter, iterasi, seed, tanggal analisis, versi model, sumber data).
"""

import json
from datetime import datetime

import numpy as np

from core.model import (
    simulate, equilibrium_and_stability, monte_carlo_risk, risk_metrics,
    sensitivity_analysis, trapz,
)
from core.recommendation import compute_ranking
from core.scenarios import BASELINE_NAME, DEFAULT_PARAMS, SCENARIOS, PARAM_META

MODEL_VERSION = "ARIES v0.1"
N_POINTS = 300
SENS_PARAMS = ["delta", "alpha", "beta", "gamma", "kappa", "I0", "g_rate"]


def config_key(cfg):
    """String kanonik dari `cfg` (JSON terurut); dipakai mendeteksi hasil usang."""
    return json.dumps(cfg, sort_keys=True)


def _uncertain(cfg, active):
    unc = {}
    for name, sd in cfg["sd"].items():
        mean = active[name]
        if cfg["dist"] == "truncnormal":
            unc[name] = ("truncnormal", mean, sd, PARAM_META[name]["min"], PARAM_META[name]["max"])
        else:
            unc[name] = ("normal", mean, sd)
    return unc


def compute_risk_ranking(cfg, base, t, active_name, active_losses):
    """Peringkat semua skenario berdasarkan risiko (CVaR) dari Monte Carlo per skenario.

    Tiap skenario dijalankan dengan jumlah iterasi, seed, distribusi, dan σ yang
    sama seperti analisis utama; skenario aktif memakai ulang `active_losses`
    sehingga angkanya identik dengan hasil utama.

    Args:
        cfg: konfigurasi run. base: parameter dasar. t: grid waktu.
        active_name: nama skenario aktif. active_losses: total kerugian per iterasi.

    Returns:
        (rows, baseline_cvar): `rows` urut dari CVaR terkecil, tiap elemen dict
        {"Skenario", "mean", "var", "cvar", "cvar_delta", "cvar_pct", "rank"};
        cvar_delta/cvar_pct = penurunan CVaR terhadap baseline.
    """
    rows = []
    for name, override in SCENARIOS.items():
        if name == active_name:
            losses = active_losses
        else:
            p = dict(base)
            p.update(override)
            losses = monte_carlo_risk(p, cfg["y0"], t, _uncertain(cfg, p),
                                      n_sim=cfg["n_sim"], seed=cfg["seed"])
        var, cvar = risk_metrics(losses, cfg["conf"])
        rows.append({"Skenario": name, "mean": float(np.mean(losses)),
                     "var": float(var), "cvar": float(cvar)})
    baseline_cvar = next(r["cvar"] for r in rows if r["Skenario"] == BASELINE_NAME)
    for r in rows:
        r["cvar_delta"] = baseline_cvar - r["cvar"]
        r["cvar_pct"] = (r["cvar_delta"] / baseline_cvar * 100) if baseline_cvar else 0.0
    rows.sort(key=lambda r: r["cvar"])
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows, baseline_cvar


def run_simulation(cfg):
    """Hitung seluruh hasil untuk konfigurasi `cfg` (lihat `inputs.build_config`).

    Grid waktu: `N_POINTS` titik dari 0 sampai `T_end`. Skenario aktif
    menimpa parameter dasar; peringkat dihitung untuk semua skenario terhadap
    baseline.

    Returns:
        dict: config, config_key, meta {date, model_version}, t, E, D, P, L,
        total_loss, active_params, base_params, stab (kestabilan), uncertain
        (spesifikasi sampling), losses (total kerugian per iterasi), var, cvar,
        sens (sensitivitas), ranking (berdasarkan total kerugian), baseline_loss,
        ranking_risk (berdasarkan CVaR), baseline_cvar.
    """
    y0 = cfg["y0"]
    t = np.linspace(0, cfg["T_end"], N_POINTS)

    base = dict(DEFAULT_PARAMS)
    base.update(cfg["params"])
    active = dict(base)
    active.update(SCENARIOS[cfg["scenario"]])

    E, D, P, L = simulate(active, y0, t)
    stab = equilibrium_and_stability(active)

    unc = _uncertain(cfg, active)
    losses = monte_carlo_risk(active, y0, t, unc, n_sim=cfg["n_sim"], seed=cfg["seed"])
    var, cvar = risk_metrics(losses, cfg["conf"])
    sens = sensitivity_analysis(active, y0, t, SENS_PARAMS)
    ranking, baseline_loss = compute_ranking(base, t, y0)
    ranking_risk, baseline_cvar = compute_risk_ranking(cfg, base, t, cfg["scenario"], losses)

    return {
        "config": cfg,
        "config_key": config_key(cfg),
        "meta": {
            "date": datetime.now().isoformat(timespec="seconds"),
            "model_version": MODEL_VERSION,
        },
        "t": t, "E": E, "D": D, "P": P, "L": L,
        "total_loss": float(trapz(L, t)),
        "active_params": active,
        "base_params": base,
        "stab": stab,
        "uncertain": unc,
        "losses": losses, "var": float(var), "cvar": float(cvar),
        "sens": sens,
        "ranking": ranking, "baseline_loss": baseline_loss,
        "ranking_risk": ranking_risk, "baseline_cvar": baseline_cvar,
    }
