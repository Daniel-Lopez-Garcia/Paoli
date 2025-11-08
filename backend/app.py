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
    "password": os.getenv("DB_PASSWORD", "lexmarks07"),
    "database": os.getenv("DB_NAME", "palogroup"),
    "cursorclass": pymysql.cursors.DictCursor,
}

BASE_DIR = Path(__file__).resolve().parents[1]
FRONT_END_DIR = BASE_DIR / "front_end"
STYLE_DIR = BASE_DIR / "style"

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

def change_password(email: str, new_password: str) -> bool:
    if not email or not new_password:
        return False

    hashed = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
    query = "UPDATE user SET password_hash = %s WHERE email = %s"

    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(query, (hashed, email))
        connection.commit()  
        
        return cursor.rowcount == 1
from flask import redirect, url_for

@app.post("/reset-password")
def reset_password():
    email = request.form.get("email")          
    old_pw = request.form.get("current_password")  
    pw1   = request.form.get("password")
    pw2   = request.form.get("confirm_password")

    # Check for missing inputs
    if not email or not old_pw or not pw1 or not pw2:
         return Response("Missing Fields", status=401, mimetype="text/plain")

    # Make sure new passwords match
    if pw1 != pw2:
         return Response("Passwords Do Not Matc.", status=401, mimetype="text/plain")

    # Verify current password first
    try:
        valid_old = verify_user(email, old_pw)
        if not valid_old:
            return Response("Credentials are Incorrect.", status=401, mimetype="text/plain")

        # Proceed with password change
        changed = change_password(email, pw1)

    except Exception as exc:
        app.logger.error("Reset error: %s", exc, exc_info=True)
        return Response("Server Error.", status=401, mimetype="text/plain")

    # Check if password was actually changed
    if not changed:
        return Response("Credential are Incorrect.", status=401, mimetype="text/plain")

    # Success → redirect to login
    return redirect("/log_in.html?reset=ok", code=302)



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


@app.get("/style/<path:asset_path>")
def style_assets(asset_path):
    if not STYLE_DIR.exists():
        return Response("Style directory missing", status=500, mimetype="text/plain")
    
    return send_from_directory(STYLE_DIR, asset_path)


@app.get("/<path:asset_path>")
def static_assets(asset_path):
    return serve_frontend(asset_path)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT)
