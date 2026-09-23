"""Impor/ekspor parameter & hasil simulasi via xlsx (masukan dosen: tombol
"Ekspor Hasil", format input xlsx / output xlsx)."""

import io

import numpy as np
import pandas as pd

from core.scenarios import PARAM_META, VARIABLE_UNITS

APP_VERSION = "ARIES v0.1 – Prototipe Penelitian"


def build_export_workbook(scenario_name, s, t, E, D, P, L, total_loss, ranking_rows, mc_results):
    """Kembalikan bytes file .xlsx berisi parameter aktif, hasil simulasi,
    ranking skenario, dan ringkasan Monte Carlo (kalau sudah dijalankan)."""
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        param_rows = [
            {"Key": key, "Parameter": meta["label"], "Nilai": s[key],
             "Satuan": meta["unit"], "Min": meta["min"], "Max": meta["max"]}
            for key, meta in PARAM_META.items()
        ]
        pd.DataFrame(param_rows).to_excel(writer, sheet_name="Parameter", index=False)
        pd.DataFrame({"Skenario Aktif": [scenario_name]}).to_excel(
            writer, sheet_name="Parameter", index=False, startrow=len(param_rows) + 2)

        pd.DataFrame({
            f"t ({VARIABLE_UNITS['t']})": t,
            f"E(t) ({VARIABLE_UNITS['E']})": E,
            f"D(t) ({VARIABLE_UNITS['D']})": D,
            f"P(t) ({VARIABLE_UNITS['P']})": P,
            f"L(t) ({VARIABLE_UNITS['L']})": L,
        }).to_excel(writer, sheet_name="Hasil Simulasi", index=False)

        pd.DataFrame([
            {"Peringkat": r["rank"], "Skenario": r["Skenario"],
             f"Total Kerugian ({VARIABLE_UNITS['L']})": r["loss"],
             "Penurunan (absolut)": r["delta"], "Penurunan (%)": r["pct"]}
            for r in ranking_rows
        ]).to_excel(writer, sheet_name="Perbandingan Skenario", index=False)

        if mc_results is None:
            pd.DataFrame({"Keterangan": ["Monte Carlo belum dijalankan pada sesi ini."]}).to_excel(
                writer, sheet_name="Monte Carlo", index=False)
        else:
            losses = mc_results["losses"]
            summary = {
                "Jumlah Iterasi": mc_results["inputs"]["n_sim"],
                "Rata-rata": losses.mean(), "Median": np.median(losses),
                "Simpangan Baku": losses.std(),
                "VaR": mc_results["var"], "CVaR": mc_results["cvar"],
            }
            pd.DataFrame([summary]).to_excel(writer, sheet_name="Monte Carlo", index=False)

        pd.DataFrame({"Info": [APP_VERSION]}).to_excel(
            writer, sheet_name="Info Versi", index=False)

    return buffer.getvalue()


def parse_import_workbook(file):
    """Baca sheet 'Parameter' dari file xlsx yang diupload, validasi tiap
    baris terhadap PARAM_META. Kembalikan (values, errors) — values kosong
    kalau ada errors (tolak semua-atau-tidak-sama-sekali)."""
    try:
        df = pd.read_excel(file, sheet_name="Parameter")
    except Exception as exc:
        return {}, [f"Gagal membaca file: {exc}"]

    if "Key" not in df.columns or "Nilai" not in df.columns:
        return {}, ["Sheet 'Parameter' harus punya kolom 'Key' dan 'Nilai' "
                     "(sesuai format hasil Ekspor Hasil)."]

    values = {}
    errors = []
    seen = set()
    for _, row in df.iterrows():
        key = row.get("Key")
        if pd.isna(key) or key not in PARAM_META:
            continue
        seen.add(key)
        meta = PARAM_META[key]
        raw_value = row.get("Nilai")
        if pd.isna(raw_value):
            errors.append(f"{meta['label']}: nilai kosong.")
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            errors.append(f"{meta['label']}: '{raw_value}' bukan angka.")
            continue
        if not (meta["min"] <= value <= meta["max"]):
            errors.append(
                f"{meta['label']}: {value} di luar rentang ({meta['min']}–{meta['max']}).")
            continue
        if key == "T_end":
            value = int(value)
        values[key] = value

    missing = set(PARAM_META.keys()) - seen
    if missing:
        errors.append(f"Parameter tidak ditemukan di file: {', '.join(sorted(missing))}.")

    if errors:
        return {}, errors
    return values, []
