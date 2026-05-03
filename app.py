import os
from flask import Flask, request, jsonify, redirect, render_template_string
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor

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


@app.route("/")
def home():
    return "Interlink Catalog API работает"


def check_admin():
    login = request.args.get("login") or request.form.get("login")
    password = request.args.get("password") or request.form.get("password")
    return login == ADMIN_LOGIN and password == ADMIN_PASSWORD


ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Interlink Catalog Admin</title>
<style>
body{
  font-family:Arial,sans-serif;
  max-width:1200px;
  margin:20px auto;
  background:#f8fafc;
  color:#0f172a;
}
h1,h2{margin:0 0 14px;}
.box{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:14px;
  padding:16px;
  margin-bottom:18px;
  box-shadow:0 8px 22px rgba(15,23,42,.06);
}
.grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:10px;
}
input,select{
  width:100%;
  padding:9px;
  border:1px solid #cbd5e1;
  border-radius:8px;
  font-size:14px;
}
button{
  padding:9px 14px;
  border:0;
  border-radius:8px;
  font-weight:700;
  cursor:pointer;
}
.add{background:#16a34a;color:#fff;}
.save{background:#2563eb;color:#fff;}
.delete{background:#dc2626;color:#fff;}
.item{
  background:#fff;
  border:1px solid #e5e7eb;
  border-radius:14px;
  padding:14px;
  margin-bottom:12px;
}
.row{
  display:grid;
  grid-template-columns:repeat(8,1fr);
  gap:8px;
  align-items:center;
}
.small{font-size:12px;color:#64748b;margin-bottom:4px;}
.actions{display:flex;gap:8px;margin-top:10px;}
.total{
  font-weight:800;
  color:#16a34a;
}
@media(max-width:900px){
  .grid,.row{grid-template-columns:1fr;}
}
</style>
</head>
<body>

<h1>Interlink Catalog Admin</h1>

<div class="box">
  <h2>Добавить товар</h2>

  <form method="POST" action="/admin/add">
    <input type="hidden" name="login" value="{{login}}">
    <input type="hidden" name="password" value="{{password}}">

    <div class="grid">
      <div>
        <div class="small">Категория</div>
        <select name="category">
          <option value="split">split</option>
          <option value="multisplit">multisplit</option>
        </select>
      </div>

      <div>
        <div class="small">Серия</div>
        <input name="series" placeholder="MSZ-LN">
      </div>

      <div>
        <div class="small">Статус</div>
        <select name="status">
          <option>В наличии</option>
          <option>Под заказ</option>
        </select>
      </div>

      <div>
        <div class="small">MXZ модель</div>
        <input name="mxz_model" placeholder="MXZ-2F42VF">
      </div>

      <div>
        <div class="small">Внутренний блок</div>
        <input name="indoor" placeholder="MSZ-LN35VG2">
      </div>

      <div>
        <div class="small">Цена внутреннего</div>
        <input name="indoor_price" type="number" value="0">
      </div>

      <div>
        <div class="small">Наружный блок</div>
        <input name="outdoor" placeholder="MUZ-LN35VG">
      </div>

      <div>
        <div class="small">Цена наружного / MXZ</div>
        <input name="outdoor_price" type="number" value="0">
      </div>
    </div>

    <br>
    <button class="add">Добавить</button>
  </form>
</div>

<div class="box">
  <h2>Каталог</h2>

  {% for item in items %}
  <div class="item">
    <form method="POST" action="/admin/update/{{item.id}}">
      <input type="hidden" name="login" value="{{login}}">
      <input type="hidden" name="password" value="{{password}}">

      <div class="row">
        <div>
          <div class="small">Категория</div>
          <select name="category">
            <option value="split" {% if item.category == 'split' %}selected{% endif %}>split</option>
            <option value="multisplit" {% if item.category == 'multisplit' %}selected{% endif %}>multisplit</option>
          </select>
        </div>

        <div>
          <div class="small">Серия</div>
          <input name="series" value="{{item.series or ''}}">
        </div>

        <div>
          <div class="small">Внутренний</div>
          <input name="indoor" value="{{item.indoor or ''}}">
        </div>

        <div>
          <div class="small">Цена внутр.</div>
          <input name="indoor_price" type="number" value="{{item.indoor_price or 0}}">
        </div>

        <div>
          <div class="small">Наружный</div>
          <input name="outdoor" value="{{item.outdoor or ''}}">
        </div>

        <div>
          <div class="small">Цена наруж.</div>
          <input name="outdoor_price" type="number" value="{{item.outdoor_price or 0}}">
        </div>

        <div>
          <div class="small">MXZ / цена MXZ</div>
          <input name="mxz_model" value="{{item.mxz_model or ''}}">
        </div>

        <div>
          <div class="small">Цена MXZ</div>
          <input name="mxz_price" type="number" value="{{item.mxz_price or 0}}">
        </div>
      </div>

      <br>

      <div class="row">
        <div>
          <div class="small">Статус</div>
          <select name="status">
            <option {% if item.status == 'В наличии' %}selected{% endif %}>В наличии</option>
            <option {% if item.status == 'Под заказ' %}selected{% endif %}>Под заказ</option>
          </select>
        </div>

        <div>
          <div class="small">Итого</div>
          <div class="total">{{item.total}} ₾</div>
        </div>
      </div>

      <div class="actions">
        <button class="save">Сохранить</button>
    </form>

        <form method="POST" action="/admin/delete/{{item.id}}" onsubmit="return confirm('Удалить товар?');">
          <input type="hidden" name="login" value="{{login}}">
          <input type="hidden" name="password" value="{{password}}">
          <button class="delete">Удалить</button>
        </form>
      </div>
  </div>
  {% endfor %}
</div>

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
        password=request.args.get("password")
    )


@app.route("/admin/add", methods=["POST"])
def add_item():
    if not check_admin():
        return "Access denied"

    data = request.form
    category = data.get("category", "split")

    indoor_price = int(data.get("indoor_price") or 0)
    outdoor_price = int(data.get("outdoor_price") or 0)
    mxz_price = int(data.get("mxz_price") or 0)

    total = indoor_price + outdoor_price if category == "split" else mxz_price

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
        mxz_price,
        data.get("status")
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/admin/update/<int:item_id>", methods=["POST"])
def update_item(item_id):
    if not check_admin():
        return "Access denied"

    data = request.form
    category = data.get("category", "split")

    indoor_price = int(data.get("indoor_price") or 0)
    outdoor_price = int(data.get("outdoor_price") or 0)
    mxz_price = int(data.get("mxz_price") or 0)

    total = indoor_price + outdoor_price if category == "split" else mxz_price

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        UPDATE catalog
        SET category=%s,
            series=%s,
            indoor=%s,
            indoor_price=%s,
            outdoor=%s,
            outdoor_price=%s,
            total=%s,
            mxz_model=%s,
            mxz_price=%s,
            status=%s
        WHERE id=%s
    """, (
        category,
        data.get("series"),
        data.get("indoor"),
        indoor_price,
        data.get("outdoor"),
        outdoor_price,
        total,
        data.get("mxz_model"),
        mxz_price,
        data.get("status"),
        item_id
    ))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


@app.route("/admin/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    if not check_admin():
        return "Access denied"

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM catalog WHERE id=%s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(f"/admin?login={ADMIN_LOGIN}&password={ADMIN_PASSWORD}")


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
