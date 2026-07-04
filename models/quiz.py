from __future__ import annotations

from datetime import datetime, timezone

from app import db


class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey("labs.id"), nullable=False)
    lab_name = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    total_questions = db.Column(db.Integer, default=5, nullable=False)
    submitted_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="quiz_attempts")
    lab = db.relationship("Lab")

    __table_args__ = (db.UniqueConstraint("user_id", "lab_id", name="uq_user_lab_quiz"),)
