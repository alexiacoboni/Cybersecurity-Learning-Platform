from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp

from app import db
from models.user import User
from utils.helpers import record_activity
from utils.security import is_locked, register_failed_login, reset_login_failures

auth_bp = Blueprint("auth", __name__)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=50)])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(3, 50)])
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Length(max=120),
            Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Enter a valid email."),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Create account")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("labs.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        if User.query.filter_by(username=username).first():
            flash("That username is already registered.", "danger")
            return render_template("register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("That email is already registered.", "danger")
            return render_template("register.html", form=form)

        user = User(username=username, email=email, role="student")
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        record_activity("registration", username, True)
        flash("Account created. You can sign in now.", "success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("labs.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data.strip()).first()
        if user and is_locked(user):
            flash("Account temporarily locked after repeated failed attempts.", "danger")
            record_activity("secure login lockout", form.username.data, False)
            return render_template("login.html", form=form)
        if user and user.check_password(form.password.data):
            reset_login_failures(user)
            login_user(user)
            record_activity("secure login", user.username, True)
            return redirect(url_for("labs.dashboard"))
        if user:
            register_failed_login(user)
        record_activity("secure login", form.username.data, False)
        flash("Invalid username or password.", "danger")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    record_activity("logout", current_user.username, True)
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
