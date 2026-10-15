"""Shared fixtures for the Maven Market test suite.

Run from the repository root:
    python -m pytest

Data tests need the generated files in data/model (run the pipeline first).
TMDL parsing needs Windows PowerShell and Power BI Desktop; those tests are
skipped when either is unavailable.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

DASHBOARD = ROOT / "dashboard"
MODEL_DIR = DASHBOARD / "MavenMarket.SemanticModel"
REPORT_DIR = DASHBOARD / "MavenMarket.Report"
PAGES_DIR = REPORT_DIR / "definition" / "pages"
DESKTOP_BIN = Path(r"C:\Program Files\Microsoft Power BI Desktop\bin")


@pytest.fixture(scope="session")
def model_tables() -> dict[str, pd.DataFrame]:
    model = ROOT / "data" / "model"
    if not (model / "fact_sales.csv").exists():
        pytest.skip("data/model is not built; run the pipeline first")
    names = ["dim_date", "dim_customer", "dim_product", "dim_store", "fact_sales", "fact_returns"]
    return {name: pd.read_csv(model / f"{name}.csv") for name in names}


@pytest.fixture(scope="session")
def tmdl_summary() -> dict:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell or not (DESKTOP_BIN / "Microsoft.PowerBI.Tabular.dll").exists():
        pytest.skip("TMDL parsing needs Windows PowerShell and Power BI Desktop")
    completed = subprocess.run(
        [
            powershell, "-NoProfile", "-ExecutionPolicy", "Bypass",
            "-File", str(ROOT / "tests" / "tmdl_parse.ps1"),
            str(MODEL_DIR / "definition"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.lstrip("\ufeff"))


def load_pages() -> list[dict]:
    """Every page with its visuals, in report order."""
    order = json.loads((PAGES_DIR / "pages.json").read_text(encoding="utf-8"))["pageOrder"]
    pages = []
    for name in order:
        page_dir = PAGES_DIR / name
        visuals = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((page_dir / "visuals").glob("*/visual.json"))
        ]
        pages.append(
            {
                "page": json.loads((page_dir / "page.json").read_text(encoding="utf-8")),
                "visuals": visuals,
            }
        )
    return pages


@pytest.fixture(scope="session")
def pages() -> list[dict]:
    return load_pages()
