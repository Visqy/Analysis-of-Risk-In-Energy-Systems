"""Ranking skenario & rekomendasi keputusan (masukan dosen §2.3).

ΔLi = L_baseline - Li
Ri  = ΔLi / L_baseline * 100%

Selalu menghitung SEMUA skenario di SCENARIOS (bukan cuma yang dipilih di
multiselect sidebar) karena rekomendasi butuh baseline sebagai acuan yang
konsisten, terlepas dari apa yang sedang ditampilkan di halaman
Perbandingan Skenario.
"""

from core.model import simulate, trapz as _trapz
from core.scenarios import SCENARIOS, BASELINE_NAME, DEFAULT_Y0


def compute_ranking(base_params, t):
    """Kembalikan list of dict (sudah diurutkan dari kerugian terkecil,
    dengan field 'rank' 1..N) dan total kerugian baseline."""
    rows = []
    for name, override in SCENARIOS.items():
        p = dict(base_params); p.update(override)
        _, _, _, L = simulate(p, DEFAULT_Y0, t)
        rows.append({"Skenario": name, "loss": _trapz(L, t)})

    baseline_loss = next(r["loss"] for r in rows if r["Skenario"] == BASELINE_NAME)
    for r in rows:
        r["delta"] = baseline_loss - r["loss"]
        r["pct"] = (r["delta"] / baseline_loss * 100) if baseline_loss else 0.0

    rows.sort(key=lambda r: r["loss"])
    for i, r in enumerate(rows, start=1):
        r["rank"] = i
    return rows, baseline_loss


def get_recommendation(rows):
    """rank-1 sebagai kandidat rekomendasi utama. beats_baseline=False kalau
    baseline sendiri yang jadi rank-1 (tidak ada skenario yang lebih baik)."""
    top = rows[0]
    beats_baseline = top["Skenario"] != BASELINE_NAME
    return top, beats_baseline
