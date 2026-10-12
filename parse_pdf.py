#!/usr/bin/env python3
"""Parse any subject's exam or midterm marks PDF into web/data.js and data/marks.json.

Adapts automatically to the specific subject/module (e.g., IT2011, SE2020, CS3040),
assessment type (Midterm, Final, etc.), and weightage from the standard SLIIT marksheet format.

Usage:
    python parse_pdf.py path/to/results.pdf
    python parse_pdf.py path/to/results.pdf --anonymize
    python parse_pdf.py path/to/results.pdf --subject-code IT2011 --subject-title "AI & ML"
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pdfplumber

# Multi-format row patterns:
# Format B (No student name: No, Reg, Mark, Grade, Status): e.g. "1 IT 23 1724 32 66.6 C Pass"
ROW_B = re.compile(
    r"^(?P<idx>[\d,]+)\s+(?P<reg>[A-Z]{2,4}\s+\d{2}\s+\d{4}\s+\d{2})\s+"
    r"(?P<mark>\d+(?:\.\d+)?|-)\s+(?P<grade>[A-Z][+-]?|[A-Z]{1,2})(?:\s+(?P<status>Pass|Fail))?\s*$",
    re.I,
)

# Format B absent without mark: "13 IT 24 1019 48 E Fail"
ROW_B_NOMARK = re.compile(
    r"^(?P<idx>[\d,]+)\s+(?P<reg>[A-Z]{2,4}\s+\d{2}\s+\d{4}\s+\d{2})\s+"
    r"(?P<grade>[A-Z][+-]?|[A-Z]{1,2})\s+(?P<status>Pass|Fail)\s*$",
    re.I,
)

# Format C (With name, mark, grade, status): e.g. "1 IT 23 1724 32 Silva A. 66.6 C Pass"
ROW_C = re.compile(
    r"^(?P<idx>[\d,]+)\s+(?P<reg>[A-Z]{2,4}\s+\d{2}\s+\d{4}\s+\d{2})\s+(?P<name>.+?)\s+"
    r"(?P<mark>\d+(?:\.\d+)?|-)\s+(?P<grade>[A-Z][+-]?|[A-Z]{1,2})(?:\s+(?P<status>Pass|Fail))?\s*$",
    re.I,
)

# Format A (Midterm with name, mark, score): e.g. "1,234 IT 25 1017 94 Jayasundara R.H. 82.66 16.532"
ROW_A = re.compile(
    r"^(?P<idx>[\d,]+)\s+(?P<reg>[A-Z]{2,4}\s\d{2}\s\d{4}\s\d{2})\s+(?P<name>.+?)"
    r"(?:\s+(?P<mark>\d+(?:\.\d+)?)\s+(?P<score>\d+(?:\.\d+)?))?\s*$"
)
ROW = ROW_A

# Header patterns commonly found in SLIIT exam sheets
SUBJECT_PATTERN_1 = re.compile(r"^(?P<title>.+?)\s*-\s*(?P<code>[A-Z]{2,4}\s*\d{4})\s*$", re.I)
SUBJECT_PATTERN_2 = re.compile(r"^(?P<code>[A-Z]{2,4}\s*\d{4})\s*-\s*(?P<title>.+?)\s*$", re.I)
EXAM_YEAR_PATTERN = re.compile(r"^(?:Examination\s*Type\s*:-\s*)?(?P<exam>[A-Za-z0-9\s]+?)\s*-\s*(?P<year>\d{4})\s*$", re.I)
MAX_WEIGHTAGE_PATTERN = re.compile(r"Out of\s+(?P<max>\d+)(?:\s*\(\s*(?P<weight>[^\)]+)\s*\))?", re.I)


def extract_metadata(header_text: str, pdf_path: Path) -> dict:
    """Extract subject code, subject title, exam type, year, and weightage from header text or filename."""
    meta = {
        "subject_code": "",
        "subject_title": "",
        "exam_type": "Assessment",
        "year": "",
        "max_mark": 100.0,
        "weightage": "",
    }

    lines = [line.strip() for line in header_text.splitlines() if line.strip()]
    for line in lines[:25]:
        if re.search(r"final\s*grades", line, re.I):
            meta["exam_type"] = "Final"
        m1 = SUBJECT_PATTERN_1.match(line)
        if m1 and not meta["subject_code"]:
            meta["subject_title"] = m1.group("title").strip()
            meta["subject_code"] = re.sub(r"\s+", "", m1.group("code").upper())
            continue

        m2 = SUBJECT_PATTERN_2.match(line)
        if m2 and not meta["subject_code"]:
            meta["subject_code"] = re.sub(r"\s+", "", m2.group("code").upper())
            meta["subject_title"] = m2.group("title").strip()
            continue

        me = EXAM_YEAR_PATTERN.match(line)
        if me and not meta["year"]:
            meta["exam_type"] = me.group("exam").strip()
            meta["year"] = me.group("year").strip()
            continue

        mw = MAX_WEIGHTAGE_PATTERN.search(line)
        if mw:
            try:
                meta["max_mark"] = float(mw.group("max"))
            except (ValueError, TypeError):
                pass
            if mw.group("weight"):
                meta["weightage"] = mw.group("weight").strip()

    # Fallback to filename if subject code not detected from header
    if not meta["subject_code"]:
        fn_match = re.search(r"([A-Z]{2,4}\s*\d{4})", pdf_path.stem, re.I)
        if fn_match:
            meta["subject_code"] = re.sub(r"\s+", "", fn_match.group(1).upper())
            if not meta["subject_title"]:
                meta["subject_title"] = meta["subject_code"]

    if not meta["subject_title"] and meta["subject_code"]:
        meta["subject_title"] = meta["subject_code"]

    if "mid" in pdf_path.stem.lower() and meta["exam_type"] == "Assessment":
        meta["exam_type"] = "Midterm"

    return meta


def parse(pdf_path: Path, override_meta: dict = None):
    rows = []
    metadata = {}

    with pdfplumber.open(pdf_path) as pdf:
        # Extract metadata from the first page header
        first_page_text = pdf.pages[0].extract_text() or "" if pdf.pages else ""
        metadata = extract_metadata(first_page_text, pdf_path)

        for page in pdf.pages:
            for line in (page.extract_text() or "").splitlines():
                l = line.strip()
                mb = ROW_B.match(l)
                mb_no = ROW_B_NOMARK.match(l) if not mb else None
                mc = ROW_C.match(l) if not (mb or mb_no) else None
                ma = ROW_A.match(l) if not (mb or mb_no or mc) else None
                m = mb or mb_no or mc or ma
                if not m:
                    continue

                reg = m.group("reg")
                parts = reg.split()
                batch = f"20{parts[1]}" if len(parts) > 1 and parts[1].isdigit() else "Unknown"
                degree = parts[0] if len(parts) > 0 else "Unknown"

                gd = m.groupdict()
                name = gd.get("name")
                name = name.strip() if name else ""

                mark_val = gd.get("mark")
                mark = float(mark_val) if (mark_val and mark_val != "-") else None

                score_val = gd.get("score")
                score = float(score_val) if score_val else None

                grade = gd.get("grade")
                status = gd.get("status")

                item = {
                    "no": int(m.group("idx").replace(",", "")),
                    "reg": reg,
                    "batch": batch,
                    "degree": degree,
                    "name": name,
                    "mark": mark,
                    "score": score,
                }
                if grade:
                    item["grade"] = grade.strip()
                if status:
                    item["status"] = status.strip()
                rows.append(item)

    if override_meta:
        for k, v in override_meta.items():
            if v:
                metadata[k] = v

    return metadata, rows


def main():
    ap = argparse.ArgumentParser(
        description="Parse exam and midterm marks PDF into dashboard data."
    )
    ap.add_argument("pdf", type=Path, help="Path to marks PDF file")
    ap.add_argument(
        "--anonymize",
        action="store_true",
        help="replace student names and mask registration numbers",
    )
    ap.add_argument("--subject-code", help="override subject code (e.g. IT2011, SE2020)")
    ap.add_argument("--subject-title", help="override subject title (e.g. 'Software Engineering')")
    ap.add_argument("--exam-type", help="override assessment type (e.g. 'Midterm', 'Final')")
    ap.add_argument("--weightage", help="override weightage (e.g. 20%%)")
    args = ap.parse_args()

    overrides = {
        "subject_code": args.subject_code,
        "subject_title": args.subject_title,
        "exam_type": args.exam_type,
        "weightage": args.weightage,
    }

    metadata, rows = parse(args.pdf, overrides)
    if not rows:
        sys.exit("No student rows found – is this the right PDF?")

    if args.anonymize:
        for r in rows:
            r["name"] = f"Student {r['no']}"
            r["reg"] = r["reg"][:6] + " ** **"

    absent = sum(r["mark"] is None for r in rows)
    metadata["total_students"] = len(rows)
    metadata["scored_students"] = len(rows) - absent
    metadata["absent_students"] = absent

    out = Path(__file__).parent
    payload = {
        "metadata": metadata,
        "records": rows,
    }

    # Save JSON and JS outputs
    (out / "data" / "marks.json").write_text(json.dumps(payload, indent=1))
    js_content = f"window.DATA = {json.dumps(payload)};\nwindow.MARKS = window.DATA.records;\n"
    (out / "web" / "data.js").write_text(js_content)

    print(
        f"Parsed {len(rows)} students for {metadata.get('subject_code', 'Subject')} - {metadata.get('subject_title', '')}"
    )
    print(f"({len(rows) - absent} with marks, {absent} absent/blank)")
    print(f"Assessment: {metadata.get('exam_type', '')} ({metadata.get('weightage', '')})")
    print("Wrote web/data.js and data/marks.json")


if __name__ == "__main__":
    main()
