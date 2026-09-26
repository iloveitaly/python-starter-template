import pytest
from pydantic import ValidationError
from whenever import Date

from app.lib.dates import Quarter, start_of_day


def test_start_of_day():
    date = Date(2026, 3, 15)
    sod = start_of_day(date, "America/New_York")

    assert str(sod) == "2026-03-15T00:00:00-04:00[America/New_York]"


def test_quarter_start_and_end():
    q1 = Quarter(year=2026, number=1)
    assert q1.start() == Date(2026, 1, 1)
    assert q1.end() == Date(2026, 3, 31)
    assert q1.label == "Jan - Mar 2026"

    q4 = Quarter(year=2026, number=4)
    assert q4.start() == Date(2026, 10, 1)
    assert q4.end() == Date(2026, 12, 31)
    assert q4.label == "Oct - Dec 2026"


def test_quarter_invalid_number():
    with pytest.raises(ValidationError):
        Quarter(year=2026, number=0)

    with pytest.raises(ValidationError):
        Quarter(year=2026, number=5)


def test_quarter_all_in_year():
    quarters = Quarter.all_in_year(2026)
    assert len(quarters) == 4
    assert [q.number for q in quarters] == [1, 2, 3, 4]
    assert [q.label for q in quarters] == [
        "Jan - Mar 2026",
        "Apr - Jun 2026",
        "Jul - Sep 2026",
        "Oct - Dec 2026",
    ]
