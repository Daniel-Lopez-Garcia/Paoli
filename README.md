# Paoli
This is a onboarding prototype for the company Paoli for the class CCOM4075

## Local backend (Python)

1. `cd backend`
2. *(optional but recommended)* `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. `python app.py`
5. Navigate to `http://localhost:3000/log_in.html` and log in with any user whose `email`/`password_hash` exists in the database.

### Database configuration

The backend expects a local MySQL-compatible database named `palogroup` with a table `user (email VARCHAR(...), password_hash CHAR(64))`. Set credentials via environment variables before running:

- `DB_HOST` (default `localhost`)
- `DB_USER` (default `root`)
- `DB_PASSWORD` (default empty)
- `DB_NAME` (default `palogroup`)
- `HOST` (default `127.0.0.1`)
- `PORT` (default `3000`)

`password_hash` should store the SHA-256 hex digest of the user's password. The server compares the hash of the submitted password to this value.

The server also hosts the static files under `front_end`, so the existing login form can post to `/login` without any client-side changes.
