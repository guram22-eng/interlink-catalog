import os
from flask import Flask, request, jsonify, redirect, render_template_string
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from openpyxl import load_workbook

app = Flask(__name__)
CORS(app)

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


def check_admin():
    login = request.args.get("login") or request.form.get("login")
    password = request.args.get("password") or request.form.get("password")
    return login == ADMIN_LOGIN and password == ADMIN_PASSWORD


SERIES_LIST = ["MSZ-LN", "MSZ-EF", "MSZ-AY", "MSZ-HR", "MS-GF"]
MXZ_LIST = ["MXZ-2F42", "MXZ-3F54", "MXZ-4F72", "MXZ-5F102"]


ADMIN_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Admin</title>
<style>
body{font-family:Arial;max-width:1200px;margin:20px auto;background:#f8fafc;}
.box{background:#fff;padding:15px;border-radius:12px;margin-bottom:15px;}
input,select{width:100%;padding:8px;margin-bottom:8px;}
button{padding:8px 12px;border:0;border-radius:6px;cursor:pointer;}
.add{background:#16a34a;color:#fff;}
.save{background:#2563eb;color:#fff;}
.delete{background:#dc2626;color:#fff;}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}
.item{border:1px solid #ddd;padding:10px;border-radius:10px;margin-bottom:10px;}
</style>
</head>
<body>

<h2>Добавить товар</h2>

<div class="box">
<form method="POST" action="/admin/add">
<input type="hidden" name="login" value="{{login}}">
<input type="hidden" name="password" value="{{password}}">

<select name="category">
<option value="split">split</option>
<option value="multisplit">multisplit</option>
</select>

<select name="series">
<option value="">Серия</option>
{% for s in series %}
<option>{{s}}</option>
{% endfor %}
</select>

<select name="mxz_model">
<option value="">MXZ модель</option>
{% for m in mxz %}
<option>{{m}}</option>
{% endfor %}
</select>

<input name="indoor" placeholder="Внутренний">
<input name="indoor_price" type="number" placeholder="Цена внутр">

<input name="outdoor" placeholder="Наружный">
<input name="outdoor_price" type="number" placeholder="Цена наруж">

<select name="status">
<option>В наличии</option>
<option>Под заказ</option>
</select>

<button class="add">Добавить</button>
</form>
</div>

<h2>Импорт Excel</h2>

<div class="box">
<form method="POST" action="/admin/upload" enctype="multipart/form-data">
<input type="hidden" name="login" value="{{login}}">
<input type="hidden" name="password" value="{{password}}">
<input type="file" name="file">
<button class="add">Загрузить Excel (очистит базу)</button>
</form>
</div>

<h2>Каталог</h2>

{% for item in items %}
<div class="item">

<form method="POST" action="/admin/update/{{item.id}}">
<input type="hidden" name="login" value="{{login}}">
<input type="hidden" name="password" value="{{password}}">

<div class="grid">

<select name="category">
<option value="split" {% if item.category=='split' %}selected{% endif %}>split</option>
<option value="multisplit" {% if item.category=='multisplit' %}selected{% endif %}>multisplit</option>
</select>

<input name="series" value="{{item.series or ''}}">
<input name="indoor" value="{{item.indoor or ''}}">
<input name="indoor_price" type="number" value="{{item.indoor_price or 0}}">

<input name="outdoor" value="{{item.outdoor or ''}}">
<input name="outdoor_price" type="number" value="{{item.outdoor_price or 0}}">

<input name="mxz_model" value="{{item.mxz_model or ''}}">
<input name="mxz_price" type="number" value="{{item.mxz_price or 0}}">

<select name="status">
<option {% if item.status=='В наличии' %}selected{% endif %}>В наличии</option>
<option {% if item.status=='Под заказ' %}selected{% endif %}>Под заказ</option>
</select>

</div>

<br>

<button class="save">Сохранить</button>
</form>

<form method="POST" action="/admin/delete/{{item.id}}">
<input type="hidden" name="login" value="{{login}}">
<input type="hidden" name="password" value="{{password}}">
<button class="delete">Удалить</button>
</form>

</div>
{% endfor %}

</body>
</html>
"""


@app.route("/admin")
def admin():
    if not check_admin():
        return "Access denied"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM catalog ORDER BY id DESC")
    items = cur.fetchall()
    cur.close()
    conn.close()

    return render_template_string(
        ADMIN_HTML,
        items=items,
        login=request.args.get("login"),
        password=request.args.get("password"),
        series=SERIES_LIST,
        mxz=MXZ_LIST
    )


@app.route("/admin/add", methods=["POST"])
def add():
    if not check_admin():
        return "Access denied"

    d = request.form
    category = d.get("category")

    indoor_price = int(d.get("indoor_price") or 0)
    outdoor_price = int(d.get("outdoor_price") or 0)

    mxz_price = outdoor_price
    total = indoor_price + outdoor_price if category == "split" else mxz_price

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO catalog
    (category,series,indoor,indoor_price,outdoor,outdoor_price,total,mxz_model,mxz_price,status)
    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        category,
        d.get("series"),
        d.get("indoor"),
        indoor_price,
        d.get("outdoor"),
        outdoor_price,
        total,
        d.get("mxz_model"),
        mxz_price,
        d.get("status")
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/admin/update/<int:id>", methods=["POST"])
def update(id):
    if not check_admin():
        return "Access denied"

    d = request.form
    category = d.get("category")

    indoor_price = int(d.get("indoor_price") or 0)
    outdoor_price = int(d.get("outdoor_price") or 0)
    mxz_price = int(d.get("mxz_price") or 0)

    total = indoor_price + outdoor_price if category == "split" else mxz_price

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    UPDATE catalog SET
    category=%s,series=%s,indoor=%s,indoor_price=%s,
    outdoor=%s,outdoor_price=%s,total=%s,
    mxz_model=%s,mxz_price=%s,status=%s
    WHERE id=%s
    """, (
        category,
        d.get("series"),
        d.get("indoor"),
        indoor_price,
        d.get("outdoor"),
        outdoor_price,
        total,
        d.get("mxz_model"),
        mxz_price,
        d.get("status"),
        id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/admin/delete/<int:id>", methods=["POST"])
def delete(id):
    if not check_admin():
        return "Access denied"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM catalog WHERE id=%s", (id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/admin/upload", methods=["POST"])
def upload():
    if not check_admin():
        return "Access denied"

    file = request.files["file"]
    wb = load_workbook(file)
    ws = wb.active

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("DELETE FROM catalog")

    for row in ws.iter_rows(min_row=2, values_only=True):
        category, series, indoor, indoor_price, outdoor, outdoor_price, mxz_model, mxz_price, status = row

        indoor_price = int(indoor_price or 0)
        outdoor_price = int(outdoor_price or 0)
        mxz_price = int(mxz_price or 0)

        total = indoor_price + outdoor_price if category == "split" else mxz_price

        cur.execute("""
        INSERT INTO catalog
        (category,series,indoor,indoor_price,outdoor,outdoor_price,total,mxz_model,mxz_price,status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            category, series, indoor, indoor_price,
            outdoor, outdoor_price, total,
            mxz_model, mxz_price, status
        ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/api/catalog")
def api():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM catalog ORDER BY id DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(data)


if __name__ == "__main__":
    app.run()
