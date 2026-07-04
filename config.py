from __future__ import annotations

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-before-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'database.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_TIME_LIMIT = None
    LOG_DIR = BASE_DIR / "logs"
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_SECONDS = 60
