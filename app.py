from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any
from uuid import uuid4

from flask import Flask, flash, g, redirect, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "inventory.db"
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev-secret-key"
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(_: Any) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    db = sqlite3.connect(DATABASE)
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL CHECK(quantity >= 0),
            price REAL NOT NULL CHECK(price >= 0),
            low_stock_threshold INTEGER NOT NULL CHECK(low_stock_threshold >= 0),
            photo_filename TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    db.close()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def dashboard() -> str:
    db = get_db()
    products = db.execute(
        """
        SELECT id, name, quantity, price, low_stock_threshold, photo_filename,
               CASE WHEN quantity <= low_stock_threshold THEN 1 ELSE 0 END AS is_low_stock
        FROM products
        ORDER BY created_at DESC, id DESC
        """
    ).fetchall()

    stats = db.execute(
        """
        SELECT
            COUNT(*) AS total_products,
            COALESCE(SUM(quantity), 0) AS total_units,
            COALESCE(SUM(quantity * price), 0) AS inventory_value,
            SUM(CASE WHEN quantity <= low_stock_threshold THEN 1 ELSE 0 END) AS low_stock_count
        FROM products
        """
    ).fetchone()

    return render_template("dashboard.html", products=products, stats=stats)


@app.post("/products")
def create_product() -> Any:
    name = request.form.get("name", "").strip()
    quantity = request.form.get("quantity", "").strip()
    price = request.form.get("price", "").strip()
    low_stock_threshold = request.form.get("low_stock_threshold", "").strip()
    photo = request.files.get("photo")

    if not name:
        flash("Product name is required.", "error")
        return redirect(url_for("dashboard"))

    try:
        quantity_value = int(quantity)
        price_value = float(price)
        low_stock_threshold_value = int(low_stock_threshold)
        if quantity_value < 0 or price_value < 0 or low_stock_threshold_value < 0:
            raise ValueError
    except ValueError:
        flash("Quantity, price, and low stock threshold must be non-negative numbers.", "error")
        return redirect(url_for("dashboard"))

    photo_filename = None
    if photo and photo.filename:
        if not allowed_file(photo.filename):
            flash("Invalid image format. Use png/jpg/jpeg/gif/webp.", "error")
            return redirect(url_for("dashboard"))
        original_name = secure_filename(photo.filename)
        extension = original_name.rsplit(".", 1)[1].lower()
        photo_filename = f"{uuid4().hex}.{extension}"
        photo.save(UPLOAD_FOLDER / photo_filename)

    db = get_db()
    db.execute(
        """
        INSERT INTO products (name, quantity, price, low_stock_threshold, photo_filename)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, quantity_value, price_value, low_stock_threshold_value, photo_filename),
    )
    db.commit()
    flash("Product created successfully.", "success")
    return redirect(url_for("dashboard"))


@app.post("/products/<int:product_id>/quantity")
def update_quantity(product_id: int) -> Any:
    quantity = request.form.get("quantity", "").strip()
    try:
        quantity_value = int(quantity)
        if quantity_value < 0:
            raise ValueError
    except ValueError:
        flash("Quantity must be a non-negative integer.", "error")
        return redirect(url_for("dashboard"))

    db = get_db()
    db.execute("UPDATE products SET quantity = ? WHERE id = ?", (quantity_value, product_id))
    db.commit()
    flash("Quantity updated.", "success")
    return redirect(url_for("dashboard"))


@app.route("/uploads/<path:filename>")
def uploaded_file(filename: str) -> Any:
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)
