#!/usr/bin/env python3
"""extract_pdf_text.py — Extract full text from any PDF using pypdf."""

import sys
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    print("Installing pypdf...")
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    from pypdf import PdfReader


def extract_text(pdf_path: str, output_path: str | None = None) -> str:
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    print(f"PDF: {pdf_path}")
    print(f"Pages: {total_pages}")
    print("-" * 60)

    all_text = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        all_text.append(f"\n{'=' * 60}\nPAGE {i + 1} / {total_pages}\n{'=' * 60}\n{text}")
        if (i + 1) % 10 == 0:
            print(f"  Extracted page {i + 1}/{total_pages}...")

    full_text = "\n".join(all_text)

    if output_path:
        Path(output_path).write_text(full_text, encoding="utf-8")
        print(f"\nSaved to: {output_path}")
        print(f"Total chars: {len(full_text):,}")
    else:
        print(full_text)

    return full_text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_text.py <input.pdf> [output.txt]")
        sys.exit(1)
    pdf = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else pdf.rsplit(".", 1)[0] + ".txt"
    extract_text(pdf, out)
