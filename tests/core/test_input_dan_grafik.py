"""Kelengkapan teks input (label, keterangan, satuan) dan format angka grafik."""

import numpy as np

from core.inputs import (
    ALL_KEYS, DISPLAY_NAME, HELP, LATEX_LABEL, PARAM_KEYS, SHORT_DESC, SHORT_UNIT, range_text,
)
from core.scenarios import PARAM_META
from ui.charts import histogram_chart, line_chart, localize, tornado_chart


def test_setiap_input_punya_label_keterangan_dan_satuan():
    for k in ALL_KEYS:
        assert LATEX_LABEL[k] and HELP[k] and SHORT_DESC[k] and range_text(k)
        assert k in SHORT_UNIT
    # hanya seed yang boleh tanpa satuan
    assert [k for k in ALL_KEYS if not SHORT_UNIT[k]] == ["seed"]


def test_keterangan_singkat_tanpa_persamaan():
    for k, text in SHORT_DESC.items():
        assert "$" not in text and "\\" not in text and len(text) < 80, k


def test_nama_simbol_untuk_semua_parameter():
    assert set(DISPLAY_NAME) == set(PARAM_KEYS)
    for k in PARAM_KEYS:
        assert PARAM_META[k]["unit"]


def test_grafik_memakai_format_angka_indonesia():
    t = np.linspace(0, 15, 10)
    figs = [
        line_chart(t, t, "#2E86AB"),
        histogram_chart(np.linspace(1, 100, 50), 90.0, 0.95, unit="u"),
        tornado_chart([("delta", 1.0, 2.0, 3.0)], unit="u"),
        localize(__import__("plotly.graph_objects", fromlist=["Figure"]).Figure()),
    ]
    assert all(f.layout.separators == ",." for f in figs)


def test_tornado_memakai_simbol_bukan_nama_variabel():
    fig = tornado_chart([("delta", 1.0, 2.0, 3.0), ("g_rate", 1.0, 2.0, 3.0)])
    assert list(fig.data[0].y) == ["δ", "g"]
