"""Peringkat skenario dan rekomendasi berdasarkan total kerugian terendah.

Untuk tiap skenario i:
    ΔL_i = L_baseline − L_i            (pengurangan kerugian)
    R_i  = ΔL_i / L_baseline × 100%    (persentase penurunan)

Selalu menghitung SEMUA skenario di `SCENARIOS`, bukan hanya yang sedang
ditampilkan di halaman Perbandingan Skenario, supaya baseline menjadi acuan
yang konsisten. Kriteria tunggal: total kerugian ekonomi paling rendah.
"""

from core.model import simulate, trapz as _trapz
from core.scenarios import SCENARIOS, BASELINE_NAME, DEFAULT_Y0


def compute_ranking(base_params, t, y0=None):
    """Hitung dan urutkan semua skenario berdasarkan total kerugian.

    Args:
        base_params: parameter dasar (di-override per skenario).
        t: grid waktu.
        y0: kondisi awal [E0, D0, P0]; default `DEFAULT_Y0`.

    Returns:
        (rows, baseline_loss): `rows` urut dari kerugian terkecil, tiap elemen
        dict {"Skenario", "loss", "delta" (ΔL), "pct" (R, persen), "rank"};
        `baseline_loss` = total kerugian skenario baseline.
    """
    y0 = DEFAULT_Y0 if y0 is None else y0
    rows = []
    for name, override in SCENARIOS.items():
        p = dict(base_params); p.update(override)
        _, _, _, L = simulate(p, y0, t)
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
