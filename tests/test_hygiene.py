"""Kerapian kode: tanpa impor tak terpakai dan tanpa API Streamlit yang sudah usang."""

import ast
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

def _py_files():
    files = [ROOT / "app.py"]
    for d in ("core", "pages", "ui"):
        files += sorted((ROOT / d).glob("*.py"))
    return [f for f in files if f.name != "__init__.py"]


def _unused_imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            names |= {(a.asname or a.name).split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom):
            names |= {a.asname or a.name for a in n.names}
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    return sorted(x for x in names if x not in used and x != "*")


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_tanpa_impor_tak_terpakai(path):
    assert _unused_imports(path) == []


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_tanpa_use_container_width(path):
    assert "use_container_width" not in path.read_text(encoding="utf-8")


# ---- dokumentasi kode: fungsional, tanpa rujukan sumber ----

# Kode dan komentar menjelaskan fungsi; asal-usul kebutuhan dicatat di dokumen
# dokumen terpisah, bukan di kode.
_SOURCE_REFS = ("§", "masukan dosen", "arahan", "dosen", "pembimbing", "bu sisil",
                "wireframe", "fase ", "docs/", "claude.md", "notebook", "persetujuan peneliti")


def _all_text_files():
    files = _py_files()
    files += [f for f in sorted((ROOT / "tests").rglob("*.py")) if f.name != "test_hygiene.py"]
    return files


@pytest.mark.parametrize("path", _all_text_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_tanpa_rujukan_sumber_kebutuhan(path):
    text = path.read_text(encoding="utf-8").lower()
    hits = [ref for ref in _SOURCE_REFS if ref in text]
    assert hits == [], f"rujukan sumber di {path.name}: {hits}"


@pytest.mark.parametrize("path", _py_files(), ids=lambda p: str(p.relative_to(ROOT)))
def test_modul_punya_docstring(path):
    assert ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))), path.name


@pytest.mark.parametrize(
    "path", [f for f in _py_files() if f.parent.name in ("core", "ui")],
    ids=lambda p: str(p.relative_to(ROOT)))
def test_fungsi_publik_core_dan_ui_punya_docstring(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    missing = [n.name for n in tree.body
               if isinstance(n, (ast.FunctionDef, ast.ClassDef))
               and not n.name.startswith("_") and not ast.get_docstring(n)]
    assert missing == [], f"{path.name}: {missing}"
