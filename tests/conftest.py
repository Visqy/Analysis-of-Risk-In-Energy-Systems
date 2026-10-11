import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from core.inputs import (  # noqa: E402
    FIELD_SPECS, build_config, default_text, scenario_names, validate_all,
)

APP_PATH = os.path.join(ROOT, "app.py")
BASELINE = scenario_names()[0]


def make_config(scenario=BASELINE, dist="truncnormal", **overrides):
    """Config valid dari nilai bawaan; overrides = string seperti yang diketik user."""
    raw = {k: default_text(k) for k in FIELD_SPECS}
    raw.update({k: str(v) for k, v in overrides.items()})
    values, errors = validate_all(raw)
    assert not errors, errors
    return build_config(values, scenario, dist)


@pytest.fixture
def default_cfg():
    return make_config()


@pytest.fixture
def small_cfg():
    return make_config(n_sim=100)


@pytest.fixture(scope="session")
def small_run():
    from core.run import run_simulation
    return run_simulation(make_config(n_sim=100))


# ---------- helper AppTest ----------

DATA_PAGE = "pages/data_parameter.py"
RESULT_PAGES = ["pages/dashboard.py", "pages/dinamika_sistem.py", "pages/analisis_kestabilan.py",
                "pages/analisis_risiko.py", "pages/perbandingan_skenario.py",
                "pages/rekomendasi.py", "pages/laporan.py"]


def make_app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(APP_PATH, default_timeout=120).run()


def open_data_page(at):
    return at.switch_page(DATA_PAGE).run()


def set_text(at, key, value):
    at.text_input(key=f"w_in_{key}").set_value(value)
    return at.run()


def click(at, label_part):
    next(b for b in at.button if label_part in b.label).click()
    return at.run()


def run_button(at):
    return next(b for b in at.button if "Jalankan" in b.label)


def ran_app(**inputs):
    """App setelah Jalankan dengan n_sim kecil; inputs = string seperti diketik user."""
    at = open_data_page(make_app())
    at.text_input(key="w_in_n_sim").set_value("100")
    for key, value in inputs.items():
        at.text_input(key=f"w_in_{key}").set_value(value)
    at.run()
    click(at, "Jalankan")
    assert at.session_state["last_run"] is not None
    return at


def page_texts(at):
    """Semua teks yang tampil di halaman aktif (markdown, caption, alert, label metrik, dst)."""
    out = []

    def walk(node):
        for child in getattr(node, "children", {}).values():
            for attr in ("value", "label", "body"):
                v = getattr(child, attr, None)
                if isinstance(v, str):
                    out.append(v)
            walk(child)

    walk(at.main)
    return out
