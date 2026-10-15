"""Remove run timestamps from the project notebooks.

Jupyter records when each cell ran (metadata.execution: iopub.* and
shell.execute_reply). These change on every run and carry no analysis
content, so they are removed. Cell outputs are kept.

Run from the repository root after executing a notebook:
    python scripts/strip_notebook_metadata.py
"""

from __future__ import annotations

from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
RUN_METADATA_KEYS = ("execution", "papermill", "ExecuteTime")


def strip_notebook(path: Path) -> bool:
    notebook = nbformat.read(path, as_version=4)
    changed = False
    for cell in notebook.cells:
        for key in RUN_METADATA_KEYS:
            if key in cell.metadata:
                del cell.metadata[key]
                changed = True
    for key in RUN_METADATA_KEYS:
        if key in notebook.metadata:
            del notebook.metadata[key]
            changed = True
    if changed:
        nbformat.write(notebook, path)
    return changed


def main() -> None:
    for path in sorted((ROOT / "notebooks").glob("*.ipynb")):
        if strip_notebook(path):
            print(f"Stripped run metadata: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
