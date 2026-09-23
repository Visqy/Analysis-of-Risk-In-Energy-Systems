"""
Skenario, parameter default, dan metadata parameter (persis sama dengan
notebook riset, cell 7) — plus PARAM_META untuk panel Data & Parameter.
"""

SCENARIOS = {
    "Baseline (Business as Usual)": {},
    "Peningkatan Investasi Energi": {"I_ramp": 0.8},
    "Integrasi Energi Terbarukan": {"I_ramp": 0.5, "beta": 1.3},
    "Subsidi Energi": {"gamma": 0.4},
    "Investasi Darurat (step tahun ke-5)": {"I_step_t": 5, "I_step_val": 15.0},
}

DEFAULT_PARAMS = {
    "I0": 5.0, "delta": 0.08, "alpha": 1.2, "beta": 0.5,
    "gamma": 0.3, "G0": 10.0, "g_rate": 0.05, "kappa": 2.0,
    "I_ramp": 0.0, "I_step_t": None, "I_step_val": 0.0,
}
DEFAULT_Y0 = [50.0, 45.0, 20.0]  # E0, D0, P0

BASELINE_NAME = "Baseline (Business as Usual)"

# Jawaban dosen pembimbing (2026-09-20): parameter masih ilustratif, belum
# dikalibrasi data empiris — satuan pakai "unit model" generik untuk
# parameter, dan satuan relatif/indeks untuk variabel keadaan (lihat
# VARIABLE_UNITS di bawah). Setelah ada data empiris, ganti ke satuan
# sebenarnya (MW/GWh/TWh, Rp/kWh, juta/miliar rupiah, dst).
DATA_TYPE_LABEL = "Asumsi/Ilustratif"
SOURCE_LABEL = "Skenario simulasi penelitian"
PARAM_DISCLAIMER = (
    "Parameter pada versi prototipe merupakan nilai asumsi untuk keperluan "
    "simulasi dan belum merepresentasikan data empiris suatu wilayah atau "
    "sistem energi tertentu."
)

# Satuan variabel keadaan & waktu — dipakai di caption grafik/metric card.
VARIABLE_UNITS = {
    "E": "unit energi relatif",
    "D": "unit energi relatif",
    "P": "indeks harga",
    "L": "unit kerugian ekonomi relatif",
    "t": "tahun",
}

PARAM_META = {
    "I0": {"label": "I0 (investasi dasar)", "min": 0.0, "max": 20.0, "step": 0.5,
           "default": DEFAULT_PARAMS["I0"], "unit": "unit model"},
    "delta": {"label": "δ (depresiasi infrastruktur)", "min": 0.01, "max": 0.5, "step": 0.01,
              "default": DEFAULT_PARAMS["delta"], "unit": "unit model"},
    "alpha": {"label": "α (elastisitas demand thd ekonomi)", "min": 0.1, "max": 3.0, "step": 0.1,
              "default": DEFAULT_PARAMS["alpha"], "unit": "unit model"},
    "beta": {"label": "β (sensitivitas demand thd harga)", "min": 0.1, "max": 3.0, "step": 0.1,
             "default": DEFAULT_PARAMS["beta"], "unit": "unit model"},
    "gamma": {"label": "γ (sensitivitas harga thd gap)", "min": 0.05, "max": 2.0, "step": 0.05,
              "default": DEFAULT_PARAMS["gamma"], "unit": "unit model"},
    "G0": {"label": "G0 (aktivitas ekonomi awal)", "min": 1.0, "max": 30.0, "step": 1.0,
           "default": DEFAULT_PARAMS["G0"], "unit": "unit model"},
    "g_rate": {"label": "g (laju pertumbuhan ekonomi)", "min": 0.0, "max": 0.2, "step": 0.01,
               "default": DEFAULT_PARAMS["g_rate"], "unit": "unit model"},
    "kappa": {"label": "κ (nilai ekonomi dari shortage)", "min": 0.1, "max": 10.0, "step": 0.1,
              "default": DEFAULT_PARAMS["kappa"], "unit": "unit model"},
    "T_end": {"label": "Horizon Simulasi (tahun)", "min": 5, "max": 60, "step": 1,
              "default": 15, "unit": "tahun"},
}

# Label ramah-baca untuk key override skenario yang bukan bagian PARAM_META
# (I_ramp/I_step_t/I_step_val cuma dipakai skenario, bukan slider mandiri).
OVERRIDE_LABELS = {
    "I_ramp": "Laju investasi tambahan (I_ramp)",
    "I_step_t": "Tahun step investasi (I_step_t)",
    "I_step_val": "Besar step investasi (I_step_val)",
    "beta": PARAM_META["beta"]["label"],
    "gamma": PARAM_META["gamma"]["label"],
}

# Nilai awal kondisi (E0, D0, P0) — untuk panel Data & Parameter.
Y0_META = {
    "E0": {"label": "E0 (kapasitas energi awal)", "default": DEFAULT_Y0[0],
           "unit": VARIABLE_UNITS["E"]},
    "D0": {"label": "D0 (permintaan energi awal)", "default": DEFAULT_Y0[1],
           "unit": VARIABLE_UNITS["D"]},
    "P0": {"label": "P0 (harga energi awal)", "default": DEFAULT_Y0[2],
           "unit": VARIABLE_UNITS["P"]},
}
