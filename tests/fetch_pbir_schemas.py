"""Download the Power BI project JSON schemas used by the report into tests/schemas.

Run once from the repository root (network required):
    python tests/fetch_pbir_schemas.py

The pytest suite validates offline against the vendored copies.
"""

from __future__ import annotations

import json
import posixpath
import re
import urllib.request
from pathlib import Path

PREFIX = "https://developer.microsoft.com/json-schemas/"
RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"
SCHEMA_DIR = Path(__file__).resolve().parent / "schemas"
ROOT_SCHEMAS = [
    "fabric/pbip/pbipProperties/1.0.0/schema.json",
    "fabric/item/report/definitionProperties/2.0.0/schema.json",
    "fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
    "fabric/item/report/definition/report/3.3.0/schema.json",
    "fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
    "fabric/item/report/definition/page/2.1.0/schema.json",
    "fabric/item/report/definition/visualContainer/2.10.0/schema.json",
]
REF_PATTERN = re.compile(r'"\$ref"\s*:\s*"([^"#]+)')


def fetch(relative: str, seen: set[str]) -> None:
    if relative in seen:
        return
    seen.add(relative)
    with urllib.request.urlopen(RAW + relative) as response:
        text = response.read().decode("utf-8")
    json.loads(text)
    target = SCHEMA_DIR / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    for ref in REF_PATTERN.findall(text):
        if ref.startswith(PREFIX):
            fetch(ref[len(PREFIX):], seen)
        elif not ref.startswith("http"):
            fetch(posixpath.normpath(posixpath.join(posixpath.dirname(relative), ref)), seen)


def main() -> None:
    seen: set[str] = set()
    for relative in ROOT_SCHEMAS:
        fetch(relative, seen)
    print(f"Schemas downloaded: {len(seen)}")


if __name__ == "__main__":
    main()
