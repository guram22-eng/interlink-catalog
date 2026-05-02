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
        name TEXT,
        price REAL,
        status TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "Catalog running"

@app.route("/api/catalog")
def catalog():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    data = [dict(row) for row in cur.fetchall()]
    return jsonify(data)

def check_login():
    return session.get("auth")

@app.route("/admin/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["u"] == os.getenv("ADMIN_USERNAME") and request.form["p"] == os.getenv("ADMIN_PASSWORD"):
            session["auth"] = True
            return redirect("/admin")
    return '''
    <form method="post">
    <input name="u"><input name="p" type="password">
    <button>Login</button>
    </form>
    '''

@app.route("/admin")
def admin():
    if not check_login():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM products")
    rows = cur.fetchall()

    html = "<h2>Admin</h2>"

    html += '''
    <form method="post" action="/add">
    <input name="name">
    <input name="price">
    <input name="status">
    <button>Add</button>
    </form><hr>
    '''

    for r in rows:
        html += f'''
        <form method="post" action="/update/{r['id']}">
        <input name="name" value="{r['name']}">
        <input name="price" value="{r['price']}">
        <input name="status" value="{r['status']}">
        <button>Save</button>
        </form>
        <form method="post" action="/delete/{r['id']}">
        <button>Delete</button>
        </form><hr>
        '''

    return html

@app.route("/add", methods=["POST"])
def add():
    if not check_login():
        return redirect("/admin/login")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO products (name, price, status) VALUES (?, ?, ?)",
                (request.form["name"], request.form["price"], request.form["status"]))
    conn.commit()
    return redirect("/admin")

@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE products SET name=?, price=?, status=? WHERE id=?",
                (request.form["name"], request.form["price"], request.form["status"], id))
    conn.commit()
    return redirect("/admin")

@app.route("/delete/<int:id>", methods=["POST"])
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM products WHERE id=?", (id,))
    conn.commit()
    return redirect("/admin")
