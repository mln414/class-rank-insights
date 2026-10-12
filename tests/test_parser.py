import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse_pdf import ROW, extract_metadata


def test_row_with_mark():
    m = ROW.match("1,234 IT 25 1017 94 Jayasundara R.H. 82.66 16.532")
    assert m["idx"] == "1,234" and m["reg"] == "IT 25 1017 94"
    assert m["name"] == "Jayasundara R.H." and float(m["mark"]) == 82.66
    assert float(m["score"]) == 16.532


def test_row_absent():
    m = ROW.match("6 IT 23 7792 66 CHRISTILAN K")
    assert m["name"] == "CHRISTILAN K" and m["mark"] is None


def test_integer_mark():
    m = ROW.match("14 IT 24 1009 07 Adihetti A.R.D. 90 18")
    assert float(m["mark"]) == 90 and float(m["score"]) == 18


def test_row_different_degree_prefix():
    """Ensure parser handles other degree codes like SE, CS, BM."""
    m = ROW.match("5 SE 24 1021 33 Silva A.B. 75.5 15.1")
    assert m is not None
    assert m["reg"] == "SE 24 1021 33"
    assert m["name"] == "Silva A.B."
    assert float(m["mark"]) == 75.5


def test_metadata_subject_title_code():
    header = (
        "Sri Lanka Institute of Information Technology\n"
        "Artificial Intelligence and Machine Learning - IT2011\n"
        "Midterm - 2026\n"
        "All - Institute All - Specialization All - Regular\n"
        "Assessment Mark Weightage Score\n"
        "# Registration No Name\n"
        "Out of 100 ( 20% )\n"
    )
    meta = extract_metadata(header, Path("IT2011_Mid_Marks.pdf"))
    assert meta["subject_code"] == "IT2011"
    assert meta["subject_title"] == "Artificial Intelligence and Machine Learning"
    assert meta["exam_type"] == "Midterm"
    assert meta["year"] == "2026"
    assert meta["max_mark"] == 100.0
    assert meta["weightage"] == "20%"


def test_metadata_fallback_to_filename():
    """When header has no subject info, fall back to extracting from filename."""
    meta = extract_metadata("", Path("SE2030_Final_Results.pdf"))
    assert meta["subject_code"] == "SE2030"


def test_metadata_override():
    """Manual overrides should take precedence over auto-detected values."""
    header = "Artificial Intelligence and Machine Learning - IT2011\nMidterm - 2026\nOut of 100 ( 20% )"
    meta = extract_metadata(header, Path("results.pdf"))
    # Simulate an override from CLI args
    overrides = {"subject_code": "CS3040", "subject_title": "Data Structures"}
    for k, v in overrides.items():
        if v:
            meta[k] = v
    assert meta["subject_code"] == "CS3040"
    assert meta["subject_title"] == "Data Structures"
    # Non-overridden fields should still come from auto-detection
    assert meta["exam_type"] == "Midterm"


def test_row_format_b_with_grade_status():
    from parse_pdf import ROW_B
    m = ROW_B.match("1 IT 23 1724 32 66.6 C Pass")
    assert m is not None
    assert m.group("idx") == "1"
    assert m.group("reg") == "IT 23 1724 32"
    assert float(m.group("mark")) == 66.6
    assert m.group("grade") == "C"
    assert m.group("status") == "Pass"


def test_row_format_b_repeat_and_zero():
    from parse_pdf import ROW_B
    m1 = ROW_B.match("2663 IT 25 1040 97 89.1 R Fail")
    assert m1 and m1.group("grade") == "R" and m1.group("status") == "Fail"

    m2 = ROW_B.match("13 IT 24 1019 48 0 E Fail")
    assert m2 and float(m2.group("mark")) == 0.0 and m2.group("grade") == "E"


def test_metadata_final_exam_format():
    header = (
        "Sri Lanka Institute of Information Technology\n"
        "IT1170 - Data Structures and Algorithms\n"
        "All - Institute All - Specialization All - Regular\n"
        "Unofficial Final Grades (Official grades will be available through student profiles after the BOE)\n"
        "Examination Type :- General Examination - 2026\n"
        "No Registration No CA Marks Grade Status\n"
    )
    meta = extract_metadata(header, Path("IT1170_Final.pdf"))
    assert meta["subject_code"] == "IT1170"
    assert meta["subject_title"] == "Data Structures and Algorithms"
    assert meta["exam_type"] in ("Final", "General Examination")
    assert meta["year"] == "2026"
