import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "civictrack-local-dev-key")
DB_PATH = os.environ.get("DB_PATH", str(Path(__file__).resolve().parent / "civictrack.db"))

CATEGORIES = ("Road Damage", "Garbage", "Streetlight", "Drainage", "Water Supply", "Other")
STATUSES = ("Open", "In Progress", "Resolved")


def connect_db():
    """Open SQLite with named-column access and create the database directory."""
    path = Path(DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(path), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db():
    with closing(connect_db()) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Open',
                created_at TEXT NOT NULL
            )
        """)
        connection.commit()


def issue_counts():
    with closing(connect_db()) as connection:
        rows = connection.execute(
            "SELECT status, COUNT(*) AS total FROM issues GROUP BY status"
        ).fetchall()
    counts = {status: 0 for status in STATUSES}
    for row in rows:
        counts[row["status"]] = row["total"]
    return counts


@app.get("/")
def dashboard():
    selected_status = request.args.get("status", "All")
    if selected_status not in ("All", *STATUSES):
        selected_status = "All"
    query, parameters = "SELECT * FROM issues", ()
    if selected_status != "All":
        query += " WHERE status = ?"
        parameters = (selected_status,)
    query += " ORDER BY id DESC"
    with closing(connect_db()) as connection:
        issues = connection.execute(query, parameters).fetchall()
    counts = issue_counts()
    return render_template(
        "index.html", issues=issues, counts=counts, total=sum(counts.values()),
        categories=CATEGORIES, statuses=STATUSES, selected_status=selected_status
    )


@app.post("/issues")
def create_issue():
    title = request.form.get("title", "").strip()
    category = request.form.get("category", "").strip()
    location = request.form.get("location", "").strip()
    description = request.form.get("description", "").strip()
    if not all((title, category, location, description)):
        flash("Please complete every field before submitting.", "error")
        return redirect(url_for("dashboard")), 303
    if category not in CATEGORIES:
        abort(400, description="Invalid issue category.")
    if len(title) > 100 or len(location) > 120 or len(description) > 1000:
        abort(400, description="One or more fields exceed the allowed length.")
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with closing(connect_db()) as connection:
        connection.execute(
            """INSERT INTO issues
               (title, category, location, description, status, created_at)
               VALUES (?, ?, ?, ?, 'Open', ?)""",
            (title, category, location, description, created_at)
        )
        connection.commit()
    flash("Issue reported successfully.", "success")
    return redirect(url_for("dashboard")), 303


@app.post("/issues/<int:issue_id>/status")
def update_status(issue_id):
    status = request.form.get("status", "").strip()
    if status not in STATUSES:
        abort(400, description="Invalid issue status.")
    with closing(connect_db()) as connection:
        cursor = connection.execute(
            "UPDATE issues SET status = ? WHERE id = ?", (status, issue_id)
        )
        connection.commit()
        if cursor.rowcount == 0:
            abort(404, description="Issue not found.")
    flash("Issue status updated.", "success")
    return redirect(url_for("dashboard")), 303


@app.get("/health")
def health():
    try:
        with closing(connect_db()) as connection:
            connection.execute("SELECT 1").fetchone()
        return {"status": "ok", "service": "civictrack"}, 200
    except sqlite3.Error:
        app.logger.exception("Database health check failed")
        return {"status": "error", "service": "civictrack"}, 503


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
