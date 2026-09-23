"""Teks interpretasi otomatis 1-2 kalimat per grafik (masukan dosen §2.2):
arah perubahan, waktu nilai tertinggi/terendah, hubungan D-E-L, dan makna
bagi pengambil keputusan.
"""

import numpy as np

from core.formatting import id_number


def _direction(y):
    if y[-1] > y[0] * 1.01:
        return "meningkat"
    if y[-1] < y[0] * 0.99:
        return "menurun"
    return "relatif stabil"


def interpret_E(t, E):
    direction = _direction(E)
    idx = int(np.argmax(E))
    return (f"Kapasitas energi E(t) {direction} sepanjang horizon simulasi, mencapai nilai "
            f"tertinggi {id_number(E[idx])} pada tahun ke-{id_number(t[idx], 1)}.")


def interpret_D(t, D):
    direction = _direction(D)
    idx = int(np.argmax(D))
    return (f"Permintaan energi D(t) {direction}, dengan titik tertinggi "
            f"{id_number(D[idx])} pada tahun ke-{id_number(t[idx], 1)}.")


def interpret_P(t, P):
    direction = _direction(P)
    idx = int(np.argmax(P))
    return (f"Harga energi P(t) {direction} mengikuti dinamika ketidakseimbangan "
            f"permintaan-kapasitas, mencapai titik tertinggi {id_number(P[idx])} "
            f"pada tahun ke-{id_number(t[idx], 1)}.")


def interpret_L(t, E, D, L):
    idx = int(np.argmax(L))
    if L[idx] <= 1e-9:
        return ("Kerugian ekonomi L(t) tetap nol sepanjang horizon simulasi karena "
                "permintaan D(t) tidak pernah melebihi kapasitas E(t) — tidak ada "
                "defisit pasokan yang perlu diantisipasi pada konfigurasi saat ini.")
    return (f"Kerugian ekonomi L(t) muncul saat permintaan D(t) melebihi kapasitas E(t), "
            f"mencapai puncak {id_number(L[idx])} pada tahun ke-{id_number(t[idx], 1)} — "
            f"periode ini menandai defisit pasokan terbesar yang perlu diantisipasi "
            f"pengambil keputusan, misalnya lewat penambahan investasi kapasitas.")
