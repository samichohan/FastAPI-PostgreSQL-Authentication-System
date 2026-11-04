# Auth System – FastAPI + PostgreSQL

A beginner-friendly backend for **user signup, login and JWT authentication**.

## Features
- Signup with full name, email, password and confirm password
- Email format validation + duplicate email rejection
- Password strength rules (8+ chars, upper, lower, number, special character)
- Passwords hashed with **Argon2** (plain passwords are never stored)
- Login returns a signed **JWT access token** with an expiry time
- Protected route `GET /auth/me` using a reusable dependency
- Clear JSON errors with correct HTTP status codes
- Secrets (DB password, JWT secret) kept in `.env`

## Technology Stack
Python 3.11+ · FastAPI · PostgreSQL · SQLAlchemy ORM · Psycopg 3 · Pydantic · Pydantic Settings · Argon2 (argon2-cffi) · PyJWT · Uvicorn

## Folder Structure
```
auth-system/
├── app/
│   ├── main.py        # creates the FastAPI app, creates tables on startup
│   ├── config.py      # reads settings from .env
│   ├── database.py    # PostgreSQL connection + get_db dependency
│   ├── models.py      # SQLAlchemy "users" table
│   ├── schemas.py     # Pydantic request/response validation
│   ├── security.py    # Argon2 hashing, JWT create/verify, get_current_user
│   └── routes/auth.py # /auth/signup, /auth/login, /auth/me
├── .env               # your real secrets (NOT committed)
├── .env.example       # template with placeholders
├── .gitignore
├── requirements.txt
└── README.md
```

## Installation (Windows PowerShell)

### 1. Create and activate a virtual environment
```powershell
cd auth-system
python -m venv venv
.\venv\Scripts\Activate.ps1
```
If PowerShell blocks the script, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 2. Install dependencies
```powershell
pip install -r requirements.txt
```

### 3. Create the PostgreSQL database
Make sure PostgreSQL is installed and running, then:
```powershell
psql -U postgres -c "CREATE DATABASE auth_db;"
```
(Enter the password you chose when installing PostgreSQL.)
If `psql` is not recognized, use **pgAdmin** → right-click *Databases* → *Create* → *Database* → name it `auth_db`.

The `users` table is created automatically when the app starts.

### 4. Configure `.env`
```powershell
Copy-Item .env.example .env
```
Generate a strong JWT secret:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```
Open `.env` and fill in:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=auth_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password_here
JWT_SECRET_KEY=paste_the_generated_secret_here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Run the app
```powershell
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs**

## API Endpoints
| Method | URL            | Auth | Success | Description |
|--------|----------------|------|---------|-------------|
| POST   | `/auth/signup` | No   | 201     | Register a user |
| POST   | `/auth/login`  | No   | 200     | Returns `access_token` and `token_type` |
| GET    | `/auth/me`     | Yes  | 200     | Returns id, full_name, email of current user |

Error codes: `400` duplicate email / password mismatch · `401` bad credentials or bad/expired token · `422` validation error.

## Testing with Swagger UI (`/docs`)
1. **Signup** → `POST /auth/signup` → *Try it out* → use:
   ```json
   {"full_name": "Ali Khan", "email": "ali@example.com", "password": "Strong@123", "confirm_password": "Strong@123"}
   ```
   Expect `201`.
2. Repeat the same request → `400` (duplicate email).
3. Change `confirm_password` → `400` (mismatch).
4. Use `"email": "abc"` → `422` (invalid email).
5. **Login** → `POST /auth/login` with email + password → `200`, copy the `access_token`.
6. Wrong password → `401`.
7. Click the green **Authorize** button (top right), paste the token (only the token, no word "Bearer"), click *Authorize*.
8. `GET /auth/me` → `200` with your profile.
9. Click *Authorize* → *Logout*, then call `/auth/me` again → `401`. Typing a random fake token also gives `401`.

To test an **expired token**, set `ACCESS_TOKEN_EXPIRE_MINUTES=1` in `.env`, restart, log in, wait 61 seconds, and call `/auth/me`.

## About Logout
JWTs are **stateless**: the server does not keep a list of issued tokens, so it cannot "delete" one. Logout is normally done **on the client side** by deleting the token (from memory/localStorage). Until it expires, a copied token would still work.

If you need real server-side logout (token revocation), you must add state, for example:
- a `revoked_tokens` table (or Redis) storing each token's unique ID (`jti`) until it expires, and checking it in `get_current_user`; or
- short-lived access tokens + refresh tokens stored in the database, revoking the refresh token on logout.

This project keeps it simple and does not implement revocation.

## Security Notes
- Never commit `.env` (it is in `.gitignore`).
- All DB queries use SQLAlchemy ORM (parameterized → safe from SQL injection).
- Login returns the same error for wrong email and wrong password.
- For production, use HTTPS and consider rate limiting.
