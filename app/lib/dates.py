"""
Generic date helpers built on `whenever`.
"""

from typing import ClassVar

from pydantic import BaseModel as PydanticBaseModel
from pydantic import Field, computed_field
from whenever import Date, Time, ZonedDateTime


def start_of_day(date: Date, tz: str) -> ZonedDateTime:
    "midnight at the beginning of `date` in the IANA timezone `tz`"

    return date.at(Time.MIDNIGHT).assume_tz(tz)


class Quarter(PydanticBaseModel):
    "a calendar quarter, e.g. Q1 2027 is `Quarter(year=2027, number=1)`"

    MONTHS_PER_QUARTER: ClassVar[int] = 3
    QUARTERS_PER_YEAR: ClassVar[int] = 4

    year: int
    number: int = Field(ge=1, le=QUARTERS_PER_YEAR)

    @classmethod
    def all_in_year(cls, year: int) -> list[Quarter]:
        return [
            cls(year=year, number=number)
            for number in range(1, cls.QUARTERS_PER_YEAR + 1)
        ]

    def start(self) -> Date:
        "first day of the quarter"

        return Date(self.year, (self.number - 1) * self.MONTHS_PER_QUARTER + 1, 1)

    def end(self) -> Date:
        "last day of the quarter"

        return self.start().add(months=self.MONTHS_PER_QUARTER).subtract(days=1)

    @computed_field
    @property
    def label(self) -> str:
        "e.g. `Jan - Mar 2027`"

        return f"{self.start().format('MMM')} - {self.end().format('MMM')} {self.year}"
