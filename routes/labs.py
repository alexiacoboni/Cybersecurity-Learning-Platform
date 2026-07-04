from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from markupsafe import Markup
from sqlalchemy import text

from app import csrf, db, to_romania_time
from models.badge import Badge
from models.lab import Lab
from models.log import Log
from models.progress import Progress
from models.quiz import QuizAttempt
from utils.helpers import (
    complete_lab,
    dashboard_metrics,
    latest_completed_lab,
    record_activity,
    unlock_badges,
)
from utils.quiz import quiz_for_lab, score_quiz
from utils.report import build_simple_pdf
from utils.security import escaped_text

labs_bp = Blueprint("labs", __name__, url_prefix="/labs")

_brute_force_attempts: dict[str, list[datetime]] = defaultdict(list)
_stored_messages: list[dict[str, str]] = []


@labs_bp.route("/dashboard")
@login_required
def dashboard():
    labs = Lab.query.order_by(Lab.id).all()
    progress = {
        item.lab_id: item for item in Progress.query.filter_by(user_id=current_user.id)
    }
    recent_logs = (
        Log.query.filter_by(user=current_user.username)
        .order_by(Log.timestamp.desc())
        .limit(8)
        .all()
    )
    badges = unlock_badges(current_user.id)
    return render_template(
        "dashboard.html",
        labs=labs,
        progress=progress,
        metrics=dashboard_metrics(current_user.id),
        recent_logs=recent_logs,
        badges=badges,
        latest_completed=latest_completed_lab(current_user.id),
    )


@labs_bp.route("/sql", methods=["GET", "POST"])
@login_required
def sql_lab():
    vulnerable_result = None
    secure_result = None
    generated_query = None

    if request.method == "POST":
        mode = request.form.get("mode")
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if mode == "vulnerable":
            generated_query = (
                "SELECT username, role FROM users "
                f"WHERE username = '{username}' AND password_hash = '{password}'"
            )
            try:
                conn = sqlite3.connect(current_app.config["SQLALCHEMY_DATABASE_URI"][10:])
                rows = conn.execute(generated_query).fetchall()
                conn.close()
                if rows:
                    username_result, role_result = rows[0]
                    vulnerable_result = {
                        "success": True,
                        "title": "Authentication bypass successful!",
                        "username": username_result,
                        "role": "Administrator" if role_result == "admin" else role_result.title(),
                        "reason": (
                            "The injected payload modified the WHERE clause by adding "
                            "OR '1'='1', which is always TRUE. The '--' comment ignored "
                            "the password comparison."
                        ),
                    }
                else:
                    vulnerable_result = {
                        "success": False,
                        "title": "Login failed",
                        "reason": "The vulnerable query did not return a matching user.",
                    }
                record_activity(
                    "SQL injection simulation",
                    username,
                    bool(rows),
                    lab_name="SQL Injection",
                    result=vulnerable_result["title"],
                )
            except sqlite3.Error as exc:
                vulnerable_result = {
                    "success": False,
                    "title": "SQL error",
                    "reason": str(exc),
                }
                record_activity(
                    "SQL injection simulation",
                    username,
                    False,
                    lab_name="SQL Injection",
                    result="SQL error",
                )
        elif mode == "secure":
            statement = text(
                "SELECT username, role FROM users "
                "WHERE username = :username AND password_hash = :password_hash"
            )
            rows = db.session.execute(
                statement, {"username": username, "password_hash": password}
            ).fetchall()
            if rows:
                username_result, role_result = rows[0]
                secure_result = {
                    "success": True,
                    "title": "Login successful",
                    "username": username_result,
                    "role": "Administrator" if role_result == "admin" else role_result.title(),
                    "reason": "The supplied values matched an existing account exactly.",
                }
            else:
                secure_result = {
                    "success": False,
                    "title": "Login failed",
                    "reason": (
                        "The application uses parameterized queries. The payload was "
                        "treated as a normal string rather than executable SQL."
                    ),
                }
            record_activity(
                "Prepared statement simulation",
                username,
                bool(rows),
                lab_name="SQL Injection",
                result=secure_result["title"],
            )
        elif mode == "complete":
            complete_lab(current_user.id, "SQL Injection", 100)
            flash("SQL Injection lab marked complete.", "success")

    return render_template(
        "sql_lab.html",
        generated_query=generated_query,
        vulnerable_result=vulnerable_result,
        secure_result=secure_result,
    )


@labs_bp.route("/xss", methods=["GET", "POST"])
@login_required
def xss_lab():
    reflected_vulnerable = ""
    reflected_secure = ""
    stored_secure = [{"author": item["author"], "message": escaped_text(item["message"])} for item in _stored_messages]

    if request.method == "POST":
        mode = request.form.get("mode")
        payload = request.form.get("payload", "")
        if mode == "reflected":
            reflected_vulnerable = Markup(payload)
            reflected_secure = escaped_text(payload)
            record_activity(
                "Reflected XSS simulation",
                payload,
                "<script" in payload.lower(),
                lab_name="Cross-Site Scripting",
                result="Payload reflected",
            )
        elif mode == "stored":
            _stored_messages.append({"author": current_user.username, "message": payload})
            record_activity(
                "Stored XSS simulation",
                payload,
                "<script" in payload.lower(),
                lab_name="Cross-Site Scripting",
                result="Payload stored",
            )
            stored_secure = [{"author": item["author"], "message": escaped_text(item["message"])} for item in _stored_messages]
        elif mode == "complete":
            complete_lab(current_user.id, "Cross-Site Scripting", 100)
            flash("Cross-Site Scripting lab marked complete.", "success")

    return render_template(
        "xss_lab.html",
        reflected_vulnerable=reflected_vulnerable,
        reflected_secure=reflected_secure,
        stored_messages=_stored_messages,
        stored_secure=stored_secure,
    )


@labs_bp.route("/bruteforce", methods=["GET", "POST"])
@login_required
def bruteforce_lab():
    vulnerable_result = None
    secure_result = None
    simulated_attempts = []
    active_mode = None

    if request.method == "POST":
        mode = request.form.get("mode")
        active_mode = mode
        username = request.form.get("username", "student")
        passwords = [
            item.strip()
            for item in request.form.get("passwords", "").splitlines()
            if item.strip()
        ]
        correct_password = "training-pass"

        if mode == "vulnerable":
            for password in passwords[:20]:
                success = password == correct_password
                simulated_attempts.append({"password": password, "success": success})
                if success:
                    break
            vulnerable_success = any(item["success"] for item in simulated_attempts)
            vulnerable_result = {
                "success": vulnerable_success,
                "message": (
                    "Authentication successful"
                    if vulnerable_success
                    else "Authentication failed"
                ),
            }
            record_activity(
                "Brute force vulnerable simulation",
                ", ".join(passwords[:20]),
                vulnerable_success,
                lab_name="Brute Force",
                result=vulnerable_result["message"],
            )
        elif mode == "secure":
            now = datetime.now(timezone.utc)
            _brute_force_attempts[username].clear()
            for password in passwords[:20]:
                if len(_brute_force_attempts[username]) >= 5:
                    secure_result = {
                        "success": False,
                        "locked": True,
                        "message": "Account locked",
                        "remaining_attempts": 0,
                        "retry_after": 30,
                    }
                    break
                _brute_force_attempts[username].append(now)
                success = password == correct_password
                simulated_attempts.append({"password": password, "success": success})
                if success:
                    secure_result = {
                        "success": True,
                        "locked": False,
                        "message": "Authentication successful",
                        "remaining_attempts": 5 - len(_brute_force_attempts[username]),
                        "retry_after": 0,
                    }
                    _brute_force_attempts[username].clear()
                    break
            if secure_result is None:
                secure_result = {
                    "success": False,
                    "locked": len(_brute_force_attempts[username]) >= 5,
                    "message": (
                        "Account locked"
                        if len(_brute_force_attempts[username]) >= 5
                        else "Authentication failed"
                    ),
                    "remaining_attempts": max(0, 5 - len(_brute_force_attempts[username])),
                    "retry_after": 30 if len(_brute_force_attempts[username]) >= 5 else 0,
                }
            record_activity(
                "Brute force rate limit simulation",
                ", ".join(passwords[:20]),
                secure_result["success"],
                lab_name="Brute Force",
                result=secure_result["message"],
            )
        elif mode == "complete":
            complete_lab(current_user.id, "Brute Force", 100)
            flash("Brute Force lab marked complete.", "success")

    return render_template(
        "bruteforce_lab.html",
        vulnerable_result=vulnerable_result,
        secure_result=secure_result,
        simulated_attempts=simulated_attempts,
        active_mode=active_mode,
    )


@labs_bp.route("/quiz/<lab_slug>", methods=["GET", "POST"])
@login_required
def quiz(lab_slug: str):
    lab_names = {
        "sql": "SQL Injection",
        "xss": "Cross-Site Scripting",
        "bruteforce": "Brute Force",
    }
    lab_name = lab_names.get(lab_slug)
    if not lab_name:
        flash("Quiz not found.", "warning")
        return redirect(url_for("labs.dashboard"))

    lab = Lab.query.filter_by(title=lab_name).first_or_404()
    existing = QuizAttempt.query.filter_by(user_id=current_user.id, lab_id=lab.id).first()
    questions = quiz_for_lab(lab_name)

    if request.method == "POST" and not existing:
        score = score_quiz(lab_name, request.form)
        attempt = QuizAttempt(
            user_id=current_user.id,
            lab_id=lab.id,
            lab_name=lab_name,
            score=score,
            total_questions=len(questions),
        )
        db.session.add(attempt)
        db.session.commit()
        complete_lab(current_user.id, lab_name, score)
        record_activity(
            f"{lab_name} quiz",
            "quiz submitted",
            True,
            lab_name=lab_name,
            result=f"Quiz score: {score}",
            score=score,
        )
        flash(f"Quiz submitted. Score: {score}/{len(questions) * 10}.", "success")
        return redirect(url_for("labs.quiz", lab_slug=lab_slug))

    if request.method == "POST" and existing:
        flash("You already completed this quiz. Score farming is disabled.", "warning")

    return render_template(
        "quiz.html",
        lab_slug=lab_slug,
        lab_name=lab_name,
        questions=questions,
        existing=existing,
    )


@labs_bp.route("/activity")
@login_required
def activity():
    logs = (
        Log.query.filter_by(user_id=current_user.id)
        .order_by(Log.timestamp.desc())
        .limit(100)
        .all()
    )
    return render_template("activity.html", logs=logs)


@labs_bp.route("/report.pdf")
@login_required
def report_pdf():
    metrics = dashboard_metrics(current_user.id)
    progress_items = Progress.query.filter_by(user_id=current_user.id).all()
    quiz_items = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    badges = Badge.query.filter_by(user_id=current_user.id).order_by(Badge.unlocked_at).all()
    recent_logs = (
        Log.query.filter_by(user_id=current_user.id)
        .order_by(Log.timestamp.desc())
        .limit(8)
        .all()
    )
    lines = [
        f"Username: {current_user.username}",
        f"Completed labs: {metrics['completed']}/{metrics['total_labs']}",
        f"Completion percentage: {metrics['percent']}%",
        f"Final score: {metrics['score']}",
        f"Quiz score: {metrics['quiz_score']}",
        "Completed lab details:",
    ]
    lines.extend(
        f"- {item.lab.title}: {item.score} pts"
        for item in progress_items
        if item.completed
    )
    lines.append("Quiz attempts:")
    lines.extend(f"- {item.lab_name}: {item.score} pts" for item in quiz_items)
    lines.append("Badges:")
    lines.extend(f"- {badge.name}" for badge in badges)
    lines.append("Recent activity:")
    lines.extend(
        f"- {to_romania_time(log.timestamp)} | {log.lab_name or log.attack} | {log.result or log.attack}"
        for log in recent_logs
    )
    return Response(
        build_simple_pdf("CyberLabs Report", lines),
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=cyberlabs-report.pdf"},
    )


csrf.exempt(sql_lab)
csrf.exempt(xss_lab)
csrf.exempt(bruteforce_lab)
csrf.exempt(quiz)
