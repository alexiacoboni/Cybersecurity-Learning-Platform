from __future__ import annotations

from datetime import datetime, timezone

from flask import current_app, request
from flask_login import current_user

from app import db
from models.badge import Badge
from models.lab import Lab
from models.log import Log
from models.progress import Progress
from models.quiz import QuizAttempt


def current_username() -> str:
    if current_user.is_authenticated:
        return current_user.username
    return "anonymous"


def record_activity(
    attack: str,
    payload: str,
    success: bool,
    lab_name: str | None = None,
    result: str | None = None,
    score: int = 0,
) -> None:
    user_id = current_user.id if current_user.is_authenticated else None
    username = current_username()
    entry = Log(
        user_id=user_id,
        username=username,
        lab_name=lab_name or attack,
        user=username,
        attack=attack,
        payload=payload[:1000],
        result=result or ("success" if success else "failed"),
        success=success,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        score=score,
    )
    db.session.add(entry)
    db.session.commit()
    current_app.logger.info(
        "lab_event user=%s attack=%s success=%s payload=%r",
        entry.user,
        attack,
        success,
        payload[:120],
    )


def get_or_create_progress(user_id: int, lab_title: str) -> Progress:
    lab = Lab.query.filter_by(title=lab_title).first_or_404()
    progress = Progress.query.filter_by(user_id=user_id, lab_id=lab.id).first()
    if progress:
        return progress
    progress = Progress(user_id=user_id, lab_id=lab.id)
    db.session.add(progress)
    db.session.commit()
    return progress


def complete_lab(user_id: int, lab_title: str, score: int) -> Progress:
    progress = get_or_create_progress(user_id, lab_title)
    progress.completed = True
    progress.score = max(progress.score, score)
    now = datetime.now(timezone.utc)
    progress.updated_at = now
    if not progress.completion_date:
        progress.completion_date = now
    db.session.commit()
    unlock_badges(user_id)
    return progress


def dashboard_metrics(user_id: int) -> dict[str, int | float]:
    total_labs = Lab.query.count()
    completed = Progress.query.filter_by(user_id=user_id, completed=True).count()
    lab_score = (
        db.session.query(db.func.coalesce(db.func.sum(Progress.score), 0))
        .filter_by(user_id=user_id)
        .scalar()
    )
    quiz_score = (
        db.session.query(db.func.coalesce(db.func.sum(QuizAttempt.score), 0))
        .filter_by(user_id=user_id)
        .scalar()
    )
    percent = round((completed / total_labs) * 100) if total_labs else 0
    return {
        "total_labs": total_labs,
        "completed": completed,
        "score": lab_score + quiz_score,
        "lab_score": lab_score,
        "quiz_score": quiz_score,
        "percent": percent,
    }


def latest_completed_lab(user_id: int) -> Progress | None:
    return (
        Progress.query.filter_by(user_id=user_id, completed=True)
        .order_by(Progress.completion_date.desc().nullslast(), Progress.updated_at.desc())
        .first()
    )


def unlock_badges(user_id: int) -> list[Badge]:
    completed_titles = {
        item.lab.title
        for item in Progress.query.filter_by(user_id=user_id, completed=True).all()
    }
    score = dashboard_metrics(user_id)["score"]
    wanted = set()
    if "SQL Injection" in completed_titles:
        wanted.add("SQL Explorer")
    if "Cross-Site Scripting" in completed_titles:
        wanted.add("XSS Hunter")
    if "Brute Force" in completed_titles:
        wanted.add("Brute Force Defender")
    if completed_titles:
        wanted.add("CyberLabs Beginner")
    if len(completed_titles) >= 2 or score >= 150:
        wanted.add("CyberLabs Intermediate")
    if len(completed_titles) >= 3 and score >= 250:
        wanted.add("CyberLabs Expert")

    existing = {badge.name for badge in Badge.query.filter_by(user_id=user_id).all()}
    created = []
    for name in sorted(wanted - existing):
        badge = Badge(user_id=user_id, name=name)
        db.session.add(badge)
        created.append(badge)
    if created:
        db.session.commit()
    return Badge.query.filter_by(user_id=user_id).order_by(Badge.unlocked_at).all()
