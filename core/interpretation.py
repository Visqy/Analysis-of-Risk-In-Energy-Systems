"""Teks interpretasi otomatis di bawah grafik.

Format tiap interpretasi: **Temuan** (apa yang terjadi di grafik, dengan angka
dan tahun dari hasil), **Makna** (mengapa penting), dan **Implikasi** (tindakan
yang dapat dipertimbangkan). Implikasi selalu bersyarat ("dapat/perlu
dipertimbangkan"), spesifik terhadap hasil, dan tidak memutuskan apa pun,
karena model masih prototipe dengan parameter ilustratif. Gaya ini dijaga oleh
tests/core/test_interpretation_style.py.
"""

import numpy as np

from core.formatting import id_number

_FLAT_TOL = 0.01   # selisih maks-min <= 1% skala -> dianggap datar
_TURN_TOL = 0.02   # puncak/minimum dianggap "balik arah" bila selisih ke ujung > 2% rentang
_GAP_TOL = 0.01    # D - E di atas 1% dari E dianggap permintaan melampaui kapasitas

CATATAN_PROTOTIPE = (
    "Interpretasi ini merupakan hasil simulasi prototipe berdasarkan parameter yang "
    "digunakan dan belum dapat diperlakukan sebagai rekomendasi kebijakan nyata tanpa "
    "validasi menggunakan data empiris."
)


def _year(t, i):
    """Teks "tahun ke-x" untuk indeks `i` pada grid waktu `t`."""
    x = float(t[i])
    return f"tahun ke-{id_number(x, 0 if abs(x - round(x)) < 0.05 else 1)}"


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


def _tmi(temuan, makna, implikasi):
    """Susun interpretasi tiga bagian (markdown) dari Temuan, Makna, dan Implikasi.

    Tiap bagian menjadi paragraf sendiri (dipisah baris kosong).
    """
    return f"**Temuan:** {temuan}\n\n**Makna:** {makna}\n\n**Implikasi:** {implikasi}"


def _gaps(t, E, D):
    """Ringkasan periode permintaan melampaui kapasitas (selisih D - E di atas 1% dari E).

    Returns:
        None bila tidak ada periode; selain itu dict dengan `segments` (list
        (indeks_awal, indeks_akhir) per periode kontinu, urut waktu), `persists`
        (periode terakhir berlangsung sampai akhir horizon), dan `n`.
    """
    E = np.asarray(E, dtype=float)
    D = np.asarray(D, dtype=float)
    over = (D - E) > _GAP_TOL * np.maximum(np.abs(E), 1e-12)
    segments, start = [], None
    for i, flag in enumerate(over):
        if flag and start is None:
            start = i
        if not flag and start is not None:
            segments.append((start, i - 1))
            start = None
    if start is not None:
        segments.append((start, len(over) - 1))
    if not segments:
        return None
    return {"segments": segments, "persists": segments[-1][1] >= len(over) - 1, "n": len(over)}


def capacity_gap_periods(t, E, D):
    """Periode permintaan melampaui kapasitas (selisih D - E di atas 1% dari E).

    Returns:
        List (indeks_awal, indeks_akhir) per periode kontinu, urut waktu; list kosong
        bila tidak ada.
    """
    g = _gaps(t, E, D)
    return [] if g is None else list(g["segments"])


def _gap_periods(t, segs):
    """Frasa periode defisit: "tahun ke-a sampai tahun ke-b", beberapa periode dihubungkan "dan"."""
    parts = [f"{_year(t, i0)} sampai {_year(t, i1)}" for i0, i1 in segs]
    return " dan ".join(parts)


def interpret_capacity_demand(t, E, D):
    """Interpretasi grafik kapasitas dan permintaan: periode D(t) melampaui E(t) dan risikonya."""
    g = _gaps(t, E, D)
    if g is None:
        return _tmi(
            "Permintaan D(t) tidak melampaui kapasitas E(t) sepanjang horizon simulasi.",
            "Tidak tampak risiko kekurangan pasokan energi pada konfigurasi ini.",
            "Pemantauan pertumbuhan permintaan terhadap kapasitas tetap dapat dipertimbangkan.")
    segs = g["segments"]
    if segs[0][0] == 0:
        implikasi = ("Peningkatan kapasitas atau investasi dapat dipertimbangkan sesegera mungkin "
                     "karena kondisi ini sudah terjadi sejak awal horizon.")
    else:
        implikasi = (f"Peningkatan kapasitas atau investasi sebelum {_year(t, segs[0][0])} "
                     "dapat dipertimbangkan.")
    return _tmi(
        f"Permintaan D(t) melampaui kapasitas E(t) pada {_gap_periods(t, segs)}.",
        "Pada periode ini terdapat risiko kekurangan pasokan energi.", implikasi)


def interpret_price(t, P, E, D):
    """Interpretasi grafik harga energi: jalur harga dan kaitannya dengan kesenjangan pasokan."""
    P = np.asarray(P, dtype=float)
    temuan = _describe(t, P, "Indeks harga P(t)")
    gap = _gaps(t, E, D)
    ipk = int(np.argmax(P))
    rising = P.max() > P[0] * 1.05
    if gap is not None:
        makna = ("Pergerakan harga mengikuti kesenjangan antara permintaan dan kapasitas, "
                 "sehingga menunjukkan adanya tekanan harga akibat keterbatasan pasokan.")
    else:
        makna = "Harga bergerak tanpa tekanan kekurangan pasokan yang berarti pada konfigurasi ini."
    if rising:
        implikasi = ("Intervensi untuk menjaga keseimbangan pasokan dan permintaan perlu "
                     f"dipertimbangkan sebelum kenaikan harga mencapai puncaknya pada {_year(t, ipk)}.")
    else:
        implikasi = "Kenaikan harga yang berarti tidak tampak; pemantauan harga tetap dapat dipertimbangkan."
    return _tmi(temuan, makna, implikasi)


def interpret_loss(t, E, D, L):
    """Interpretasi grafik kerugian ekonomi: kapan muncul, puncak, dan kapan kembali nol."""
    L = np.asarray(L, dtype=float)
    pos = np.where(L > 1e-9)[0]
    if len(pos) == 0:
        return _tmi(
            "Kerugian ekonomi L(t) tetap nol sepanjang horizon simulasi.",
            "Permintaan tidak pernah melebihi kapasitas, sehingga tidak ada defisit pasokan.",
            "Intervensi tambahan tampaknya belum diperlukan pada konfigurasi ini, namun "
            "pemantauan tetap dapat dipertimbangkan.")
    n = len(L)
    first, peak = int(pos[0]), int(np.argmax(L))
    awal = "sejak awal horizon" if first == 0 else f"pada {_year(t, first)}"
    if pos[-1] < n - 1:
        akhir = f"dan kembali nol pada {_year(t, int(pos[-1]) + 1)}"
        makna = ("Kerugian muncul ketika permintaan melampaui kapasitas dan menurun setelah "
                 "kapasitas kembali mencukupi permintaan.")
    else:
        akhir = f"dan masih berlangsung hingga {_year(t, n - 1)} sebesar {id_number(L[-1])}"
        makna = "Kerugian masih berlangsung pada akhir horizon karena kapasitas belum mencukupi permintaan."
    if first == 0:
        implikasi = ("Persiapan intervensi dapat dipertimbangkan sesegera mungkin karena kerugian "
                     "sudah muncul sejak awal horizon.")
    else:
        implikasi = (f"Periode sebelum {_year(t, first)} dapat digunakan sebagai batas waktu "
                     "persiapan intervensi.")
    return _tmi(
        f"Kerugian ekonomi L(t) muncul {awal}, memuncak {id_number(L[peak])} pada "
        f"{_year(t, peak)}, {akhir}.",
        makna, implikasi)


def interpret_risk(losses, var, cvar, conf_pct):
    """Interpretasi analisis risiko: arti VaR dan CVaR pada tingkat keyakinan `conf_pct`%."""
    tail = max(100 - conf_pct, 0)
    return _tmi(
        f"VaR {conf_pct}% bernilai {id_number(var)} dan CVaR bernilai {id_number(cvar)}.",
        f"Pada sekitar {conf_pct}% hasil simulasi, total kerugian tidak melebihi VaR; CVaR adalah "
        f"rata-rata kerugian pada {tail}% kondisi terburuk.",
        "CVaR dapat digunakan sebagai acuan untuk menilai kebutuhan cadangan pada kondisi ekstrem.")


def interpret_tornado(sens, display_name=None, top=3):
    """Urutan parameter paling berpengaruh pada total kerugian untuk perubahan ±20%.

    Args:
        sens: list (nama, rugi_-20%, rugi_dasar, rugi_+20%).
        display_name: dict nama -> simbol tampilan (opsional).
        top: jumlah parameter yang disebut.
    """
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
    """Interpretasi perbandingan skenario: skenario terendah dan selisihnya terhadap baseline.

    Args:
        names, losses: skenario yang ditampilkan dan total kerugiannya.
        curves, t: kurva L(t) per nama dan grid waktu (tidak dipakai pada teks;
            dipertahankan agar tanda tangan fungsi stabil).
        baseline_loss, baseline_name: total kerugian dan nama skenario baseline.
    """
    i = int(np.argmin(losses))
    name, loss = names[i], float(losses[i])
    if name == baseline_name:
        return _tmi(
            f"Di antara skenario yang ditampilkan, {name} memiliki total kerugian terendah "
            f"({id_number(loss)}); tidak ada skenario intervensi yang lebih baik daripada baseline "
            "pada parameter saat ini.",
            "Intervensi yang dibandingkan tidak mengurangi total kerugian pada konfigurasi ini.",
            "Peninjauan ulang parameter atau rancangan skenario intervensi dapat dipertimbangkan.")
    delta = baseline_loss - loss
    pct = delta / baseline_loss * 100 if baseline_loss else 0.0
    return _tmi(
        f"Skenario {name} menghasilkan total kerugian terendah ({id_number(loss)}), turun "
        f"{id_number(delta)} ({id_number(pct)}%) dibandingkan baseline.",
        "Ini adalah skenario dengan kerugian terendah berdasarkan model saat ini dalam "
        "konfigurasi simulasi ini.",
        "Skenario tersebut dapat dipertimbangkan lebih lanjut, tetapi keputusan penerapan tetap "
        "memerlukan analisis biaya, kelayakan teknis, dan dampak lainnya.")


def interpret_ranking_basis(ranking_loss, ranking_risk, conf_pct, baseline_name):
    """Interpretasi peringkat: skenario dengan kerugian terendah dan perbandingannya dengan peringkat risiko.

    Args:
        ranking_loss: baris peringkat total kerugian (urut; elemen punya "Skenario",
            "loss", "delta", "pct").
        ranking_risk: baris peringkat risiko (urut; elemen punya "Skenario", "cvar").
        conf_pct: tingkat keyakinan dalam persen untuk label CVaR.
        baseline_name: nama skenario baseline.
    """
    a, b = ranking_loss[0], ranking_risk[0]
    beats = a["Skenario"] != baseline_name
    cvar_a = next(r["cvar"] for r in ranking_risk if r["Skenario"] == a["Skenario"])
    if beats:
        bagian1 = (f"{a['Skenario']} merupakan skenario dengan kerugian terendah berdasarkan model "
                   f"saat ini (total kerugian {id_number(a['loss'])}, turun {id_number(a['delta'])} "
                   f"atau {id_number(a['pct'])}% dibandingkan baseline; dasar: minimum total "
                   "kerugian ekonomi).")
    else:
        bagian1 = ("Tidak terdapat skenario intervensi yang lebih baik daripada baseline "
                   f"berdasarkan parameter saat ini (total kerugian baseline {id_number(a['loss'])}).")
    if a["Skenario"] == b["Skenario"]:
        bagian2 = (f"Skenario yang sama juga memiliki risiko terendah (CVaR {conf_pct}% "
                   f"{id_number(b['cvar'])}).")
        makna = ("Kerugian terendah dan risiko ekstrem terendah menunjuk skenario yang sama "
                 "pada konfigurasi ini.")
    else:
        bagian2 = (f"Berdasarkan risiko, {b['Skenario']} terendah (CVaR {conf_pct}% "
                   f"{id_number(b['cvar'])} dibanding {id_number(cvar_a)}).")
        makna = ("Skenario dengan kerugian rata-rata terendah belum tentu memiliki kerugian "
                 "ekstrem terendah.")
    if not beats:
        implikasi = "Peninjauan ulang parameter atau rancangan skenario intervensi dapat dipertimbangkan."
    elif a["Skenario"] == b["Skenario"]:
        implikasi = ("Skenario tersebut dapat dipertimbangkan lebih lanjut, tetapi keputusan "
                     "penerapan tetap memerlukan analisis biaya, kelayakan teknis, dan dampak lainnya.")
    else:
        implikasi = ("Pertimbangan antara total kerugian dan risiko pada kondisi ekstrem dapat "
                     "dijadikan dasar memilih skenario untuk dianalisis lebih lanjut, dengan analisis "
                     "biaya, kelayakan teknis, dan dampak lainnya.")
    return _tmi(f"{bagian1} {bagian2}", makna, implikasi)


def interpret_implications(t, E, D, P, L):
    """Butir untuk bagian "Implikasi bagi Pengambil Keputusan".

    Returns:
        List kalimat (markdown) tentang kondisi yang perlu diperhatikan dan tindakan
        yang dapat dipertimbangkan; bersyarat dan spesifik terhadap hasil simulasi.
    """
    items = []
    g = _gaps(t, E, D)
    if g is None:
        items.append("Permintaan tidak melampaui kapasitas pada konfigurasi ini; pemantauan "
                     "pertumbuhan permintaan terhadap kapasitas tetap dapat dipertimbangkan.")
    else:
        segs = g["segments"]
        awal = ("sesegera mungkin" if segs[0][0] == 0
                else f"sebelum {_year(t, segs[0][0])}")
        items.append(f"Permintaan melampaui kapasitas pada {_gap_periods(t, segs)}; peningkatan "
                     f"kapasitas atau investasi {awal} dapat dipertimbangkan.")
    L = np.asarray(L, dtype=float)
    if L.max() > 1e-9:
        ipk = int(np.argmax(L))
        items.append(f"Kerugian memuncak ({id_number(L[ipk])}) pada {_year(t, ipk)}; intervensi yang "
                     "difokuskan pada periode sebelum puncak itu dapat dipertimbangkan.")
    P = np.asarray(P, dtype=float)
    if P.max() > P[0] * 1.05:
        items.append(f"Indeks harga naik hingga {id_number(P.max())} pada {_year(t, int(np.argmax(P)))}; "
                     "langkah menjaga keseimbangan pasokan dan permintaan perlu dipertimbangkan "
                     "sebelum waktu tersebut.")
    return items


def interpret_perturbation(t, D_pert, P_pert, D_star, P_star, beta, gamma, osc_freq):
    """Interpretasi simulasi gangguan kecil di sekitar ekuilibrium.

    Subsistem (D,P) tak teredam: simpangan gabungan A = sqrt(dD^2 + (beta/gamma) dP^2)
    konstan. A dibandingkan di awal dan di akhir horizon.
    """
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


def decision_hint(ranking_loss, ranking_risk, baseline_name):
    """Satu kalimat bersyarat untuk pengambil keputusan dari peringkat skenario.

    Args:
        ranking_loss: baris peringkat total kerugian (urut; punya "Skenario").
        ranking_risk: baris peringkat risiko CVaR (urut; punya "Skenario").
        baseline_name: nama skenario baseline.
    """
    a, b = ranking_loss[0]["Skenario"], ranking_risk[0]["Skenario"]
    if a == baseline_name:
        return ("Tidak ada skenario intervensi yang lebih baik daripada baseline pada parameter "
                "saat ini; peninjauan ulang parameter atau rancangan skenario dapat dipertimbangkan.")
    if a == b:
        return (f"{a} dapat dipertimbangkan lebih lanjut berdasarkan kerugian total dan CVaR, "
                "sebelum menelaah biaya, kelayakan teknis, dan aspek implementasi lainnya.")
    return (f"Peringkat berbeda antara kerugian total ({a}) dan CVaR ({b}); keduanya dapat "
            "dibandingkan sebelum menelaah biaya, kelayakan teknis, dan aspek implementasi lainnya.")
