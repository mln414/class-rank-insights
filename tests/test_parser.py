import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from parse_pdf import ROW


def test_row_with_mark():
    m = ROW.match("1,234 IT 25 1017 94 Jayasundara R.H. 82.66 16.532")
    assert m["idx"] == "1,234" and m["reg"] == "IT 25 1017 94"
    assert m["name"] == "Jayasundara R.H." and float(m["mark"]) == 82.66


def test_row_absent():
    m = ROW.match("6 IT 23 7792 66 CHRISTILAN K")
    assert m["name"] == "CHRISTILAN K" and m["mark"] is None


def test_integer_mark():
    m = ROW.match("14 IT 24 1009 07 Adihetti A.R.D. 90 18")
    assert float(m["mark"]) == 90 and float(m["score"]) == 18
