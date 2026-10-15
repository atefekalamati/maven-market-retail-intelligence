"""Clean the exported dashboard PDF and render each page as a PNG.

Prerequisite: export the report from Power BI Desktop (File > Export >
Export to PDF) and copy the file to dashboard/dashboard.pdf.

Run from the repository root:
    python scripts/export_dashboard_images.py

The script removes the PDF's creation timestamp, so the committed file does
not change between identical exports, and writes images/dashboard/*.png.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "dashboard" / "dashboard.pdf"
IMAGE_DIR = ROOT / "images" / "dashboard"
PAGE_IMAGES = [
    "01_executive_overview.png",
    "02_sales_performance.png",
    "03_product_profitability.png",
    "04_customer_analysis.png",
    "05_store_geography.png",
    "06_returns_detail.png",
]
# 1280 px wide at a 996 pt page width; matches the report canvas.
ZOOM = 1280 / 996 * 1.5


def clean_pdf(path: Path) -> None:
    document = pymupdf.open(path)
    if document.page_count != len(PAGE_IMAGES):
        raise ValueError(f"Expected {len(PAGE_IMAGES)} pages, found {document.page_count}")
    document.set_metadata(
        {
            "title": "Maven Market Retail Intelligence",
            "creator": "Power BI Desktop",
            "creationDate": "",
            "modDate": "",
        }
    )
    temporary = path.with_suffix(".tmp.pdf")
    document.save(temporary, garbage=4, deflate=True, no_new_id=True)
    document.close()
    temporary.replace(path)


def render_pages(path: Path) -> list[Path]:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    document = pymupdf.open(path)
    written = []
    for page, name in zip(document, PAGE_IMAGES):
        target = IMAGE_DIR / name
        page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM)).save(target)
        written.append(target)
    return written


def main() -> None:
    clean_pdf(PDF_PATH)
    for path in render_pages(PDF_PATH):
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
