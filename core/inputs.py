"""Spesifikasi, parsing, dan validasi seluruh input form.

`FIELD_SPECS` mendefinisikan tiap input (label, satuan, rentang, nilai bawaan,
bilangan bulat atau desimal). Input diketik sebagai teks; `parse_field`
mengubahnya menjadi angka (koma atau titik sebagai desimal) dan menolak nilai
kosong, bukan angka, negatif, bukan bilangan bulat (bila diwajibkan), atau di
luar rentang. `build_config` menyusun konfigurasi run dari nilai yang valid.

Teks tampilan: `LATEX_LABEL` (label), `SHORT_DESC` + `HELP` (tooltip),
`SHORT_UNIT` (satuan di dalam kotak), `DISPLAY_NAME` (simbol untuk tabel/grafik).
"""

import re

from core.scenarios import PARAM_META, DEFAULT_Y0, Y0_META, VARIABLE_UNITS, SCENARIOS

PARAM_KEYS = ["I0", "delta", "alpha", "beta", "gamma", "G0", "g_rate", "kappa"]
Y0_KEYS = ["E0", "D0", "P0"]
SIGMA_KEYS = ["sd_delta", "sd_gamma", "sd_I0"]
SIGMA_TARGET = {"sd_delta": "delta", "sd_gamma": "gamma", "sd_I0": "I0"}

DIST_OPTIONS = {
    "truncnormal": "Distribusi normal terpotong dalam rentang parameter",
    "normal": "Normal dengan batas bawah (metode lama)",
}


def _spec(key, label, unit, lo, hi, default, group, is_int=False, dec=2, step=None):
    return {"key": key, "label": label, "unit": unit, "min": lo, "max": hi,
            "default": default, "group": group, "int": is_int, "dec": dec, "step": step}


def _build_specs():
    specs = {}
    for k, label in (("E0", "E(0) — kapasitas energi awal"),
                     ("D0", "D(0) — permintaan energi awal"),
                     ("P0", "P(0) — harga energi awal")):
        unit = VARIABLE_UNITS[k[0]]
        specs[k] = _spec(k, label, unit, 0.0, 500.0, Y0_META[k]["default"], "kondisi")
    m = PARAM_META["T_end"]
    specs["T_end"] = _spec("T_end", "Horizon simulasi", "tahun", m["min"], m["max"],
                           m["default"], "kondisi", is_int=True, dec=0)
    for k in PARAM_KEYS:
        m = PARAM_META[k]
        specs[k] = _spec(k, m["label"], m["unit"], m["min"], m["max"], m["default"],
                         "parameter", dec=2, step=m["step"])
    specs["n_sim"] = _spec("n_sim", "Jumlah iterasi", "iterasi", 100, 5000, 1000,
                           "risiko", is_int=True, dec=0)
    specs["conf"] = _spec("conf", "Tingkat keyakinan VaR/CVaR", "%", 80, 99, 95,
                          "risiko", is_int=True, dec=0)
    specs["seed"] = _spec("seed", "Seed acak", "bilangan bulat", 0, 999999, 2026,
                          "risiko", is_int=True, dec=0)
    specs["sd_delta"] = _spec("sd_delta", "σ untuk δ", "unit model", 0.0, 0.1, 0.02, "sigma", dec=3)
    specs["sd_gamma"] = _spec("sd_gamma", "σ untuk γ", "unit model", 0.0, 0.5, 0.10, "sigma", dec=2)
    specs["sd_I0"] = _spec("sd_I0", "σ untuk I0", "unit model", 0.0, 5.0, 1.50, "sigma", dec=2)
    return specs


FIELD_SPECS = _build_specs()
ALL_KEYS = list(FIELD_SPECS.keys())

# Label tampilan: "{nama} ({simbol})" dengan notasi LaTeX (Streamlit merender $...$).
LATEX_LABEL = {
    "E0": r"Kapasitas energi awal ($E(0)$)",
    "D0": r"Permintaan energi awal ($D(0)$)",
    "P0": r"Harga energi awal ($P(0)$)",
    "T_end": r"Horizon simulasi ($T$)",
    "I0": r"Investasi dasar ($I_0$)",
    "delta": r"Depresiasi infrastruktur ($\delta$)",
    "alpha": r"Elastisitas permintaan ($\alpha$)",
    "beta": r"Sensitivitas permintaan ($\beta$)",
    "gamma": r"Sensitivitas harga ($\gamma$)",
    "G0": r"Aktivitas ekonomi awal ($G_0$)",
    "g_rate": r"Pertumbuhan ekonomi ($g$)",
    "kappa": r"Nilai ekonomi shortage ($\kappa$)",
    "n_sim": "Jumlah iterasi",
    "conf": "Tingkat keyakinan VaR/CVaR",
    "seed": "Seed acak",
    "sd_delta": r"Ketidakpastian depresiasi ($\sigma_\delta$)",
    "sd_gamma": r"Ketidakpastian sensitivitas harga ($\sigma_\gamma$)",
    "sd_I0": r"Ketidakpastian investasi ($\sigma_{I_0}$)",
}

# Satuan ringkas yang tampil di dalam kotak input (rata kanan). Satuan lengkap ada di tooltip.
SHORT_UNIT = {
    "E0": "unit energi", "D0": "unit energi", "P0": "indeks harga", "T_end": "tahun",
    "I0": "unit model", "delta": "unit model", "alpha": "unit model", "beta": "unit model",
    "gamma": "unit model", "G0": "unit model", "g_rate": "unit model", "kappa": "unit model",
    "n_sim": "iterasi", "conf": "%", "seed": "",
    "sd_delta": "unit model", "sd_gamma": "unit model", "sd_I0": "unit model",
}

# Keterangan singkat (satu kalimat, tanpa persamaan) yang tampil di bawah tiap input.
SHORT_DESC = {
    "E0": "Kapasitas energi pada awal periode.",
    "D0": "Permintaan energi pada awal periode.",
    "P0": "Indeks harga energi pada awal periode.",
    "T_end": "Panjang periode analisis (bilangan bulat).",
    "I0": "Laju investasi dasar pada infrastruktur energi.",
    "delta": "Tingkat penyusutan kapasitas energi per tahun.",
    "alpha": "Seberapa kuat aktivitas ekonomi mendorong permintaan.",
    "beta": "Seberapa kuat harga menekan permintaan.",
    "gamma": "Seberapa cepat harga bereaksi terhadap selisih permintaan dan kapasitas.",
    "G0": "Tingkat aktivitas ekonomi pada awal periode.",
    "g_rate": "Laju pertumbuhan aktivitas ekonomi per tahun.",
    "kappa": "Nilai kerugian per unit kekurangan pasokan.",
    "n_sim": "Banyaknya percobaan acak Monte Carlo (bilangan bulat).",
    "conf": "Tingkat keyakinan VaR dan CVaR dalam persen (bilangan bulat).",
    "seed": "Angka acuan acak; seed sama menghasilkan hasil sama (bilangan bulat).",
    "sd_delta": "Simpangan baku ketidakpastian depresiasi.",
    "sd_gamma": "Simpangan baku ketidakpastian sensitivitas harga.",
    "sd_I0": "Simpangan baku ketidakpastian investasi dasar.",
}

# Nama simbol untuk tabel dan sumbu grafik (teks biasa, Plotly/dataframe tidak merender LaTeX).
DISPLAY_NAME = {
    "I0": "I₀", "delta": "δ", "alpha": "α", "beta": "β", "gamma": "γ",
    "G0": "G₀", "g_rate": "g", "kappa": "κ",
}

# Persamaan/catatan simbol di tooltip (setelah SHORT_DESC) — sesuai persamaan model, tidak diubah.
HELP = {
    "E0": r"Persamaan: $\dfrac{dE}{dt} = I(t) - \delta E$.",
    "D0": r"Persamaan: $\dfrac{dD}{dt} = \alpha G(t) - \beta P$.",
    "P0": r"Persamaan: $\dfrac{dP}{dt} = \gamma (D - E)$.",
    "T_end": r"Waktu dihitung pada 300 titik dari $t=0$ sampai $T$.",
    "I0": r"$I(t) = I_0$, ditambah intervensi pada skenario tertentu.",
    "delta": r"Harus $> 0$. Muncul pada $\dfrac{dE}{dt} = I(t) - \delta E$.",
    "alpha": r"Muncul pada $\dfrac{dD}{dt} = \alpha G(t) - \beta P$, dengan $G(t)$ aktivitas ekonomi.",
    "beta": r"Harus $> 0$. Muncul pada $\dfrac{dD}{dt} = \alpha G(t) - \beta P$.",
    "gamma": r"Muncul pada $\dfrac{dP}{dt} = \gamma (D - E)$.",
    "G0": r"$G(t) = G_0 e^{g t}$.",
    "g_rate": r"$G(t) = G_0 e^{g t}$; 0,05 berarti 5% per tahun.",
    "kappa": r"$L = \kappa \max(0, D - E)$.",
    "n_sim": "Makin banyak iterasi, estimasi VaR dan CVaR makin stabil.",
    "conf": "Contoh: 95 berarti VaR 95% dan CVaR 95%.",
    "seed": "Seed yang sama menghasilkan hasil Monte Carlo yang sama.",
    "sd_delta": r"$\delta$ diacak dengan simpangan baku ini pada Monte Carlo.",
    "sd_gamma": r"$\gamma$ diacak dengan simpangan baku ini pada Monte Carlo.",
    "sd_I0": r"$I_0$ diacak dengan simpangan baku ini pada Monte Carlo.",
}


def fmt_input(value, dec):
    """Ubah nilai menjadi teks untuk kotak input: koma desimal, tanpa pemisah ribuan.

    `dec` = jumlah desimal; 0 menghasilkan bilangan bulat.
    """
    if dec == 0:
        return str(int(round(value)))
    return f"{value:.{dec}f}".replace(".", ",")


def default_text(key):
    """Teks nilai bawaan untuk field `key` (siap diisi ke kotak input)."""
    sp = FIELD_SPECS[key]
    return fmt_input(sp["default"], sp["dec"])


def range_text(key):
    """Rentang nilai yang diperbolehkan untuk field `key`, mis. "0,00–500,00"."""
    sp = FIELD_SPECS[key]
    return f"{fmt_input(sp['min'], sp['dec'] if not sp['int'] else 0)}–" \
           f"{fmt_input(sp['max'], sp['dec'] if not sp['int'] else 0)}"


_NUM = re.compile(r"^[+-]?\d+(\.\d+)?$")


def parse_field(key, raw):
    """Validasi satu field dari teks mentah.

    Args:
        key: kunci di `FIELD_SPECS`.
        raw: teks yang diketik pengguna (boleh None).

    Returns:
        (nilai, None) bila valid (int untuk field bulat, float lainnya), atau
        (None, pesan_error) dengan pesan seperti "Wajib diisi",
        "Harus berupa angka", "Tidak boleh negatif", "Harus bilangan bulat",
        atau "Di luar rentang a–b".
    """
    sp = FIELD_SPECS[key]
    s = "" if raw is None else str(raw).strip()
    if s == "":
        return None, "Wajib diisi"
    t = s.replace(",", ".")
    if not _NUM.match(t):
        return None, "Harus berupa angka"
    n = float(t)
    if n < 0:
        return None, "Tidak boleh negatif"
    if sp["int"] and n != int(n):
        return None, "Harus bilangan bulat"
    if n < sp["min"] or n > sp["max"]:
        return None, f"Di luar rentang {range_text(key)}"
    return (int(n) if sp["int"] else n), None


def validate_all(raw):
    """Validasi semua field sekaligus.

    Args:
        raw: dict key -> teks mentah.

    Returns:
        (values, errors): `values` berisi field yang valid, `errors` berisi
        pesan per field yang tidak valid (key -> pesan).
    """
    values, errors = {}, {}
    for k in ALL_KEYS:
        v, err = parse_field(k, raw.get(k))
        if err:
            errors[k] = err
        else:
            values[k] = v
    return values, errors


SOURCE_OPTIONS = ["Ilustratif/Asumsi", "Data Aktual"]


def build_config(values, scenario, dist, source=None):
    """Susun konfigurasi run dari nilai yang sudah valid.

    Args:
        values: hasil `validate_all` (semua field valid).
        scenario: nama skenario kebijakan aktif.
        dist: jenis distribusi ketidakpastian ("truncnormal" atau "normal").
        source: dict {"status", "name", "year"} sumber data; default
            "Ilustratif/Asumsi" tanpa nama dan tahun.

    Returns:
        dict dengan kunci scenario, y0 [E0, D0, P0], T_end, params (parameter
        model), n_sim, conf (pecahan, mis. 0,95), seed, dist, source, sd
        (simpangan baku δ, γ, I0). Dipakai sebagai input `run_simulation`
        dan sebagai dasar deteksi hasil usang (`config_key`).
    """
    return {
        "scenario": scenario,
        "y0": [values["E0"], values["D0"], values["P0"]],
        "T_end": values["T_end"],
        "params": {k: values[k] for k in PARAM_KEYS},
        "n_sim": values["n_sim"],
        "conf": values["conf"] / 100.0,
        "seed": values["seed"],
        "dist": dist,
        "source": source or {"status": SOURCE_OPTIONS[0], "name": "", "year": ""},
        "sd": {SIGMA_TARGET[k]: values[k] for k in SIGMA_KEYS},
    }


def scenario_names():
    """Daftar nama skenario kebijakan (urutan sesuai `SCENARIOS`)."""
    return list(SCENARIOS.keys())


def default_y0():
    """Salinan kondisi awal bawaan [E0, D0, P0]."""
    return list(DEFAULT_Y0)
