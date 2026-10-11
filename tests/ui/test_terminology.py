import re
from pathlib import Path

import pytest

from tests.conftest import RESULT_PAGES, ROOT, page_texts, ran_app

SAFE = "bukan interval kepercayaan"
BANNED = ("confidence interval", "interval kepercayaan", "kepercayaan 95")


def _is_red(hex_color):
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return r > 180 and g < 100 and b < 100


@pytest.mark.slow
def test_istilah_lama_tidak_muncul_di_ui():
    at = ran_app()
    for page in ("pages/data_parameter.py", *RESULT_PAGES):
        at = at.switch_page(page).run()
        text = " ".join(page_texts(at)).lower().replace(SAFE, "")
        for term in BANNED:
            assert term not in text, f"{term!r} di {page}"


def test_istilah_lama_tidak_ada_di_kode():
    for folder in ("pages", "ui", "core"):
        for path in Path(ROOT, folder).glob("*.py"):
            text = path.read_text(encoding="utf-8").lower().replace(SAFE, "")
            for term in BANNED:
                assert term not in text, f"{term!r} di {path.name}"


def test_merah_hanya_untuk_risiko():
    from ui.charts import COLORS, SCENARIO_COLORS
    assert _is_red(COLORS["L"])
    for k in ("E", "D", "P"):
        assert not _is_red(COLORS[k])
    assert not any(_is_red(c) for c in SCENARIO_COLORS)
    from ui.charts import tornado_chart
    tornado = tornado_chart([("delta", 1.0, 2.0, 3.0)])
    assert not any(_is_red(tr.marker.color) for tr in tornado.data)
    config = Path(ROOT, ".streamlit", "config.toml").read_text(encoding="utf-8")
    colors = re.findall(r'primaryColor\s*=\s*"(#[0-9A-Fa-f]{6})"', config)
    assert colors
    assert not any(_is_red(c) for c in colors)
