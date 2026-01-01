from flask import Flask, jsonify, request
import psycopg2
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = "postgresql://postgres:yasinlezoryarisirlar@db.mfesozvasdkjrgxexeev.supabase.co:5432/postgres"

def db():
    return psycopg2.connect(DATABASE_URL)

# ---- TABLO ----
def db_kur():
    with db() as con:
        cur = con.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id SERIAL PRIMARY KEY,
            key TEXT UNIQUE,
            rol TEXT,
            bitis TIMESTAMP
        )
        """)
        con.commit()

db_kur()

# ---- SÜRE HESABI ----
def sure_hesapla(tip):
    now = datetime.utcnow()
    if tip == "gunluk":
        return now + timedelta(days=1)
    if tip == "haftalik":
        return now + timedelta(weeks=1)
    if tip == "aylik":
        return now + timedelta(days=30)
    if tip == "yillik":
        return now + timedelta(days=365)
    if tip == "sinirsiz":
        return None
    return None

# ---- KEY OLUŞTUR ----
@app.route("/key/olustur/<rol>_<sure>")
def key_olustur(rol, sure):
    key = uuid.uuid4().hex.upper()
    bitis = sure_hesapla(sure)

    with db() as con:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO keys (key, rol, bitis) VALUES (%s,%s,%s)",
            (key, rol, bitis)
        )
        con.commit()

    return jsonify({
        "key": key,
        "rol": rol,
        "sure": sure
    })

# ---- KEY KONTROL ----
@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")

    with db() as con:
        cur = con.cursor()
        cur.execute("SELECT rol, bitis FROM keys WHERE key=%s", (key,))
        row = cur.fetchone()

    if not row:
        return jsonify({"gecerli": False})

    rol, bitis = row
    if bitis and datetime.utcnow() > bitis:
        return jsonify({"gecerli": False, "mesaj": "suresi doldu"})

    return jsonify({"gecerli": True, "rol": rol})

# ---- KEY SİL ----
@app.route("/key/sil")
def key_sil():
    key = request.args.get("key")

    with db() as con:
        cur = con.cursor()
        cur.execute("DELETE FROM keys WHERE key=%s", (key,))
        con.commit()

    return jsonify({"silindi": True})

# ---- KEY LİSTE ----
@app.route("/key/liste")
def key_liste():
    with db() as con:
        cur = con.cursor()
        cur.execute("SELECT key, rol, bitis FROM keys")
        rows = cur.fetchall()

    return jsonify([
        {"key": k, "rol": r, "bitis": str(b)}
        for k, r, b in rows
    ])

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
