from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)
app.secret_key = "pocketsmart-secret-key"


def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


def create_database():
    conn = get_db()

        conn.execute("""
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            amount REAL DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        try:
            conn.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, password)
            )

            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            return "Email already registered."

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()

        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?",
            (email, password)
        ).fetchone()

        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db()

    expenses = conn.execute(
        """
        SELECT * FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        (session["user_id"],)
    ).fetchall()

    total_expenses = conn.execute(
        """
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = ?
        """,
        (session["user_id"],)
    ).fetchone()[0]

    # Demo income for now
    income = 35000

    # Demo monthly budget for now
    budget = 20000

    balance = income - total_expenses

    conn.close()

    return render_template(
        "dashboard.html",
        name=session["user_name"],
        expenses=expenses,
        total_expenses=total_expenses,
        income=income,
        budget=budget,
        balance=balance
    )


@app.route("/add-expense", methods=["GET", "POST"])
def add_expense():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        category = request.form["category"]
        amount = request.form["amount"]
        description = request.form["description"]

        conn = get_db()

        conn.execute(
            """
            INSERT INTO expenses
            (user_id, category, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (
                session["user_id"],
                category,
                amount,
                description
            )
        )

        conn.commit()
        conn.close()

        return redirect("/dashboard")

    return render_template("add_expense.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    create_database()
    app.run(debug=True)