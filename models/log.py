from __future__ import annotations

from datetime import datetime, timezone

from app import db


class Log(db.Model):
    __tablename__ = "logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    username = db.Column(db.String(80), nullable=True)
    lab_name = db.Column(db.String(80), nullable=True)
    user = db.Column(db.String(80), nullable=False)
    attack = db.Column(db.String(80), nullable=False)
    payload = db.Column(db.Text, nullable=False)
    result = db.Column(db.String(120), nullable=True)
    success = db.Column(db.Boolean, default=False, nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    score = db.Column(db.Integer, default=0, nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user_account = db.relationship("User", back_populates="logs")
