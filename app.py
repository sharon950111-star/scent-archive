
import os
import sqlite3
from pathlib import Path

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    abort
)

app = Flask(__name__)

# 本機預設存放位置
BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB = BASE_DIR / "instance" / "scent_archive.db"

# Render 可透過環境變數指定資料庫位置
DATABASE = os.environ.get("SCENT_DB_PATH", str(LOCAL_DB))


def get_db():
    """建立資料庫連線"""
    Path(DATABASE).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建立資料表及初始資料"""

    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS scents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scent_name TEXT NOT NULL,
                scent_family TEXT NOT NULL,
                top_note TEXT,
                middle_note TEXT,
                base_note TEXT,
                projection TEXT,
                longevity TEXT,
                olfactory_impression TEXT,
                rating REAL
            )
        """)

        count = conn.execute(
            "SELECT COUNT(*) FROM scents"
        ).fetchone()[0]

        # 第一次執行時放入範例資料
        if count == 0:
            samples = [
                (
                    "Miss Dior Blooming Bouquet - Dior",
                    "Floral / 花香調",
                    "西西里柑橘",
                    "牡丹、玫瑰",
                    "白麝香",
                    "中等",
                    "約 3-5 小時",
                    "清新柔和的花香，帶有淡淡果香與乾淨的麝香氣息。",
                    4.5
                ),
                (
                    "Black Opium - YSL",
                    "Oriental / 東方調",
                    "粉紅胡椒、橙花",
                    "咖啡、茉莉",
                    "香草、雪松",
                    "強",
                    "約 7-9 小時",
                    "甜美濃郁的咖啡香，融合香草與花香氣息。",
                    4.8
                )
            ]

            conn.executemany("""
                INSERT INTO scents (
                    scent_name, scent_family,
                    top_note, middle_note, base_note,
                    projection, longevity,
                    olfactory_impression, rating
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, samples)


def row_to_dict(row):
    """將 SQLite 資料轉成模板方便使用的字典"""
    if row is None:
        return None

    scent = dict(row)

    scent["fragrance_pyramid"] = {
        "top": scent["top_note"],
        "middle": scent["middle_note"],
        "base": scent["base_note"]
    }

    scent["performance"] = {
        "projection": scent["projection"],
        "longevity": scent["longevity"]
    }

    return scent


@app.route("/")
def index():

    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scents ORDER BY id DESC"
        ).fetchall()

    scents = [row_to_dict(row) for row in rows]

    return render_template(
        "index.html",
        scents=scents
    )


@app.route("/scent/<int:scent_id>")
def detail(scent_id):

    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM scents WHERE id = ?",
            (scent_id,)
        ).fetchone()

    scent = row_to_dict(row)

    if scent is None:
        abort(404)

    return render_template(
        "detail.html",
        scent=scent
    )


@app.route("/add", methods=["GET", "POST"])
def add_scent():

    if request.method == "POST":

        scent_name = request.form.get(
            "scent_name", ""
        ).strip()

        scent_family = request.form.get(
            "scent_family", ""
        ).strip()

        impression = request.form.get(
            "olfactory_impression", ""
        ).strip()

        try:
            rating = float(request.form.get("rating", 0))
            if not 1 <= rating <= 5:
                raise ValueError
        except ValueError:
            return "評分必須介於 1 到 5", 400

        if not scent_name or not scent_family or not impression:
            return "請填寫必要欄位", 400

        data = (
            scent_name,
            scent_family,
            request.form.get("top", "").strip(),
            request.form.get("middle", "").strip(),
            request.form.get("base", "").strip(),
            request.form.get("projection", "").strip(),
            request.form.get("longevity", "").strip(),
            impression,
            rating
        )

        with get_db() as conn:
            conn.execute("""
                INSERT INTO scents (
                    scent_name, scent_family,
                    top_note, middle_note, base_note,
                    projection, longevity,
                    olfactory_impression, rating
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, data)

        return redirect(url_for("index"))

    return render_template("add_scent.html")


@app.route("/health")
def health():
    return {"status": "ok"}


# 啟動時初始化資料庫
init_db()


if __name__ == "__main__":
    app.run(debug=True)
