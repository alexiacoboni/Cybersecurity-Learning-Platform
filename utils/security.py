from __future__ import annotations

from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import abort, current_app
from flask_login import current_user
from markupsafe import escape

from app import db


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapped


def is_locked(user) -> bool:
    if not user or not user.locked_until:
        return False
    return datetime.now(timezone.utc) < normalize_utc(user.locked_until)


def register_failed_login(user) -> None:
    user.failed_login_attempts += 1
    if user.failed_login_attempts >= current_app.config["MAX_LOGIN_ATTEMPTS"]:
        user.locked_until = datetime.now(timezone.utc) + timedelta(
            seconds=current_app.config["LOCKOUT_SECONDS"]
        )
    db.session.commit()


def reset_login_failures(user) -> None:
    user.failed_login_attempts = 0
    user.locked_until = None
    db.session.commit()


def normalize_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def escaped_text(value: str) -> str:
    return str(escape(value))
