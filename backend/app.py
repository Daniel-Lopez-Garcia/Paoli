import hashlib
import os
from pathlib import Path

from flask import Flask, request, send_from_directory, Response
import pymysql


HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "3000"))

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "palogroup"),
    "cursorclass": pymysql.cursors.DictCursor,
}

FRONT_END_DIR = Path(__file__).resolve().parents[1] / "front_end"

app = Flask(__name__)


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def verify_user(identifier: str, plain_password: str) -> bool:
    if not identifier or not plain_password:
        return False

    hashed = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
    query = "SELECT password_hash FROM user WHERE email = %s"

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (identifier,))
            row = cursor.fetchone()

    if not row:
        return False

    return row["password_hash"] == hashed


def render_login_result(message: str) -> str:
    return (
        "<!DOCTYPE html>"
        "<html><body>"
        f"<h1>{message}</h1>"
        '<a href="/log_in.html">Back to login</a>'
        "</body></html>"
    )


@app.post("/login")
def login():
    username = request.form.get("username")
    password = request.form.get("password")

    try:
        is_valid = verify_user(username, password)
    except Exception as exc:  

        app.logger.error("Login error: %s", exc, exc_info=True)
        return Response("Internal Server Error", status=500, mimetype="text/plain")

    status = 200 if is_valid else 401
    message = "Login successful. Welcome!" if is_valid else "Invalid credentials. Try again."
    return Response(render_login_result(message), status=status, mimetype="text/html")


def serve_frontend(asset_path: str):
    if not FRONT_END_DIR.exists():
        return Response("Front-end directory missing", status=500, mimetype="text/plain")
    
    return send_from_directory(FRONT_END_DIR, asset_path)


@app.get("/")
def root():
    return serve_frontend("log_in.html")


@app.get("/<path:asset_path>")
def static_assets(asset_path):
    return serve_frontend(asset_path)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
