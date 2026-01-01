from flask import Flask, jsonify, request
import psycopg2
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    return psycopg2.connect(DATABASE_URL)

# TABLO
def db_kur():
    with db() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                tur TEXT,
                bitis TIMESTAMP,
                olusturma TIMESTAMP
            )
            """)
            con.commit()

db_kur()

# SÜRE HESABI
def bitis_hesapla(tur):
    now = datetime.now()
    if tur == "admin_gunluk":
        return now + timedelta(days=1)
    if tur == "admin_haftalik":
        return now + timedelta(weeks=1)
    if tur == "admin_aylik":
        return now + timedelta(days=30)
    if tur == "admin_yillik":
        return now + timedelta(days=365)
    if tur == "admin_sinirsiz":
        return None
    return None

# KEY OLUŞTUR
@app.route("/key/olustur/<tur>")
def key_olustur(tur):
    key = uuid.uuid4().hex.upper()
    bitis = bitis_hesapla(tur)

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO keys (key, tur, bitis, olusturma) VALUES (%s,%s,%s,%s)",
                (key, tur, bitis, datetime.now())
            )
            con.commit()

    return jsonify({
        "durum": "ok",
        "key": key,
        "tur": tur,
        "bitis": str(bitis) if bitis else "sinirsiz"
    })

# KEY KONTROL
@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT tur, bitis FROM keys WHERE key=%s",
                (key,)
            )
            row = cur.fetchone()

    if not row:
        return jsonify({"gecerli": False})

    tur, bitis = row
    if bitis and datetime.now() > bitis:
        return jsonify({"gecerli": False, "sebep": "sure_bitti"})

    return jsonify({"gecerli": True, "tur": tur})

# KEY SİL
@app.route("/key/sil")
def key_sil():
    key = request.args.get("key")

    with db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM keys WHERE key=%s", (key,))
            if cur.rowcount == 0:
                return jsonify({"durum": "yok"})
            con.commit()

    return jsonify({"durum": "silindi"})

# KEY LİSTELE
@app.route("/key/liste")
def key_liste():
    with db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT key, tur, bitis FROM keys")
            rows = cur.fetchall()

    return jsonify([
        {
            "key": r[0],
            "tur": r[1],
            "bitis": str(r[2]) if r[2] else "sinirsiz"
        } for r in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
