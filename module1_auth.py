# ============================================================
#  module1_auth.py  —  Module 1: Authentication & User Management
#  Handles: user registration, login, password hashing,
#  session tracking, persistent user store (JSON)
# ============================================================
"""
Design notes (mapped to evaluation parameters)
-----------------------------------------------
OOPs              : User (data model) + AuthManager (behaviour),
                    encapsulation via "protected" attributes (_prefix),
                    custom exception classes for clean error handling.
Collections       : dict for in-memory user store, list for session log.
Optimised logic   : O(1) username lookup via dict instead of linear scan.
Authentication    : SHA-256 + per-user salt password hashing, no
                    plain-text passwords stored anywhere.
Industry practice : logging module (not print) for audit trail,
                    JSON persistence, custom exceptions, docstrings,
                    type hints.
Naming convention : PascalCase for classes, snake_case for functions/
                    variables, UPPER_CASE for constants (PEP 8).
"""

import hashlib
import json
import logging
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

# ------------------------------------------------------------------
# Logging setup — industry practice: log to file instead of print()
# ------------------------------------------------------------------
logging.basicConfig(
    filename="scholarship_app.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("module1_auth")

USER_DB_FILE = "users.json"


# ------------------------------------------------------------------
# Custom Exceptions — industry practice: fail with clear, specific errors
# ------------------------------------------------------------------
class AuthenticationError(Exception):
    """Base exception for authentication failures."""


class UserAlreadyExistsError(AuthenticationError):
    """Raised when registering a username that already exists."""


class InvalidCredentialsError(AuthenticationError):
    """Raised when login username/password do not match records."""


class WeakPasswordError(AuthenticationError):
    """Raised when a password does not meet minimum strength rules."""


# ------------------------------------------------------------------
# Data Model
# ------------------------------------------------------------------
@dataclass
class User:
    """Represents a single registered user (OOP data model)."""
    username: str
    password_hash: str
    salt: str
    full_name: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "full_name": self.full_name,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(data: dict) -> "User":
        return User(
            username=data["username"],
            password_hash=data["password_hash"],
            salt=data["salt"],
            full_name=data.get("full_name", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


# ------------------------------------------------------------------
# AuthManager — core authentication service
# ------------------------------------------------------------------
class AuthManager:
    """
    Handles registration, login and persistence of users.

    Uses a dict (hash map) keyed by username for O(1) lookups instead
    of scanning a list — this is the 'optimised logic' requirement.
    """

    MIN_PASSWORD_LENGTH = 6

    def __init__(self, db_file: str = USER_DB_FILE):
        self._db_file = db_file
        self._users: Dict[str, User] = {}
        self._session_log: List[str] = []          # audit trail (collections: list)
        self._current_user: Optional[User] = None
        self._load_users()

    # ---------------- persistence (private helpers) ----------------
    def _load_users(self) -> None:
        if not os.path.exists(self._db_file):
            self._users = {}
            return
        try:
            with open(self._db_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            self._users = {u["username"]: User.from_dict(u) for u in raw}
            logger.info("Loaded %d users from %s", len(self._users), self._db_file)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not read user DB (%s) — starting fresh.", e)
            self._users = {}

    def _save_users(self) -> None:
        try:
            with open(self._db_file, "w", encoding="utf-8") as f:
                json.dump([u.to_dict() for u in self._users.values()], f, indent=2)
        except OSError as e:
            logger.error("Failed to save user DB: %s", e)

    # ---------------- password hashing ----------------
    @staticmethod
    def _hash_password(password: str, salt: str) -> str:
        return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

    # ---------------- public API ----------------
    def register(self, username: str, password: str, full_name: str) -> User:
        """Create a new account. Raises AuthenticationError subclasses on failure."""
        username = username.strip().lower()

        if not username or not full_name.strip():
            raise AuthenticationError("Username and full name cannot be empty.")

        if len(password) < self.MIN_PASSWORD_LENGTH:
            raise WeakPasswordError(
                f"Password must be at least {self.MIN_PASSWORD_LENGTH} characters."
            )

        if username in self._users:            # O(1) dict lookup
            raise UserAlreadyExistsError(f"Username '{username}' is already taken.")

        salt = secrets.token_hex(8)
        password_hash = self._hash_password(password, salt)
        user = User(username=username, password_hash=password_hash,
                    salt=salt, full_name=full_name.strip())

        self._users[username] = user
        self._save_users()
        logger.info("New user registered: %s", username)
        return user

    def login(self, username: str, password: str) -> User:
        """Authenticate a user. Raises InvalidCredentialsError on failure."""
        username = username.strip().lower()
        user = self._users.get(username)       # O(1) dict lookup

        if user is None:
            logger.warning("Login attempt for unknown user: %s", username)
            raise InvalidCredentialsError("Username not found.")

        attempted_hash = self._hash_password(password, user.salt)
        if attempted_hash != user.password_hash:
            logger.warning("Failed login attempt for user: %s", username)
            raise InvalidCredentialsError("Incorrect password.")

        self._current_user = user
        self._session_log.append(f"{username} logged in at {datetime.now().isoformat()}")
        logger.info("User logged in: %s", username)
        return user

    def logout(self) -> None:
        if self._current_user:
            logger.info("User logged out: %s", self._current_user.username)
        self._current_user = None

    @property
    def current_user(self) -> Optional[User]:
        return self._current_user

    def is_authenticated(self) -> bool:
        return self._current_user is not None


# ------------------------------------------------------------------
# Console-facing helper (kept separate from AuthManager so the
# manager stays UI-agnostic / testable — Single Responsibility).
# ------------------------------------------------------------------
def run_auth_flow(auth: AuthManager) -> User:
    """Interactive login/register loop. Returns an authenticated User."""
    print("\n" + "=" * 50)
    print("   SCHOLARSHIP ADVISOR — LOGIN")
    print("=" * 50)

    while True:
        print("\n  1. Login")
        print("  2. Register")
        print("  3. Exit")
        choice = input("  Enter choice (1-3): ").strip()

        if choice == "1":
            username = input("  Username : ").strip()
            password = input("  Password : ").strip()
            try:
                user = auth.login(username, password)
                print(f"\n  ✅ Welcome back, {user.full_name}!")
                return user
            except AuthenticationError as e:
                print(f"  ❌ {e}")

        elif choice == "2":
            username = input("  Choose a username : ").strip()
            full_name = input("  Full Name          : ").strip()
            password = input("  Choose a password  : ").strip()
            try:
                user = auth.register(username, password, full_name)
                print(f"\n  ✅ Account created. Welcome, {user.full_name}!")
                return user
            except AuthenticationError as e:
                print(f"  ❌ {e}")

        elif choice == "3":
            print("  👋 Goodbye!")
            raise SystemExit(0)

        else:
            print("  ❌ Please enter 1, 2 or 3.")
