from flask import Flask, request, jsonify
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
                key TEXT UNIQUE,
                tur TEXT,
                bitis TIMESTAMP
            )
            """)
            con.commit()

db_kur()

# SÜRE HESAPLAMA
def sure_hesapla(tur):
    now = datetime.now()
    if tur.endswith("_gunluk"):
        return now + timedelta(days=1)
    if tur.endswith("_haftalik"):
        return now + timedelta(weeks=1)
    if tur.endswith("_aylik"):
        return now + timedelta(days=30)
    if tur.endswith("_yillik"):
        return now + timedelta(days=365)
    if tur.endswith("_sinirsiz"):
        return None
    return None

# KEY OLUŞTUR (URL'DEN TÜR)
@app.route("/key/olustur/<tur>")
def key_olustur(tur):
    key = uuid.uuid4().hex.upper()
    bitis = sure_hesapla(tur)

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO keys (key, tur, bitis) VALUES (%s,%s,%s)",
                (key, tur, bitis)
            )
            con.commit()

    return jsonify({
        "key": key,
        "tur": tur,
        "bitis": bitis.isoformat() if bitis else "sinirsiz"
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
        return jsonify({"gecerli": False, "sebep": "suresi_bitti"})

    return jsonify({
        "gecerli": True,
        "tur": tur,
        "bitis": bitis.isoformat() if bitis else "sinirsiz"
    })

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
            cur.execute("SELECT key, tur, bitis FROM keys ORDER BY id DESC")
            rows = cur.fetchall()

    liste = []
    for k, t, b in rows:
        liste.append({
            "key": k,
            "tur": t,
            "bitis": b.isoformat() if b else "sinirsiz"
        })

    return jsonify(liste)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
