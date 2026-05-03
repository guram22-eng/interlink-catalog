import os
from flask import Flask, request, jsonify, redirect, render_template_string
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
CORS(app)

# ENV (задать в Render)
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASS = os.environ.get("DB_PASS")
DB_PORT = os.environ.get("DB_PORT", "5432")

ADMIN_LOGIN = os.environ.get("ADMIN_LOGIN", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "1234")


def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS,
        port=DB_PORT,
        cursor_factory=RealDictCursor
    )


@app.route("/")
def home():
    return "Interlink Catalog API работает"


# ================= ADMIN =================

ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Admin</title>
<style>
body{font-family:Arial;max-width:900px;margin:20px auto;}
input,select{width:100%;padding:6px;margin-bottom:8px;}
button{padding:8px 12px;background:#16a34a;color:#fff;border:0;border-radius:6px;}
.card{border:1px solid #ddd;padding:10px;border-radius:10px;margin-bottom:10px;}
</style>
</head>
<body>

<h2>Добавить товар</h2>

<form method="POST" action="/admin/add">

<select name="category">
<option value="split">Split</option>
<option value="multisplit">MultiSplit</option>
</select>

<input name="series" placeholder="Серия">

<input name="indoor" placeholder="Внутренний блок">
<input name="indoor_price" placeholder="Цена внутреннего">

<input name="outdoor" placeholder="Наружный блок">
<input name="outdoor_price" placeholder="Цена наружного">

<input name="mxz_model" placeholder="MXZ модель (для мульти)">
<input name="mxz_price" placeholder="Цена MXZ">

<select name="status">
<option>В наличии</option>
<option>Под заказ</option>
</select>

<button>Сохранить</button>
</form>

<hr>

<h2>Список</h2>

{% for item in items %}
<div class="card">
<b>{{item.series}}</b><br>

{% if item.category == 'split' %}
{{item.indoor}} ({{item.indoor_price}}) + {{item.outdoor}} ({{item.outdoor_price}})
<br>ИТОГО: {{item.total}}
{% else %}
MXZ: {{item.mxz_model}} — {{item.mxz_price}}
{% endif %}

<br>Статус: {{item.status}}
</div>
{% endfor %}

</body>
</html>
"""


@app.route("/admin")
def admin():
    login = request.args.get("login")
    password = request.args.get("password")

    if login != ADMIN_LOGIN or password != ADMIN_PASSWORD:
        return "Access denied"

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM catalog ORDER BY id DESC")
    items = cur.fetchall()

    cur.close()
    conn.close()

    return render_template_string(ADMIN_HTML, items=items)


@app.route("/admin/add", methods=["POST"])
def add_item():
    data = request.form

    category = data.get("category")

    indoor_price = int(data.get("indoor_price") or 0)
    outdoor_price = int(data.get("outdoor_price") or 0)
    total = indoor_price + outdoor_price

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO catalog
    (category, series, indoor, indoor_price, outdoor, outdoor_price, total,
     mxz_model, mxz_price, status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        category,
        data.get("series"),
        data.get("indoor"),
        indoor_price,
        data.get("outdoor"),
        outdoor_price,
        total,
        data.get("mxz_model"),
        int(data.get("mxz_price") or 0),
        data.get("status")
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/admin?login=admin&password=1234")


# ================= API =================

@app.route("/api/catalog")
def catalog():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM catalog ORDER BY id DESC")
    items = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify(items)


if __name__ == "__main__":
    app.run()
