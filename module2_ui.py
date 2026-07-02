
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from module3_database import Scholarship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module4_engine import EligibilitySummary


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
@dataclass
class StudentProfile:
    name: str
    year: int                       # 0 = Class 12 graduate, 1-4 = college year
    course: str
    percentage: float
    category: str
    gender: str
    state: str
    father_name: str
    father_occupation: str
    father_income: int
    mother_name: str
    mother_occupation: str
    mother_income: int
    entrance_exam: Optional[str] = None

    @property
    def total_income(self) -> int:
        return self.father_income + self.mother_income

    @property
    def academic_status(self) -> str:
        return "Class 12 Graduate" if self.year == 0 else "College Student"

    @property
    def year_label(self) -> str:
        return "Not Yet Joined College" if self.year == 0 else f"Year {self.year}"


# ------------------------------------------------------------------
# UI Manager — all console interaction lives here
# ------------------------------------------------------------------
class UIManager:

    COURSE_MAP = {1: "Engineering", 2: "Medical", 3: "Arts-Science", 4: "Law", 5: "Other"}
    CATEGORY_MAP = {1: "OC", 2: "BC", 3: "MBC", 4: "SC", 5: "ST", 6: "Minority"}
    OCCUPATION_MAP = {1: "Farmer", 2: "Daily Labour", 3: "Govt Employee",
                       4: "Private Employee", 5: "Business", 6: "Other"}
    MOTHER_OCC_MAP = {1: "Homemaker", 2: "Farmer", 3: "Daily Labour",
                       4: "Govt Employee", 5: "Private Employee", 6: "Other"}
    EXAM_MAP = {1: "JEE", 2: "NEET", 3: "TNEA", 4: "Other Entrance", 5: "None"}

    # ---------------- generic reusable prompts ----------------
    @staticmethod
    def _prompt_int(label: str, valid_range: range, error: str = "Please enter a valid number.") -> int:
        while True:
            try:
                value = int(input(label))
                if value in valid_range:
                    return value
                print(f"  ❌ {error}")
            except ValueError:
                print("  ❌ Please enter a number.")

    @staticmethod
    def _prompt_text(label: str, allow_empty: bool = False, letters_only: bool = False) -> str:
        while True:
            value = input(label).strip()
            if not value and not allow_empty:
                print("  ❌ This field cannot be empty.")
                continue
            if letters_only and value and not value.replace(" ", "").isalpha():
                print("  ❌ Must contain letters only.")
                continue
            return value

    @staticmethod
    def _prompt_float(label: str, low: float, high: float) -> float:
        while True:
            try:
                value = float(input(label))
                if low <= value <= high:
                    return value
                print(f"  ❌ Value must be between {low} and {high}.")
            except ValueError:
                print("  ❌ Please enter a valid number like 85 or 78.5")

    @staticmethod
    def _prompt_non_negative_int(label: str) -> int:
        while True:
            try:
                value = int(input(label))
                if value >= 0:
                    return value
                print("  ❌ Value cannot be negative.")
            except ValueError:
                print("  ❌ Please enter a number without commas.")

    def _prompt_from_map(self, title: str, options: Dict[int, str], label: str) -> str:
        print(f"\n  {title}")
        for key, val in options.items():
            print(f"  {key}. {val}")
        choice = self._prompt_int(label, range(1, len(options) + 1), "Please choose a valid option.")
        return options[choice]

    # ---------------- main menu ----------------
    def display_menu(self) -> int:
        print("\n" + "-" * 50)
        print("   SCHOLARSHIP ADVISOR — MAIN MENU")
        print("-" * 50)
        print("  1.  Search Scholarships")
        print("  2.  View Application Status")
        print("  3.  View Search History")
        print("  4.  Exit")
        print("-" * 50)
        return self._prompt_int("  Enter your choice (1-4): ", range(1, 5))

    def display_submenu(self) -> int:
        print("\n  What would you like to do?")
        options = ["View Application Guide", "Update Application Status", "Save Report",
                   "Show Document Checklist", "Show Deadline Alerts",
                   "Show Scholarship Calendar", "Back to Main Menu"]
        for i, opt in enumerate(options, 1):
            print(f"  [{i}]  {opt}")
        return self._prompt_int("  Enter choice (1-7): ", range(1, 8))

    # ---------------- profile collection ----------------
    def get_student_profile(self) -> StudentProfile:
        print("  STUDENT PROFILE — ENTER YOUR DETAILS")
        name = self._prompt_text("  Enter Student Name        : ", letters_only=True)

        print("\n  Are you in college or just passed Class 12?")
        print("  0.  Just Passed Class 12 — Not Yet Joined College")
        print("  1-4. Nth Year College")
        year = self._prompt_int("  Enter Choice (0-4)        : ", range(0, 5))

        if year == 0:
            course = self._prompt_from_map("What course are you planning to join?",
                                            self.COURSE_MAP, "  Select Course (1-5)       : ")
        else:
            course = self._prompt_text("  Enter Current Course      : ")

        marks_label = "  Enter Class 12 Percentage : " if year == 0 else "  Enter Current Percentage  : "
        percentage = self._prompt_float(marks_label, 0, 100)

        category = self._prompt_from_map("Category Options:", self.CATEGORY_MAP,
                                          "  Select Category (1-6)     : ")

        gender = "Male" if self._prompt_int("\n  Gender: 1.Male 2.Female -> ", range(1, 3)) == 1 else "Female"
        state = "Tamil Nadu" if self._prompt_int("\n  State: 1.Tamil Nadu 2.Other -> ", range(1, 3)) == 1 else "Other"

        entrance_exam = None
        if year == 0:
            entrance_exam = self._prompt_from_map("Have you appeared for any entrance exam?",
                                                   self.EXAM_MAP, "  Select (1-5)              : ")

        father_name = self._prompt_text("  Father Name               : ", letters_only=True)
        father_occ = self._prompt_from_map("Father Occupation:", self.OCCUPATION_MAP,
                                            "  Select Occupation (1-6)   : ")
        father_income = self._prompt_non_negative_int("  Father Annual Income (₹)  : ")

        mother_name = self._prompt_text("  Mother Name               : ", letters_only=True)
        mother_occ = self._prompt_from_map("Mother Occupation:", self.MOTHER_OCC_MAP,
                                            "  Select Occupation (1-6)   : ")
        mother_income = self._prompt_non_negative_int("  Mother Annual Income (₹)  : ")

        profile = StudentProfile(
            name=name, year=year, course=course, percentage=percentage,
            category=category, gender=gender, state=state,
            father_name=father_name, father_occupation=father_occ, father_income=father_income,
            mother_name=mother_name, mother_occupation=mother_occ, mother_income=mother_income,
            entrance_exam=entrance_exam,
        )
        print(f"  ✅ Total Family Income : ₹{profile.total_income:,}")
        return profile

    # ---------------- display helpers ----------------
    def display_profile_summary(self, profile: StudentProfile) -> None:
        print("\n" + "-" * 50)
        print("   YOUR PROFILE SUMMARY")
        print("-" * 50)
        print(f"  Name            : {profile.name}")
        print(f"  Academic Status : {profile.academic_status}")
        print(f"  Course          : {profile.course}")
        print(f"  Year            : {profile.year_label}")
        print(f"  Percentage      : {profile.percentage}%")
        print(f"  Category        : {profile.category}  |  Gender: {profile.gender}")
        print(f"  State           : {profile.state}")
        if profile.year == 0:
            print(f"  Entrance Exam   : {profile.entrance_exam or 'Not specified'}")
        print(f"  Father          : {profile.father_name} ({profile.father_occupation}) — ₹{profile.father_income:,}")
        print(f"  Mother          : {profile.mother_name} ({profile.mother_occupation}) — ₹{profile.mother_income:,}")
        print(f"  Total Income    : ₹{profile.total_income:,}")
        if profile.year == 0:
            print("\n  ℹ️  Showing scholarships for students ENTERING college.")
        print("-" * 50)

    def display_results(self, summary) -> None:
        print("\n" + "-" * 50)
        print("   ELIGIBLE SCHOLARSHIPS FOUND")
        print("-" * 50)

        if not summary.ranked:
            print("  ❌ No scholarships matched your profile.")
            return

        for title in ("Government", "Private", "NGO"):
            group = summary.by_type.get(title, [])
            if group:
                print(f"\n  ── {title.upper()} SCHOLARSHIPS ({len(group)} found) ──")
                for i, s in enumerate(group, 1):
                    print(f"  {i}. {s.name}")
                    print(f"     Amount: {s.amount_display}  |  Deadline: {s.deadline}")

        print("\n" + "-" * 50)
        print(f"   📋 Total Matched: {len(summary.ranked)}")
        print("-" * 50)

    def display_scholarship_selector(self, ranked: List[Scholarship]) -> Scholarship:
        print("\n  Select a Scholarship:")
        for i, s in enumerate(ranked, 1):
            print(f"  [{i}]  {s.name}")
        choice = self._prompt_int(f"  Enter choice (1-{len(ranked)}): ", range(1, len(ranked) + 1))
        return ranked[choice - 1]

    def show_application_guide(self, s: Scholarship) -> None:
        print("\n" + "-" * 50)
        print(f"   APPLICATION GUIDE — {s.name}")
        print("-" * 50)
        print(f"\n  🌐  Official Website : {s.website}")
        print(f"  🔗  Apply Portal     : {s.portal}")
        print("\n  How to Apply:")
        for step in s.steps:
            print(f"    {step}")
        print("\n  Documents You Need:")
        for doc in s.documents:
            print(f"    ✅  {doc}")
        print(f"\n    Amount   : {s.amount_display}")
        print(f"    Deadline : {s.deadline}")
        print("-" * 50)

    def show_document_checklist(self) -> None:
        master_docs = [
            "Student Aadhaar Card", "Passport Size Photograph", "Class 10 Mark Sheet",
            "Class 12 Mark Sheet", "Previous Semester/Year Mark Sheet (if applicable)",
            "College Bonafide / Admission Certificate", "Income Certificate",
            "Community / Caste Certificate (if applicable)", "Bank Passbook (Student Account)",
            "Bank Account Number & IFSC Code", "Student Mobile Number", "Student Email ID",
            "Parent/Guardian Aadhaar Card", "Father Occupation & Income Details",
            "Mother Occupation & Income Details", "Ration Card (if applicable)",
            "Transfer Certificate", "OTR ID (for NSP Scholarships)",
            "First Graduate Certificate (if applicable)", "Disability Certificate (if applicable)",
            "Single Parent / Orphan Certificate (if applicable)",
            "Achievements / Sports / Awards Certificates (if applicable)",
        ]
        print("\n   📋 YOUR MASTER DOCUMENT CHECKLIST")
        for i, doc in enumerate(master_docs, 1):
            print(f"  {i:2}. ☐ {doc}")
        print(f"\n  Total Common Documents : {len(master_docs)}")
        print("-" * 50)

    def show_deadline_alerts(self, alerts: List[Scholarship]) -> None:
        print("\n" + "-" * 50)
        print("  ⚠️  DEADLINE ALERTS — Apply These First:")
        print("-" * 50)
        for s in alerts:
            print(f"  🔴  {s.name[:38]}")
            print(f"       Amount: {s.amount_display}  |  Deadline: {s.deadline}")
        print("-" * 50)

    def show_priority_order(self, priority: List[Scholarship]) -> None:
        print("\n" + "-" * 50)
        print("  📌 RECOMMENDED APPLY ORDER:")
        print("-" * 50)
        for i, s in enumerate(priority, 1):
            print(f"  {i}. {s.name}")
            print(f"     Amount: {s.amount_display} | Deadline: {s.deadline}")
        print("-" * 50)

    def show_scholarship_calendar(self, ranked: List[Scholarship]) -> None:
        month_order = ["August", "September", "October", "November", "December",
                        "January", "February", "March", "Multiple", "Variable"]
        calendar: Dict[str, List[str]] = {}
        for s in ranked:
            calendar.setdefault(s.deadline, []).append(s.name)

        print("\n" + "-" * 50)
        print("  📅  YOUR SCHOLARSHIP CALENDAR:")
        print("-" * 50)
        for month in month_order:
            if month in calendar:
                print(f"\n  {month}:")
                for name in calendar[month]:
                    print(f"    →  {name[:45]}")
        print("-" * 50)

    def show_why_not_matched(self, reasons: List[str]) -> None:
        if not reasons:
            print("  ✅ You matched all available scholarships!")
            return
        print("\n" + "-" * 50)
        print("  WHY SOME SCHOLARSHIPS DID NOT MATCH:")
        print("-" * 50)
        for line in reasons:
            print(f"  ✗  {line}")
        print("-" * 50)
