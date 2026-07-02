# ============================================================
#  module3_database.py — Module 3: Scholarship Database
#  Handles: loading, validating and querying scholarship records
# ============================================================
"""
OOPs              : Scholarship (data model) + ScholarshipRepository
                    (behaviour) — separates data from operations.
Collections       : list[Scholarship] as the core store, dict for
                    O(1) name lookup, set for type counting.
Optimised logic   : name-indexed dict built once at load time instead
                    of a linear scan on every get_by_name() call.
Industry practice : custom exceptions, logging, dataclasses instead
                    of raw dicts (type safety + autocomplete).
Naming convention : PascalCase classes, snake_case members (PEP 8).
"""

import csv
import logging
from dataclasses import dataclass
from typing import Dict, List

logger = logging.getLogger("module3_database")

REQUIRED_FIELDS = [
    "Name", "Type", "MinMarks", "MaxIncome", "Category",
    "Gender", "Course", "Amount", "Website", "Portal",
    "Steps", "Documents", "Deadline", "MinYear",
    "MaxYear",
]


class DatabaseError(Exception):
    """Raised for CSV loading / validation problems."""


@dataclass
class Scholarship:
    """Immutable-ish record for a single scholarship (OOP data model)."""
    name: str
    type: str
    min_marks: float
    max_income: int
    category: List[str]
    gender: str
    course: str
    amount_raw: str
    website: str
    portal: str
    steps: List[str]
    documents: List[str]
    deadline: str
    min_year: int = 0
    max_year: int = 4

    @property
    def amount_display(self) -> str:
        return f"₹{int(self.amount_raw):,}" if self.amount_raw.isdigit() else self.amount_raw

    @property
    def amount_numeric(self) -> int:
        """Returns numeric amount for sorting/scoring, 0 if variable."""
        return int(self.amount_raw) if self.amount_raw.isdigit() else 0

    @staticmethod
    def from_row(row: dict) -> "Scholarship":
        return Scholarship(
            name=row["Name"],
            type=row["Type"],
            min_marks=_safe_float(row.get("MinMarks"), 0.0),
            max_income=_safe_int(row.get("MaxIncome"), 9_999_999),
            category=[c.strip() for c in row.get("Category", "").split("-") if c.strip()],
            gender=row.get("Gender", "All").strip() or "All",
            course=row.get("Course", "All").strip() or "All",
            amount_raw=row.get("Amount", "0"),
            website=row.get("Website", ""),
            portal=row.get("Portal", ""),
            steps=[s.strip() for s in row.get("Steps", "").split(",") if s.strip()],
            documents=[d.strip() for d in row.get("Documents", "").split(",") if d.strip()],
            deadline=row.get("Deadline", "Variable"),
            min_year=_safe_int(row.get("MinYear"), 0),
            max_year=_safe_int(row.get("MaxYear"), 4),
        )


def _safe_float(value, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class ScholarshipRepository:
    """Loads and serves Scholarship records — the only class that
    talks to the CSV file (Single Responsibility Principle)."""

    def __init__(self, filepath: str):
        self._filepath = filepath
        self._scholarships: List[Scholarship] = []
        self._by_name: Dict[str, Scholarship] = {}   # O(1) lookup index

    def load(self) -> List[Scholarship]:
        try:
            with open(self._filepath, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)
        except FileNotFoundError as exc:
            logger.error("Scholarship CSV not found: %s", self._filepath)
            raise DatabaseError(f"'{self._filepath}' not found.") from exc
        except OSError as exc:
            raise DatabaseError(f"Error reading CSV file: {exc}") from exc

        self._validate(rows)

        self._scholarships = [Scholarship.from_row(row) for row in rows]
        self._by_name = {s.name: s for s in self._scholarships}   # build index once
        logger.info("Loaded %d scholarships from %s", len(self._scholarships), self._filepath)
        return self._scholarships

    def _validate(self, rows: List[dict]) -> None:
        errors = []
        for i, row in enumerate(rows):
            for field_name in REQUIRED_FIELDS:
                if field_name not in row or row[field_name] == "":
                    errors.append(f"Row {i + 1} ({row.get('Name', 'Unknown')}): missing '{field_name}'")
        if errors:
            logger.warning("%d data issues found in scholarship CSV.", len(errors))
            for err in errors[:5]:
                print(f"    - {err}")

    def get_by_name(self, name: str) -> "Scholarship | None":
        return self._by_name.get(name)          # O(1) instead of linear scan

    def filter_by_type(self, stype: str) -> List[Scholarship]:
        return [s for s in self._scholarships if s.type == stype]

    def count_by_type(self) -> Dict[str, int]:
        counts = {"Government": 0, "Private": 0, "NGO": 0}
        for s in self._scholarships:
            if s.type in counts:
                counts[s.type] += 1
        return counts

    @property
    def all(self) -> List[Scholarship]:
        return self._scholarships
