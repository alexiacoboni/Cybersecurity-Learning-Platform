from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, redirect, render_template, url_for
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from config import Config

if __name__ == "__main__":
    sys.modules["app"] = sys.modules[__name__]

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

ROMANIA_TZ = ZoneInfo("Europe/Bucharest")


def to_romania_time(value: datetime, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Convert a stored UTC timestamp to Romania local time for display."""
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(ROMANIA_TZ).strftime(fmt)


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.jinja_env.filters["ro_time"] = to_romania_time

    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    configure_logging(app)
    register_blueprints(app)
    register_commands(app)

    with app.app_context():
        from models import Badge, Lab, Log, Progress, QuizAttempt, User

        db.create_all()
        ensure_schema()
        seed_labs(Lab)
        seed_admin(User)

    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("labs.dashboard"))
        return redirect(url_for("auth.login"))

    return app


def configure_logging(app: Flask) -> None:
    log_dir = Path(app.config["LOG_DIR"])
    log_dir.mkdir(exist_ok=True)
    handler = RotatingFileHandler(log_dir / "app.log", maxBytes=250_000, backupCount=3)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def register_blueprints(app: Flask) -> None:
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.labs import labs_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(labs_bp)
    app.register_blueprint(admin_bp)


def register_commands(app: Flask) -> None:
    @app.cli.command("init-db")
    def init_db() -> None:
        from models.lab import Lab
        from models.user import User

        db.drop_all()
        db.create_all()
        seed_labs(Lab)
        seed_admin(User)
        print("Database initialized with default labs and admin account.")


def ensure_schema() -> None:
    additions = {
        "logs": {
            "user_id": "INTEGER",
            "username": "VARCHAR(80)",
            "lab_name": "VARCHAR(80)",
            "result": "VARCHAR(120)",
            "ip_address": "VARCHAR(45)",
            "score": "INTEGER DEFAULT 0 NOT NULL",
        },
        "progress": {
            "completion_date": "DATETIME",
        },
    }
    for table, columns in additions.items():
        existing = {
            row[1]
            for row in db.session.execute(text(f"PRAGMA table_info({table})")).fetchall()
        }
        for name, column_type in columns.items():
            if name not in existing:
                db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {column_type}"))
    db.session.commit()


def seed_labs(Lab) -> None:
    labs = [
        {
            "title": "SQL Injection",
            "description": "Compare unsafe string-built SQL with parameterized queries.",
            "difficulty": "Beginner",
        },
        {
            "title": "Cross-Site Scripting",
            "description": "Explore reflected and stored XSS, then neutralize it with escaping.",
            "difficulty": "Beginner",
        },
        {
            "title": "Brute Force",
            "description": "Simulate repeated login attempts and defend with rate limits.",
            "difficulty": "Intermediate",
        },
    ]
    for item in labs:
        if not Lab.query.filter_by(title=item["title"]).first():
            db.session.add(Lab(**item))
    db.session.commit()


def seed_admin(User) -> None:
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@cyberlabs.local",
            password_hash=generate_password_hash("admin123"),
            role="admin",
        )
        db.session.add(admin)
        db.session.commit()


@login_manager.user_loader
def load_user(user_id: str):
    from models.user import User

    return db.session.get(User, int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=5000)
