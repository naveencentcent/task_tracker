# app.py

import os
import csv
import io
from datetime import datetime, date

from flask import Flask, render_template, request, redirect, url_for, send_file
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from flask_login import UserMixin

# -----------------------------
# Create Flask App
# -----------------------------

app = Flask(__name__)

# -----------------------------
# Database Configuration
# -----------------------------

database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Render gives postgres:// but SQLAlchemy needs postgresql://
    database_url = database_url.replace("postgres://", "postgresql://")
else:
    # fallback for local development
    database_url = "sqlite:///tasks.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# -----------------------------
# Login Manager
# -----------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -----------------------------
# Models
# -----------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    tasks = db.relationship("Task", backref="owner", lazy=True)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    details = db.Column(db.Text)
    notes = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    completed_on = db.Column(db.Date)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def days_taken(self):
        if self.completed_on:
            return (self.completed_on - self.start_date).days
        return None

    def is_overdue(self):
        return self.status != "Completed" and date.today() > self.end_date


# 🔥 Visitor Counter Model
class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)


# -----------------------------
# Create Tables + Initialize Visitor Row
# -----------------------------

with app.app_context():
    db.create_all()

    if not Visitor.query.first():
        db.session.add(Visitor(count=0))
        db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# -----------------------------
# Authentication Routes
# -----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        hashed_password = generate_password_hash(request.form["password"])
        user = User(
            username=request.form["username"],
            password=hashed_password,
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(
            username=request.form["username"]
        ).first()

        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("index"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# -----------------------------
# Task Routes
# -----------------------------

@app.route("/")
@login_required
def index():
    # 🔥 Increment Visitor Counter
    visitor = Visitor.query.first()
    visitor.count += 1
    db.session.commit()

    tasks = Task.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "index.html",
        tasks=tasks,
        today=date.today(),
        visitor_count=visitor.count
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():
    if request.method == "POST":
        task = Task(
            title=request.form["title"],
            details=request.form.get("details"),
            notes=request.form.get("notes"),
            start_date=datetime.strptime(
                request.form["start_date"], "%Y-%m-%d"
            ).date(),
            end_date=datetime.strptime(
                request.form["end_date"], "%Y-%m-%d"
            ).date(),
            status=request.form["status"],
            user_id=current_user.id,
        )

        db.session.add(task)
        db.session.commit()
        return redirect(url_for("index"))

    return render_template("task_form.html")


@app.route("/complete/<int:task_id>")
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(
        id=task_id,
        user_id=current_user.id,
    ).first()

    if task:
        task.status = "Completed"
        task.completed_on = date.today()
        db.session.commit()

    return redirect(url_for("index"))


@app.route("/export")
@login_required
def export():
    tasks = Task.query.filter_by(user_id=current_user.id).all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(
        ["ID", "Title", "Details", "Start", "End", "Status"]
    )

    for task in tasks:
        writer.writerow(
            [
                task.id,
                task.title,
                task.details,
                task.start_date,
                task.end_date,
                task.status,
            ]
        )

    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode()),
        download_name="tasks.csv",
        as_attachment=True,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)