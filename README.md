# Class Rank Insights

Turn any **SLIIT exam results PDF** into a searchable, filterable analytics dashboard that shows
**how you compare with the batch** and **what to do next**.

Works with any subject (IT, SE, CS, BM, …) and any assessment type (Midterm, Final, etc.).
The subject code, title, exam type, and weightage are **auto-detected** from the PDF header.

## Features
- Auto-detects **subject code, title, exam type, year, and weightage** from the PDF
- Students grouped by **grade** (A+ … E, plus Absent) with counts; click a grade to filter
- **Search** by name or registration number; filter by **batch** (e.g. IT23 / IT24 / IT25) and **programme**
- Sortable, paginated table with competition ranks (ties share a rank)
- **"How am I doing?"** – enter your mark (or reg. no.) to get:
  - your rank, **Top X%**, and % of students you beat
  - how many students share your grade and are within ±2 marks of you
  - difference from the average and z-score
  - the **gap to the next grade** and personalised improvement suggestions

## Run it

### Option 1: In the Browser (Easiest – no Python required)
1. Open `web/index.html` in Chrome/Edge (or run `cd web; python -m http.server 8000` and visit `http://localhost:8000`).
2. **Drag & drop** your exam results PDF directly onto the page.
3. The dashboard and analytics will generate instantly in your browser (100% private, client-side).

### Option 2: Python CLI (Pre-generate data)
```bash
pip install -r requirements.txt

# Auto-detects everything from the PDF header:
python parse_pdf.py path/to/your_results.pdf        # creates web/data.js + data/marks.json

# Optional: override metadata if the PDF header is unusual:
python parse_pdf.py path/to/results.pdf --subject-code IT2011 --exam-type Midterm --weightage 20%

# Anonymize before sharing:
python parse_pdf.py path/to/results.pdf --anonymize

# Serve the dashboard:
cd web; python -m http.server 8000                 # then open http://localhost:8000
```

## Supported PDF format

The parser handles the standard SLIIT marks sheet format:

```
Sri Lanka Institute of Information Technology
<Subject Name> - <Subject Code>
<Exam Type> - <Year>
...
# Registration No Name  Assessment Mark  Out of 100  Weightage Score (X%)
1 IT 25 1017 94 Jayasundara R.H. 82.66 16.532
2 IT 24 1002 11 Riqshan F M 40.34 8.068
6 IT 23 7792 66 CHRISTILAN K                   ← absent/blank (no mark)
```

Registration prefixes can be any degree code: `IT`, `SE`, `CS`, `BM`, etc.

## ⚠️ Privacy – please read before pushing to GitHub

The PDF contains **names and registration numbers of real students**. This repo's `.gitignore`
excludes `*.pdf`, `data/` and `web/data.js` so personal data is **never committed**.
If you want to host a public demo, use the `--anonymize` flag or generate sample data.

## Grade scale

The grade boundaries in `web/index.html` (`GRADES`) use the standard SLIIT scale:

| Grade | Min Mark |
|-------|----------|
| A+    | 90       |
| A     | 85       |
| A-    | 80       |
| B+    | 75       |
| B     | 70       |
| B-    | 65       |
| C+    | 60       |
| C     | 55       |
| C-    | 50       |
| D+    | 45       |
| D     | 40       |
| E     | < 40     |

Edit the `GRADES` array in `web/index.html` if your course uses different boundaries.

## Tests

```bash
pip install pytest && pytest
```

## Project layout

```
parse_pdf.py     PDF → web/data.js (+ data/marks.json)
                 Supports any subject; auto-detects metadata from PDF header
web/index.html   Dashboard (no build step, no external dependencies)
tests/           Parser unit tests (regex, metadata extraction, edge cases)
data/            Output directory – excluded from git (personal data)
requirements.txt pdfplumber>=0.11
```
