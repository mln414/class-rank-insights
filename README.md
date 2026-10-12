# IT2011 Midterm Analyzer

Turn the IT2011 midterm marks PDF into a searchable, filterable dashboard that also tells you
**how you compare with the batch** and **what to do next**.

## Features
- Students grouped by **grade** (A+ … E, plus Absent) with counts; click a grade to filter
- **Search** by name or registration number; filter by **batch** (IT23 / IT24 / IT25 …)
- Sortable, paginated table with ranks (ties share a rank)
- **"How am I doing?"** – enter your mark (or reg. no.) to get:
  - your rank, **Top X %**, and % of students you beat
  - **how many students are in your grade** and within ±2 marks
  - difference from the average and z-score
  - the **gap to the next grade** and personalised improvement suggestions

## Run it
```bash
pip install -r requirements.txt
python parse_pdf.py path/to/IT2011_Mid_Marks_Weitages.pdf   # creates web/data.js
cd web && python -m http.server 8000                        # or just open web/index.html
```
Then open http://localhost:8000.

## ⚠️ Privacy – please read before pushing to GitHub
The PDF contains **names and registration numbers of ~2,600 students**. This repo's `.gitignore`
excludes `*.pdf`, `data/` and `web/data.js` so the personal data is **not** committed. Keep the repo
code-only. If you want to host a public demo, run `python parse_pdf.py file.pdf --anonymize`
(replaces names, masks reg. numbers) or use made-up sample data.

## Grade scale
The boundaries in `web/index.html` (`GRADES`) assume the usual SLIIT scale
(A+ ≥ 90, A ≥ 85, A- ≥ 80, B+ ≥ 75, B ≥ 70, B- ≥ 65, C+ ≥ 60, C ≥ 55, C- ≥ 50, D+ ≥ 45, D ≥ 40, E < 40).
Midterm marks are out of 100 (20 % weight). **Edit the list if your handbook differs.**

## Tests
```bash
pip install pytest && pytest
```

## Project layout
```
parse_pdf.py     PDF -> web/data.js (+ data/marks.json)
web/index.html   dashboard (no build step, no dependencies)
tests/           parser tests
```
