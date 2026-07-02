# ============================================================
#  module4_engine.py — Module 4: Eligibility Engine
#  BUGFIX: original code had a mis-indented `continue` after the
#  Year-eligibility check, so it ran unconditionally for EVERY
#  scholarship — meaning nothing could ever pass eligibility.
#  That is fixed here by nesting `continue` inside the `if`.
# ============================================================
"""
OOPs              : EligibilityEngine encapsulates all matching/
                    ranking/scoring logic as methods on a class,
                    operating on Scholarship objects (module3).
Collections       : set() for O(1) category/course membership tests
                    (was a Python 'in list' linear scan before),
                    collections.Counter for type tallies,
                    dict for combine-summary + reason tracking.
Optimised logic   : early-exit filtering, set intersection instead
                    of nested loops, single-pass scoring.
Industry practice : dataclass for results, logging, no bare prints
                    for internal errors, docstrings, type hints.
Naming convention : PascalCase classes, snake_case methods/vars.
"""

import logging
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List

from module3_database import Scholarship


logger = logging.getLogger("module4_engine")

TN_ONLY_SCHOLARSHIPS = {
    "Post Matric Scholarship SC-ST (TN)",
    "BC-MBC Scholarship (Tamil Nadu)",
    "Tamil Nadu Merit Scholarship",
    "Chief Minister Kalaignar Higher Education Assurance Scheme",
    "Dr APJ Abdul Kalam Scholarship (TN)",
    "Tamilnadu Muslim Educational and Cultural Development Society",
}

EARLY_DEADLINES = {"August", "September", "October", "November"}

DEADLINE_URGENCY_SCORE = {
    "August": 50, "September": 45, "October": 40, "November": 35,
    "December": 30, "January": 25, "Multiple": 10, "Variable": 5,
}



@dataclass
class EligibilitySummary:
    matched: List[Scholarship]
    ranked: List[Scholarship]
    by_type: Dict[str, List[Scholarship]]


class EligibilityEngine:
    """Matches a student profile against the scholarship database."""

    def __init__(self, scholarships: List[Scholarship]):
        self._scholarships = scholarships

    # ---------------- core matching ----------------
    def check_eligibility(self, profile) -> List[Scholarship]:
        matched: List[Scholarship] = []
        self.fail_reasons: Dict[str, str] = {}

        if not self._scholarships:
            logger.warning("Scholarship database is empty.")
            return []

        for s in self._scholarships:
            reason = self._first_failed_check(profile, s)
            if reason:
                self.fail_reasons[s.name] = reason
                continue
            matched.append(s)

        return matched

    def _first_failed_check(self, profile, s: Scholarship) -> str:
        """Returns a failure reason string, or '' if all checks pass."""

        # 1. Minimum marks
        if profile.percentage < s.min_marks:
            return f"Marks {profile.percentage}% < required {s.min_marks}%"

        # 2. Eligible year  (FIXED: continue now correctly scoped)
        if profile.year < s.min_year or profile.year > s.max_year:
            return f"Eligible only for Year {s.min_year} to Year {s.max_year}"

        # 3. Maximum family income
        if profile.total_income > s.max_income:
            return f"Income ₹{profile.total_income:,} > limit ₹{s.max_income:,}"

        # 4. Category — set membership, O(1) average case
        if profile.category not in set(s.category):
            return f"Category '{profile.category}' not in {s.category}"

        # 5. Gender
        if s.gender != "All" and s.gender != profile.gender:
            return f"Gender '{profile.gender}' not matching '{s.gender}'"

        # 6. State (Tamil Nadu-only scholarships)
        if s.name in TN_ONLY_SCHOLARSHIPS and profile.state != "Tamil Nadu":
            return "Tamil Nadu specific — not applicable for other states"

        # 7. Course matching
        if s.course not in ("All", "All-UG", "All-UG-PG"):
            student_course = profile.course.lower()
            scholarship_courses = {c.lower() for c in s.course.split("-")}
            course_matched = any(
                sc in student_course or student_course in sc
                for sc in scholarship_courses
            )
            if not course_matched:
                return f"Course '{profile.course}' not matching '{s.course}'"

        return ""   # all checks passed

    # ---------------- ranking / grouping ----------------
    @staticmethod
    def rank_scholarships(matched: List[Scholarship]) -> List[Scholarship]:
        return sorted(matched, key=lambda s: s.amount_numeric, reverse=True)

    @staticmethod
    def separate_by_type(ranked: List[Scholarship]) -> Dict[str, List[Scholarship]]:
        groups: Dict[str, List[Scholarship]] = {"Government": [], "Private": [], "NGO": []}
        counts = Counter(s.type for s in ranked)      # collections.Counter
        for s in ranked:
            groups.setdefault(s.type, []).append(s)
        unknown = sum(v for k, v in counts.items() if k not in groups)
        if unknown:
            logger.warning("%d scholarships have unknown type.", unknown)
        return groups


    # ---------------- scoring ----------------
    @staticmethod
    def score_scholarship(profile, s: Scholarship) -> float:
        score = 0.0
        score += (profile.percentage - s.min_marks) * 2

        if s.max_income < 300_000:
            score += 30
        elif s.max_income < 600_000:
            score += 15

        if profile.category in {"SC", "ST", "MBC"} and set(s.category) != {"OC", "BC", "MBC", "SC", "ST"}:
            score += 20

        if s.gender == "Female" and profile.gender == "Female":
            score += 25

        score += s.amount_numeric / 10_000 if s.amount_numeric else 5

        if profile.year == 0 and s.deadline in {"August", "September"}:
            score += 40   # urgent for Class-12 freshers

        return score

    # ---------------- convenience / reporting ----------------
    def get_summary(self, profile) -> EligibilitySummary:
        matched = self.check_eligibility(profile)
        ranked = self.rank_scholarships(matched)
        by_type = self.separate_by_type(ranked)
        return EligibilitySummary(matched=matched, ranked=ranked, by_type=by_type)

    def get_why_not_matched(self, matched: List[Scholarship], limit: int = 5) -> List[str]:
        matched_names = {s.name for s in matched}
        lines = []
        for s in self._scholarships:
            if s.name in matched_names:
                continue
            reason = self.fail_reasons.get(s.name, "Unknown reason")
            lines.append(f"{s.name[:40]} — {reason}")
        return lines[:limit]

    @staticmethod
    def filter_for_fresher(matched: List[Scholarship]) -> List[Scholarship]:
        priority = [s for s in matched if s.deadline in EARLY_DEADLINES]
        others = [s for s in matched if s.deadline not in EARLY_DEADLINES]
        return priority + others

    @staticmethod
    def priority_order(ranked: List[Scholarship], top_n: int = 5) -> List[Scholarship]:
        def combined_score(s: Scholarship) -> float:
            base = s.amount_numeric / 10_000 if s.amount_numeric else 5
            return base + DEADLINE_URGENCY_SCORE.get(s.deadline, 0)

        return sorted(ranked, key=combined_score, reverse=True)[:top_n]

    @staticmethod
    def deadline_alerts(ranked: List[Scholarship], top_n: int = 4) -> List[Scholarship]:
        urgency = {**DEADLINE_URGENCY_SCORE, "February": 3, "March": 2}
        return sorted(ranked, key=lambda s: urgency.get(s.deadline, 0), reverse=True)[:top_n]
