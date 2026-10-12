#!/usr/bin/env python3
"""Parse the IT2011 midterm marks PDF into web/data.js (and data/marks.json).

Usage:
    python parse_pdf.py path/to/IT2011_Mid_Marks_Weitages.pdf
    python parse_pdf.py marks.pdf --anonymize     # hide names, keep reg no. masked
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

# "1,234 IT 25 1017 94 Jayasundara R.H. 82.66 16.532"  (marks missing => absent)
ROW = re.compile(
    r"^(?P<idx>[\d,]+)\s+(?P<reg>[A-Z]{2}\s\d{2}\s\d{4}\s\d{2})\s+(?P<name>.+?)"
    r"(?:\s+(?P<mark>\d+(?:\.\d+)?)\s+(?P<score>\d+(?:\.\d+)?))?\s*$"
)


def parse(pdf_path: Path):
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                m = ROW.match(line.strip())
                if not m:
                    continue
                reg = m["reg"]
                rows.append(
                    {
                        "no": int(m["idx"].replace(",", "")),
                        "reg": reg,
                        "batch": "20" + reg.split()[1],  # IT 25 .... -> 2025 intake
                        "name": m["name"].strip(),
                        "mark": float(m["mark"]) if m["mark"] else None,
                        "score": float(m["score"]) if m["score"] else None,
                    }
                )
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--anonymize", action="store_true",
                    help="replace names and mask registration numbers")
    args = ap.parse_args()

    rows = parse(args.pdf)
    if not rows:
        sys.exit("No rows found - is this the right PDF?")

    if args.anonymize:
        for r in rows:
            r["name"] = f"Student {r['no']}"
            r["reg"] = r["reg"][:6] + " ** **"

    out = Path(__file__).parent
    (out / "data" / "marks.json").write_text(json.dumps(rows, indent=1))
    (out / "web" / "data.js").write_text("window.MARKS = " + json.dumps(rows) + ";\n")

    absent = sum(r["mark"] is None for r in rows)
    print(f"Parsed {len(rows)} students ({len(rows) - absent} with marks, {absent} absent/blank)")
    print("Wrote web/data.js and data/marks.json")


if __name__ == "__main__":
    main()
