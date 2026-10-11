"""Teks interpretasi otomatis di bawah grafik.

Setiap fungsi menerima data hasil simulasi dan mengembalikan satu atau dua
kalimat deskriptif: arah perubahan, nilai awal → puncak/minimum → nilai akhir,
tahun kejadian, dan hubungan permintaan–kapasitas–kerugian. Teks hanya memuat
fakta dari data, tanpa saran atau kesimpulan kebijakan; klaim perbandingan
selalu "berdasarkan model saat ini". Gaya ini dijaga oleh
tests/core/test_interpretation_style.py.
"""

import numpy as np

from core.formatting import id_number

_FLAT_TOL = 0.01   # selisih maks-min <= 1% skala -> dianggap datar
_TURN_TOL = 0.02   # puncak/minimum dianggap "balik arah" bila selisih ke ujung > 2% rentang


def _year(t, i):
    return f"tahun ke-{id_number(float(t[i]), 1)}"


def _describe(t, y, subject):
    """Kalimat jalur y(t): naik/turun, puncak atau minimum, nilai akhir."""
    y = np.asarray(y, dtype=float)
    n = len(y)
    edge = max(3, n // 50)
    rng = float(y.max() - y.min())
    scale = max(float(np.abs(y).max()), 1e-12)
    a, e = float(y[0]), float(y[-1])
    last = _year(t, n - 1)
    if rng <= _FLAT_TOL * scale:
        return f"{subject} relatif stabil di sekitar {id_number(a)} sepanjang horizon simulasi."

    imax, imin = int(np.argmax(y)), int(np.argmin(y))
    peak = edge <= imax <= n - 1 - edge and (y[imax] - e) > _TURN_TOL * rng and (y[imax] - a) > _TURN_TOL * rng
    trough = edge <= imin <= n - 1 - edge and (e - y[imin]) > _TURN_TOL * rng and (a - y[imin]) > _TURN_TOL * rng

    if peak and trough:
        return (f"{subject} berosilasi: puncak {id_number(y[imax])} pada {_year(t, imax)} dan "
                f"minimum {id_number(y[imin])} pada {_year(t, imin)}, berakhir di {id_number(e)} "
                f"pada {last}.")
    if peak:
        return (f"{subject} naik dari {id_number(a)} hingga puncak {id_number(y[imax])} pada "
                f"{_year(t, imax)}, lalu turun menjadi {id_number(e)} pada {last}.")
    if trough:
        return (f"{subject} turun dari {id_number(a)} ke minimum {id_number(y[imin])} pada "
                f"{_year(t, imin)}, lalu naik menjadi {id_number(e)} pada {last}.")
    verb = "naik" if e >= a else "turun"
    return f"{subject} {verb} dari {id_number(a)} menjadi {id_number(e)} pada {last}."


def interpret_E(t, E):
    """Kalimat jalur kapasitas energi E(t) di grid waktu `t`."""
    return _describe(t, E, "Kapasitas energi E(t)")


def interpret_D(t, D):
    """Kalimat jalur permintaan energi D(t)."""
    return _describe(t, D, "Permintaan energi D(t)")


def interpret_P(t, P):
    """Kalimat jalur harga energi P(t)."""
    return _describe(t, P, "Harga energi P(t)")


def interpret_L(t, E, D, L):
    """Kalimat kerugian L(t): kapan mulai muncul (D melebihi E), puncak, dan kapan kembali nol.

    Bila L nol sepanjang horizon, menyatakan bahwa permintaan tidak pernah
    melebihi kapasitas.
    """
    L = np.asarray(L, dtype=float)
    pos = np.where(L > 1e-9)[0]
    if len(pos) == 0:
        return ("Kerugian ekonomi L(t) tetap nol sepanjang horizon simulasi karena permintaan "
                "D(t) tidak pernah melebihi kapasitas E(t).")
    n = len(L)
    first, peak = int(pos[0]), int(np.argmax(L))
    start = ("sejak awal" if first == 0
             else f"pada {_year(t, first)} saat permintaan D(t) melebihi kapasitas E(t)")
    if pos[-1] < n - 1:
        ending = f"dan kembali nol pada {_year(t, int(pos[-1]) + 1)}"
    else:
        ending = f"dan masih berlangsung hingga {_year(t, n - 1)} sebesar {id_number(L[-1])}"
    return (f"Kerugian ekonomi L(t) muncul {start}, memuncak {id_number(L[peak])} pada "
            f"{_year(t, peak)}, {ending}.")


def interpret_histogram(losses, var, cvar, conf_pct):
    """Kalimat distribusi total kerugian Monte Carlo.

    Memuat perbandingan rata-rata dengan median (kemiringan), rentang 95% hasil
    simulasi (persentil 2,5–97,5), VaR pada `conf_pct`%, dan CVaR.
    """
    losses = np.asarray(losses, dtype=float)
    mean, median = float(losses.mean()), float(np.median(losses))
    lo, hi = np.percentile(losses, [2.5, 97.5])
    if mean > median * 1.02:
        shape = (f"Rata-rata total kerugian {id_number(mean)} lebih besar daripada median "
                 f"{id_number(median)} (distribusi condong ke kanan).")
    else:
        shape = (f"Rata-rata total kerugian {id_number(mean)} mendekati median "
                 f"{id_number(median)} (distribusi relatif simetris).")
    return (f"{shape} Sebanyak 95% hasil simulasi berada di antara {id_number(lo)} dan "
            f"{id_number(hi)}; VaR {conf_pct}% = {id_number(var)} dan rata-rata kerugian di atas "
            f"VaR (CVaR) = {id_number(cvar)}.")


def interpret_tornado(sens, display_name=None, top=3):
    """sens: list (nama, rugi_-20%, rugi_dasar, rugi_+20%)."""
    names = display_name or {}
    rows = []
    for name, low, base, high in sens:
        rows.append((max(abs(low - base), abs(high - base)), names.get(name, name), high - base))
    rows.sort(key=lambda r: -r[0])
    parts = []
    for rank, (swing, label, up) in enumerate(rows[:top]):
        effect = "menaikkan" if up > 0 else "menurunkan"
        if rank == 0:
            parts.append(f"{label} (hingga {id_number(swing)}; kenaikan 20% {effect} kerugian)")
        else:
            parts.append(f"{label} ({id_number(swing)}; {effect})")
    return "Urutan pengaruh terbesar terhadap total kerugian pada perubahan ±20%: " + ", ".join(parts) + "."


def interpret_comparison(names, losses, curves, t, baseline_loss, baseline_name):
    """names/losses: skenario yang ditampilkan; curves: dict nama -> L(t)."""
    i = int(np.argmin(losses))
    name, loss = names[i], float(losses[i])
    if name == baseline_name:
        return (f"Di antara skenario yang ditampilkan, {name} memiliki kerugian terendah "
                f"berdasarkan model saat ini ({id_number(loss)}); tidak ada skenario intervensi "
                "yang lebih baik daripada baseline pada parameter saat ini.")
    delta = baseline_loss - loss
    pct = delta / baseline_loss * 100 if baseline_loss else 0.0
    peak_t = float(t[int(np.argmax(curves[name]))])
    return (f"Skenario dengan kerugian terendah berdasarkan model saat ini adalah {name}: "
            f"{id_number(loss)}, turun {id_number(delta)} ({id_number(pct)}%) dibanding baseline. "
            f"Kerugian skenario ini memuncak pada tahun ke-{id_number(peak_t, 1)}.")


def interpret_perturbation(t, D_pert, P_pert, D_star, P_star, beta, gamma, osc_freq):
    """Subsistem (D,P) tak teredam: simpangan gabungan A = sqrt(dD^2 + (beta/gamma) dP^2)
    konstan. A dibandingkan di awal dan di akhir horizon."""
    dD = np.asarray(D_pert, dtype=float) - D_star
    dP = np.asarray(P_pert, dtype=float) - P_star
    amp = np.sqrt(dD ** 2 + (beta / gamma) * dP ** 2)
    first, last = float(amp[0]), float(amp[-1])
    ratio = last / first if first > 0 else 1.0
    period = 2 * np.pi / osc_freq
    if 0.95 <= ratio <= 1.05:
        behaviour = "tidak meluruh maupun membesar"
    elif ratio < 0.95:
        behaviour = "meluruh"
    else:
        behaviour = "membesar"
    return (f"Setelah gangguan kecil, D(t) dan P(t) berosilasi di sekitar {id_number(D_star)} dan "
            f"{id_number(P_star)} dengan periode ≈ {id_number(period, 1)} tahun; simpangan gabungan "
            f"bernilai {id_number(first)} di awal dan {id_number(last)} di akhir, sehingga "
            f"{behaviour}.")
