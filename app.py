from flask import Flask, request, jsonify
import psycopg2, os, uuid
from datetime import datetime, timedelta

app = Flask(__name__)
DATABASE_URL = os.environ.get("DATABASE_URL")

FREE_KEY = "FREE-ACCESS-KEY"

def db():
    return psycopg2.connect(DATABASE_URL)

def db_kur():
    with db() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                rol TEXT,
                bitis TIMESTAMP
            )
            """)
            con.commit()

db_kur()

# SÜRE HESAPLAMA
def bitis_hesapla(tip):
    now = datetime.now()
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

# KEY EKLE
@app.route("/key/ekle", methods=["POST"])
def key_ekle():
    data = request.get_json()
    rol = data.get("rol")       # vip / admin
    sure = data.get("sure")     # gunluk / haftalik / aylik / yillik / sinirsiz

    key = uuid.uuid4().hex.upper()
    bitis = bitis_hesapla(sure)

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO keys (key, rol, bitis) VALUES (%s,%s,%s)",
                (key, rol, bitis)
            )
            con.commit()

    return jsonify({"durum": "ok", "key": key, "rol": rol, "sure": sure})

# KEY SİL
@app.route("/key/sil", methods=["POST"])
def key_sil():
    key = request.get_json().get("key")

    with db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM keys WHERE key=%s", (key,))
            if cur.rowcount == 0:
                return jsonify({"durum": "hata", "mesaj": "Key yok"})
            con.commit()

    return jsonify({"durum": "ok"})

# KEY KONTROL
@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")

    # FREE KEY
    if key == FREE_KEY:
        return jsonify({
            "gecerli": True,
            "rol": "free",
            "sure": "sinirsiz"
        })

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "SELECT rol, bitis FROM keys WHERE key=%s",
                (key,)
            )
            row = cur.fetchone()

    if not row:
        return jsonify({"gecerli": False})

    rol, bitis = row

    if bitis and datetime.now() > bitis:
        return jsonify({"gecerli": False, "mesaj": "Süre doldu"})

    return jsonify({
        "gecerli": True,
        "rol": rol,
        "bitis": bitis
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
