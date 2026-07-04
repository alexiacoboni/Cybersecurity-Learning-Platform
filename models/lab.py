from __future__ import annotations

from app import db


class Lab(db.Model):
    __tablename__ = "labs"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(30), nullable=False)

    progress = db.relationship(
        "Progress", back_populates="lab", cascade="all, delete-orphan"
    )
