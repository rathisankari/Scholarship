# ============================================================
#  main.py — Application entry point
#  Wires Module 1 (Auth) -> Module 2 (UI) -> Module 3 (Database)
#  -> Module 4 (Engine) together.
# ============================================================

from module1_auth import AuthManager, run_auth_flow
from module2_ui import UIManager
from module3_database import ScholarshipRepository, DatabaseError
from module4_engine import EligibilityEngine

CSV_FILE = "scholarships.csv"


def main() -> None:
    auth = AuthManager()
    user = run_auth_flow(auth)          # Module 1: login/register gate

    ui = UIManager()                    # Module 2

    try:
        repo = ScholarshipRepository(CSV_FILE)
        scholarships = repo.load()      # Module 3
    except DatabaseError as e:
        print(f"  ❌ {e}")
        return

    engine = EligibilityEngine(scholarships)   # Module 4
    search_history = []

    while True:
        choice = ui.display_menu()

        if choice == 1:
            profile = ui.get_student_profile()
            ui.display_profile_summary(profile)

            summary = engine.get_summary(profile)
            ui.display_results(summary)
            search_history.append(profile.name)

            if not summary.ranked:
                continue

            while True:
                sub = ui.display_submenu()
                if sub == 1:
                    s = ui.display_scholarship_selector(summary.ranked)
                    ui.show_application_guide(s)
                elif sub == 2:
                    print("  ℹ️  Application status tracking coming soon.")
                elif sub == 3:
                    print("  ℹ️  Report saving coming soon.")
                elif sub == 4:
                    ui.show_document_checklist()
                elif sub == 5:
                    ui.show_deadline_alerts(engine.deadline_alerts(summary.ranked))
                elif sub == 6:
                    ui.show_scholarship_calendar(summary.ranked)
                elif sub == 7:
                    break

        elif choice == 2:
            print("  ℹ️  Application status tracking coming soon.")

        elif choice == 3:
            print("\n  SEARCH HISTORY:")
            for i, n in enumerate(search_history, 1):
                print(f"  {i}. {n}")

        elif choice == 4:
            auth.logout()
            print(f"  👋 Goodbye, {user.full_name}!")
            break


if __name__ == "__main__":
    main()
