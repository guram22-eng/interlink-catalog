from flask import Flask, request, jsonify, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")

DB_PATH = os.getenv("DATABASE_PATH", "catalog.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        status TEXT NOT NULL
    )
    """)
    conn.commit()
    conn.close()

@app.before_first_request
def setup():
    init_db()

# -------- PUBLIC --------
@app.route("/")
def home():
    return "Catalog running"

@app.route("/api/catalog")
def api_catalog():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    data = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(data)

# -------- AUTH --------
def is_auth():
    return session.get("auth") is True

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if (
            request.form.get("u") == os.getenv("ADMIN_USERNAME")
            and request.form.get("p") == os.getenv("ADMIN_PASSWORD")
        ):
            session["auth"] = True
            return redirect("/admin")
    return """
    <h3>Login</h3>
    <form method="post">
        <input name="u" placeholder="login"><br><br>
        <input name="p" type="password" placeholder="password"><br><br>
        <button>Login</button>
    </form>
    """

@app.route("/admin/logout")
def logout():
    session.clear()
    return redirect("/admin/login")

# -------- ADMIN --------
@app.route("/admin")
def admin():
    if not is_auth():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    html = """
    <h2>Catalog Admin</h2>
    <a href="/admin/logout">Logout</a>
    <hr>
    <form method="post" action="/admin/add">
        <input name="name" placeholder="Model" required>
        <input name="price" placeholder="Price" required>
        <select name="status">
            <option>В наличии</option>
            <option>Под заказ</option>
        </select>
        <button>Add</button>
    </form>
    <hr>
    """

    for r in rows:
        html += f"""
        <form method="post" action="/admin/update/{r['id']}">
            <input name="name" value="{r['name']}" required>
            <input name="price" value="{r['price']}" required>
            <input name="status" value="{r['status']}" required>
            <button>Save</button>
        </form>
        <form method="post" action="/admin/delete/{r['id']}">
            <button>Delete</button>
        </form>
        <hr>
        """

    return html

@app.route("/admin/add", methods=["POST"])
def add():
    if not is_auth():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO products (name, price, status) VALUES (?, ?, ?)",
        (
            request.form.get("name"),
            float(request.form.get("price")),
            request.form.get("status"),
        ),
    )
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/update/<int:id>", methods=["POST"])
def update(id):
    if not is_auth():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "UPDATE products SET name=?, price=?, status=? WHERE id=?",
        (
            request.form.get("name"),
            float(request.form.get("price")),
            request.form.get("status"),
            id,
        ),
    )
    conn.commit()
    conn.close()
    return redirect("/admin")

@app.route("/admin/delete/<int:id>", methods=["POST"])
def delete(id):
    if not is_auth():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin")
