from __future__ import annotations

from datetime import datetime, timezone

from app import db


class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    lab_id = db.Column(db.Integer, db.ForeignKey("labs.id"), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    completion_date = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", back_populates="progress")
    lab = db.relationship("Lab", back_populates="progress")

    __table_args__ = (db.UniqueConstraint("user_id", "lab_id", name="uq_user_lab"),)
