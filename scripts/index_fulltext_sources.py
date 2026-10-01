#!/usr/bin/env python3
"""Check a private 42-PDF corpus against the public development manifest.

The script writes only a sanitized identity/coverage index. Source PDFs,
extracted full text, absolute paths, and copyrighted text snippets are never
copied into the public package.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "references" / "development_sources_42.csv"
OUT = ROOT / "results" / "processing_phase_extension" / "fulltext_source_index.csv"
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


def normalize_doi(value: str) -> str:
    return value.lower().rstrip(".,;:)]}")


def extract_manifest_doi(reference_text: str) -> str:
    match = DOI_RE.search(reference_text)
    return normalize_doi(match.group(0)) if match else ""


def extracted_dois(text: str) -> set[str]:
    return {normalize_doi(value) for value in DOI_RE.findall(text)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf-dir", type=Path, required=True,
                        help="Private directory containing 1.pdf through 42.pdf")
    parser.add_argument("--text-dir", type=Path, required=True,
                        help="Private directory containing extracted 1.txt through 42.txt")
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()

    manifest = pd.read_csv(MANIFEST)
    manifest["reference_number"] = manifest["reference_id"].str.extract(r"(\d+)").astype(int)
    manifest["manifest_doi"] = manifest["reference_text"].map(extract_manifest_doi)

    rows: list[dict[str, object]] = []
    for row in manifest.sort_values("reference_number").itertuples(index=False):
        pdf_path = args.pdf_dir / f"{row.reference_number}.pdf"
        text_path = args.text_dir / f"{row.reference_number}.txt"
        text = text_path.read_text(encoding="utf-8", errors="replace") if text_path.exists() else ""
        rows.append(
            {
                "reference_id": row.reference_id,
                "reference_number": row.reference_number,
                "manifest_doi": row.manifest_doi,
                "source_pdf_label": pdf_path.name,
                "pdf_present": pdf_path.is_file(),
                "text_extracted": text_path.is_file() and bool(text.strip()),
                "manifest_doi_confirmed": row.manifest_doi in extracted_dois(text),
                "n_unique_records": row.n_unique_records,
            }
        )

    index = pd.DataFrame(rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    index.to_csv(args.output, index=False)
    print(f"manifest sources={len(index)}")
    print(f"PDFs present={int(index['pdf_present'].sum())}")
    print(f"texts extracted={int(index['text_extracted'].sum())}")
    print(f"manifest DOI confirmed={int(index['manifest_doi_confirmed'].sum())}")
    if not index["manifest_doi_confirmed"].all():
        print("DOI mismatches/missing:")
        print(index.loc[~index["manifest_doi_confirmed"], ["reference_id", "manifest_doi"]].to_string(index=False))


if __name__ == "__main__":
    main()
