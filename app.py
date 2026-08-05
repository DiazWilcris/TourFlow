import os
import sqlite3
from datetime import datetime
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "tourflow.db")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "tourflow-demo-secret-change-me")
app.config["DATABASE"] = DATABASE

DEMO_USER = "organizador"
DEMO_PASSWORD = "TourFlow123!"


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS tours (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            tour_type TEXT NOT NULL,
            destination TEXT NOT NULL,
            departure_date TEXT NOT NULL,
            return_date TEXT NOT NULL,
            people_count INTEGER NOT NULL,
            transport TEXT NOT NULL,
            total_budget REAL NOT NULL,
            amount_collected REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL
        )
    """)
    db.commit()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            flash("Debes iniciar sesión para acceder.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def financial_indicator(budget, collected):
    pending = round(budget - collected, 2)
    if pending == 0:
        return "Financiada", "success"
    if pending <= budget * 0.5:
        return "En progreso", "warning"
    return "Pendiente", "danger"


def validate_tour(form):
    errors = []
    data = {key: form.get(key, "").strip() for key in (
        "name", "tour_type", "destination", "departure_date", "return_date",
        "people_count", "transport", "total_budget", "amount_collected", "status"
    )}
    if not data["name"]:
        errors.append("El nombre de la gira es obligatorio.")
    elif len(data["name"]) > 100:
        errors.append("El nombre de la gira no puede superar los 100 caracteres.")
    for field, label in (("tour_type", "El tipo de gira"), ("destination", "El destino"),
                         ("transport", "El transporte"), ("status", "El estado")):
        if not data[field]:
            errors.append(f"{label} es obligatorio.")
    try:
        people = int(data["people_count"])
        if people <= 0:
            errors.append("La cantidad de personas debe ser mayor que cero.")
    except ValueError:
        errors.append("La cantidad de personas debe ser mayor que cero.")
        people = 0
    try:
        budget = float(data["total_budget"])
        if budget <= 0:
            errors.append("El presupuesto debe ser mayor que cero.")
    except ValueError:
        errors.append("El presupuesto debe ser mayor que cero.")
        budget = 0
    try:
        collected = float(data["amount_collected"])
        if collected < 0:
            errors.append("El monto recaudado no puede ser negativo.")
        elif collected > budget:
            errors.append("El monto recaudado no puede ser mayor que el presupuesto.")
    except ValueError:
        errors.append("El monto recaudado debe ser un valor válido.")
        collected = 0
    try:
        departure = datetime.strptime(data["departure_date"], "%Y-%m-%d").date()
        returned = datetime.strptime(data["return_date"], "%Y-%m-%d").date()
        if returned <= departure:
            errors.append("La fecha de regreso debe ser posterior a la fecha de salida.")
    except ValueError:
        errors.append("Las fechas son obligatorias y deben ser válidas.")
    data.update(people_count=people, total_budget=budget, amount_collected=collected)
    return data, errors


@app.route("/")
def index():
    return redirect(url_for("dashboard" if session.get("authenticated") else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password or len(username) > 50 or not username.isalnum():
            flash("Usuario o contraseña incorrectos.", "danger")
        elif username == DEMO_USER and password == DEMO_PASSWORD:
            session["authenticated"] = True
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            flash("Credenciales incorrectas.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada correctamente.", "success")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    query = request.args.get("q", "").strip()
    db = get_db()
    sql = "SELECT * FROM tours"
    params = []
    if query:
        sql += " WHERE name LIKE ? OR destination LIKE ? OR tour_type LIKE ?"
        like = f"%{query}%"
        params = [like, like, like]
    tours = db.execute(sql + " ORDER BY departure_date", params).fetchall()
    all_stats = db.execute("""
        SELECT COUNT(*) AS total_tours, COALESCE(SUM(people_count), 0) AS total_people,
               COALESCE(SUM(total_budget), 0) AS total_budget,
               COALESCE(SUM(amount_collected), 0) AS total_collected
        FROM tours
    """).fetchone()
    decorated = []
    for tour in tours:
        item = dict(tour)
        item["pending"] = round(item["total_budget"] - item["amount_collected"], 2)
        item["indicator"], item["indicator_class"] = financial_indicator(item["total_budget"], item["amount_collected"])
        decorated.append(item)
    return render_template("dashboard.html", tours=decorated, stats=all_stats, query=query)


@app.route("/tours/new", methods=["GET", "POST"])
@login_required
def create_tour():
    if request.method == "POST":
        data, errors = validate_tour(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("tour_form.html", tour=data, action="Crear")
        db = get_db()
        db.execute("""INSERT INTO tours (name, tour_type, destination, departure_date, return_date,
                   people_count, transport, total_budget, amount_collected, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                   (data["name"], data["tour_type"], data["destination"], data["departure_date"],
                    data["return_date"], data["people_count"], data["transport"], data["total_budget"],
                    data["amount_collected"], data["status"]))
        db.commit()
        flash("Gira creada exitosamente.", "success")
        return redirect(url_for("dashboard"))
    return render_template("tour_form.html", tour={}, action="Crear")


def get_tour_or_redirect(tour_id):
    tour = get_db().execute("SELECT * FROM tours WHERE id = ?", (tour_id,)).fetchone()
    if tour is None:
        flash("Gira no encontrada.", "danger")
        return None
    return tour


@app.route("/tours/<int:tour_id>/edit", methods=["GET", "POST"])
@login_required
def edit_tour(tour_id):
    tour = get_tour_or_redirect(tour_id)
    if tour is None:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        data, errors = validate_tour(request.form)
        if errors:
            for error in errors:
                flash(error, "danger")
            data["id"] = tour_id
            return render_template("tour_form.html", tour=data, action="Actualizar")
        db = get_db()
        db.execute("""UPDATE tours SET name=?, tour_type=?, destination=?, departure_date=?, return_date=?,
                   people_count=?, transport=?, total_budget=?, amount_collected=?, status=? WHERE id=?""",
                   (data["name"], data["tour_type"], data["destination"], data["departure_date"],
                    data["return_date"], data["people_count"], data["transport"], data["total_budget"],
                    data["amount_collected"], data["status"], tour_id))
        db.commit()
        flash("Gira actualizada exitosamente.", "success")
        return redirect(url_for("dashboard"))
    return render_template("tour_form.html", tour=dict(tour), action="Actualizar")


@app.route("/tours/<int:tour_id>/delete", methods=["POST"])
@login_required
def delete_tour(tour_id):
    if get_tour_or_redirect(tour_id) is None:
        return redirect(url_for("dashboard"))
    db = get_db()
    db.execute("DELETE FROM tours WHERE id = ?", (tour_id,))
    db.commit()
    flash("Gira eliminada exitosamente.", "success")
    return redirect(url_for("dashboard"))


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True)
