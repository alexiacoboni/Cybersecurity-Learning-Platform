from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func

from app import db
from models.lab import Lab
from models.log import Log
from models.progress import Progress
from models.user import User
from utils.security import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/")
@login_required
@admin_required
def panel():
    users = User.query.order_by(User.created_at.desc()).all()
    logs = Log.query.order_by(Log.timestamp.desc()).limit(80).all()
    recent_attacks = (
        Log.query.filter(Log.lab_name.in_(["SQL Injection", "Cross-Site Scripting", "Brute Force"]))
        .order_by(Log.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_logins = (
        Log.query.filter(Log.attack.in_(["secure login", "logout", "registration"]))
        .order_by(Log.timestamp.desc())
        .limit(10)
        .all()
    )
    common_sql_payloads = (
        db.session.query(Log.payload, func.count(Log.id).label("count"))
        .filter(Log.lab_name == "SQL Injection")
        .group_by(Log.payload)
        .order_by(func.count(Log.id).desc())
        .limit(5)
        .all()
    )
    common_xss_payloads = (
        db.session.query(Log.payload, func.count(Log.id).label("count"))
        .filter(Log.lab_name == "Cross-Site Scripting")
        .group_by(Log.payload)
        .order_by(func.count(Log.id).desc())
        .limit(5)
        .all()
    )
    brute_force_stats = {
        "attempts": Log.query.filter_by(lab_name="Brute Force").count(),
        "success": Log.query.filter_by(lab_name="Brute Force", success=True).count(),
        "failed": Log.query.filter_by(lab_name="Brute Force", success=False).count(),
    }
    labs = Lab.query.order_by(Lab.id).all()
    completed = (
        Progress.query.filter_by(completed=True)
        .join(User)
        .join(Lab)
        .order_by(Progress.updated_at.desc())
        .all()
    )
    stats = {
        "users": User.query.count(),
        "students": User.query.filter_by(role="student").count(),
        "admins": User.query.filter_by(role="admin").count(),
        "logs": Log.query.count(),
        "completed": Progress.query.filter_by(completed=True).count(),
        "labs": Lab.query.count(),
        "sql_attacks": Log.query.filter_by(lab_name="SQL Injection").count(),
        "xss_attacks": Log.query.filter_by(lab_name="Cross-Site Scripting").count(),
        "brute_force_attacks": brute_force_stats["attempts"],
    }
    progress_scores = {
        user_id: score
        for user_id, score in db.session.query(
            Progress.user_id, func.coalesce(func.sum(Progress.score), 0)
        )
        .group_by(Progress.user_id)
        .all()
    }
    quiz_scores = {
        row[0]: row[1]
        for row in db.session.execute(
            db.text("SELECT user_id, COALESCE(SUM(score), 0) FROM quiz_attempts GROUP BY user_id")
        ).fetchall()
    }
    top_users = sorted(
        [
            {
                "username": user.username,
                "score": progress_scores.get(user.id, 0) + quiz_scores.get(user.id, 0),
            }
            for user in users
        ],
        key=lambda item: item["score"],
        reverse=True,
    )[:5]
    return render_template(
        "admin.html",
        users=users,
        logs=logs,
        labs=labs,
        completed=completed,
        stats=stats,
        recent_attacks=recent_attacks,
        recent_logins=recent_logins,
        common_sql_payloads=common_sql_payloads,
        common_xss_payloads=common_xss_payloads,
        brute_force_stats=brute_force_stats,
        top_users=top_users,
    )


@admin_bp.route("/users/create", methods=["POST"])
@login_required
@admin_required
def create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    role = request.form.get("role", "student")

    if not username or not email or not password:
        flash("All fields are required.", "warning")
        return redirect(url_for("admin.panel"))

    if len(password) < 8:
        flash("Password must be at least 8 characters.", "warning")
        return redirect(url_for("admin.panel"))

    if role not in ("student", "admin"):
        role = "student"

    if User.query.filter_by(username=username).first():
        flash("That username is already registered.", "danger")
        return redirect(url_for("admin.panel"))

    if User.query.filter_by(email=email).first():
        flash("That email is already registered.", "danger")
        return redirect(url_for("admin.panel"))

    user = User(username=username, email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash(f"User '{username}' created successfully.", "success")
    return redirect(url_for("admin.panel"))


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id: int):
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "warning")
        return redirect(url_for("admin.panel"))
    if user.role == "admin" and User.query.filter_by(role="admin").count() == 1:
        flash("Cannot delete the last administrator.", "danger")
        return redirect(url_for("admin.panel"))
    db.session.delete(user)
    db.session.commit()
    flash("User deleted.", "success")
    return redirect(url_for("admin.panel"))
