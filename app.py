from flask import Flask, request, jsonify
import psycopg2
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔴 DB LINKINI DİREKT YAZIYORUZ
DATABASE_URL = "postgresql://panel_db_2dej_user:tb4K8BS1SGkX3tTO8ozUO8N7lVGswt0O@dpg-d5b1g38gjchc73bk7rd0-a/panel_db_2dej"

def db():
    return psycopg2.connect(DATABASE_URL)

# ---------------- DB KUR ----------------
def db_kur():
    with db() as con:
        with con.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS keys (
                id SERIAL PRIMARY KEY,
                key TEXT UNIQUE,
                tip TEXT,
                bitis TIMESTAMP
            )
            """)
            con.commit()

db_kur()

# ---------------- FREE SABİT ----------------
@app.route("/free")
def free():
    return jsonify({"durum": "ok", "tip": "free"})

# ---------------- KEY EKLE ----------------
@app.route("/key/ekle", methods=["POST"])
def key_ekle():
    data = request.json
    tip = data.get("tip")  # vip / admin
    sure = data.get("sure")  # gunluk / haftalik / aylik / yillik / sinirsiz

    now = datetime.now()
    if sure == "gunluk":
        bitis = now + timedelta(days=1)
    elif sure == "haftalik":
        bitis = now + timedelta(days=7)
    elif sure == "aylik":
        bitis = now + timedelta(days=30)
    elif sure == "yillik":
        bitis = now + timedelta(days=365)
    elif sure == "sinirsiz":
        bitis = None
    else:
        return jsonify({"hata": "sure gecersiz"})

    key = uuid.uuid4().hex.upper()

    with db() as con:
        with con.cursor() as cur:
            cur.execute(
                "INSERT INTO keys (key, tip, bitis) VALUES (%s,%s,%s)",
                (key, tip, bitis)
            )
            con.commit()

    return jsonify({"key": key, "tip": tip, "sure": sure})

# ---------------- KEY KONTROL ----------------
@app.route("/key/kontrol")
def key_kontrol():
    key = request.args.get("key")

    with db() as con:
        with con.cursor() as cur:
            cur.execute("SELECT tip, bitis FROM keys WHERE key=%s", (key,))
            row = cur.fetchone()

    if not row:
        return jsonify({"gecerli": False})

    tip, bitis = row
    if bitis and bitis < datetime.now():
        return jsonify({"gecerli": False, "mesaj": "suresi dolmus"})

    return jsonify({"gecerli": True, "tip": tip})

# ---------------- KEY SİL ----------------
@app.route("/key/sil", methods=["POST"])
def key_sil():
    key = request.json.get("key")

    with db() as con:
        with con.cursor() as cur:
            cur.execute("DELETE FROM keys WHERE key=%s", (key,))
            con.commit()

    return jsonify({"durum": "silindi"})

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
