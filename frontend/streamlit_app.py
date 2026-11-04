"""
frontend/streamlit_app.py
-------------------------
A professional Streamlit UI for the FastAPI authentication backend.
It talks to the backend ONLY through HTTP (requests) - exactly like any
real frontend would. All security logic stays in the FastAPI backend.

Run (backend must already be running):
    streamlit run frontend/streamlit_app.py
"""

import base64
import json
import os
import re
from datetime import datetime, timezone

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(
    page_title="SecureAuth",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Styling (custom CSS for a modern look)
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    #MainMenu, footer {visibility: hidden;}
    header {background: transparent !important;}  /* keep header: it holds the sidebar button */
    .block-container {padding-top: 2rem; max-width: 820px;}

    .hero {
        text-align: center; padding: 2.2rem 1rem 1.6rem 1rem; margin-bottom: 1.2rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #6C63FF 0%, #3B82F6 55%, #06B6D4 100%);
        box-shadow: 0 10px 40px rgba(108, 99, 255, 0.35);
    }
    .hero h1 {color: white; font-size: 2.4rem; margin: 0; letter-spacing: 0.5px;}
    .hero p  {color: rgba(255,255,255,0.88); margin: 0.4rem 0 0 0; font-size: 1.02rem;}

    .badges {text-align:center; margin-bottom: 1.4rem;}
    .badge {
        display:inline-block; padding: 4px 12px; margin: 3px; font-size: 0.78rem;
        border-radius: 999px; background: #1E2433; color: #B8C0FF;
        border: 1px solid #2E3650;
    }

    div[data-testid="stMetric"] {
        background: #161B26; border: 1px solid #2A3247; padding: 16px 18px;
        border-radius: 14px; box-shadow: 0 4px 14px rgba(0,0,0,0.25);
    }
    div[data-testid="stMetricLabel"] p {color: #9AA4C0; font-size: 0.85rem;}

    .stTabs [data-baseweb="tab-list"] {gap: 6px;}
    .stTabs [data-baseweb="tab"] {
        background: #161B26; border-radius: 10px 10px 0 0; padding: 10px 22px;
    }
    .stButton > button, .stFormSubmitButton > button {
        border-radius: 10px; font-weight: 600; height: 2.9rem;
        background: linear-gradient(90deg, #6C63FF, #3B82F6); color: white; border: none;
    }
    .stButton > button:hover, .stFormSubmitButton > button:hover {
        filter: brightness(1.12); color: white;
    }
    .rule-ok  {color: #34D399; font-size: 0.88rem; margin: 0;}
    .rule-bad {color: #F87171; font-size: 0.88rem; margin: 0;}
    .avatar {
        width: 76px; height: 76px; border-radius: 50%; display:flex; align-items:center;
        justify-content:center; font-size: 2rem; font-weight: 700; color: white;
        background: linear-gradient(135deg, #6C63FF, #06B6D4); margin-bottom: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def api_call(method: str, path: str, **kwargs):
    """Call the backend. Returns (response, error_message)."""
    try:
        resp = requests.request(method, f"{API_URL}{path}", timeout=10, **kwargs)
        return resp, None
    except requests.exceptions.ConnectionError:
        return None, "Cannot reach the backend. Start it with: uvicorn app.main:app --reload"
    except requests.exceptions.Timeout:
        return None, "The backend took too long to respond."


def extract_error(resp) -> str:
    """Turn FastAPI error JSON into a friendly message."""
    try:
        detail = resp.json().get("detail", "Something went wrong.")
    except ValueError:
        return "Something went wrong."
    if isinstance(detail, list):  # 422 validation errors
        msgs = []
        for item in detail:
            field = item.get("loc", ["", ""])[-1]
            msg = item.get("msg", "").replace("Value error, ", "")
            msgs.append(f"**{field}**: {msg}")
        return "\n\n".join(msgs)
    return str(detail)


def decode_jwt_unverified(token: str):
    """Decode header + payload for DISPLAY only (signature is verified by the backend)."""
    def b64(part: str):
        part += "=" * (-len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part))

    header_b64, payload_b64, _sig = token.split(".")
    return b64(header_b64), b64(payload_b64)


def password_rules(pw: str) -> dict:
    return {
        "At least 8 characters": len(pw) >= 8,
        "One uppercase letter (A-Z)": bool(re.search(r"[A-Z]", pw)),
        "One lowercase letter (a-z)": bool(re.search(r"[a-z]", pw)),
        "One number (0-9)": bool(re.search(r"\d", pw)),
        "One special character (!@#$...)": bool(re.search(r"[^A-Za-z0-9]", pw)),
    }


def logout(message: str | None = None):
    st.session_state.pop("token", None)
    st.session_state.flash = message


# ---------------------------------------------------------------------------
# Sidebar: backend status + info
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ System Status")
    health, err = api_call("GET", "/")
    if health is not None and health.status_code == 200:
        st.success("FastAPI backend: Online")
    else:
        st.error("FastAPI backend: Offline")
    st.caption(f"API: `{API_URL}`")
    st.markdown("---")
    st.markdown("### 🛡️ Security Features")
    st.markdown(
        "- Argon2id password hashing\n"
        "- Signed JWT tokens (HS256)\n"
        "- Token expiration\n"
        "- Input validation (Pydantic)\n"
        "- Safe SQL via SQLAlchemy ORM\n"
        "- No password ever returned by API"
    )
    st.markdown("---")
    st.markdown("[📘 API Docs (Swagger)](" + API_URL + "/docs)")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🔐 SecureAuth</h1>
        <p>Enterprise-grade user authentication, built with FastAPI &amp; PostgreSQL</p>
    </div>
    <div class="badges">
        <span class="badge">FastAPI</span><span class="badge">PostgreSQL</span>
        <span class="badge">SQLAlchemy</span><span class="badge">Argon2</span>
        <span class="badge">JWT</span><span class="badge">Streamlit</span>
    </div>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("flash"):
    st.warning(st.session_state.pop("flash"))

# ---------------------------------------------------------------------------
# VIEW 1: Logged OUT -> Login / Signup tabs
# ---------------------------------------------------------------------------
if "token" not in st.session_state:
    tab_login, tab_signup = st.tabs(["🔑  Login", "📝  Create Account"])

    # ---------------- Login ----------------
    with tab_login:
        st.markdown("#### Welcome back")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", use_container_width=True)

        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                with st.spinner("Verifying credentials..."):
                    resp, err = api_call("POST", "/auth/login", json={"email": email, "password": password})
                if err:
                    st.error(err)
                elif resp.status_code == 200:
                    st.session_state.token = resp.json()["access_token"]
                    st.rerun()
                else:
                    st.error(extract_error(resp))

    # ---------------- Signup ----------------
    with tab_signup:
        st.markdown("#### Create your account")
        full_name = st.text_input("Full name", placeholder="Ali Khan", key="su_name")
        su_email = st.text_input("Email", placeholder="you@example.com", key="su_email")
        su_pw = st.text_input("Password", type="password", key="su_pw")
        su_pw2 = st.text_input("Confirm password", type="password", key="su_pw2")

        # Live password strength checklist
        rules = password_rules(su_pw)
        passed = sum(rules.values())
        if su_pw:
            st.progress(passed / len(rules), text=f"Password strength: {passed}/{len(rules)}")
            for label, ok in rules.items():
                css = "rule-ok" if ok else "rule-bad"
                icon = "✅" if ok else "❌"
                st.markdown(f"<p class='{css}'>{icon} {label}</p>", unsafe_allow_html=True)
        if su_pw2 and su_pw != su_pw2:
            st.markdown("<p class='rule-bad'>❌ Passwords do not match</p>", unsafe_allow_html=True)

        ready = bool(full_name and su_email and su_pw and su_pw2) and passed == len(rules)
        if st.button("Create account", use_container_width=True, disabled=not ready, key="su_btn"):
            with st.spinner("Creating your account..."):
                resp, err = api_call(
                    "POST",
                    "/auth/signup",
                    json={
                        "full_name": full_name,
                        "email": su_email,
                        "password": su_pw,
                        "confirm_password": su_pw2,
                    },
                )
            if err:
                st.error(err)
            elif resp.status_code == 201:
                st.success("🎉 Account created successfully! Open the **Login** tab to sign in.")
                st.balloons()
            else:
                st.error(extract_error(resp))

# ---------------------------------------------------------------------------
# VIEW 2: Logged IN -> Dashboard
# ---------------------------------------------------------------------------
else:
    token = st.session_state.token
    resp, err = api_call("GET", "/auth/me", headers={"Authorization": f"Bearer {token}"})

    if err:
        st.error(err)
        st.stop()
    if resp.status_code != 200:
        # Token expired / invalid -> back to login
        logout("Your session has expired or is invalid. Please log in again.")
        st.rerun()

    user = resp.json()
    header, payload = decode_jwt_unverified(token)
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    minutes_left = max(0, int((exp - datetime.now(timezone.utc)).total_seconds() // 60))

    left, right = st.columns([4, 1])
    with left:
        st.markdown(f"<div class='avatar'>{user['full_name'][0].upper()}</div>", unsafe_allow_html=True)
        st.markdown(f"### Welcome, {user['full_name']} 👋")
        st.caption("You are securely authenticated.")
    with right:
        st.write("")
        st.write("")
        if st.button("Logout", use_container_width=True):
            logout()
            st.rerun()

    c1, c2, c3 = st.columns(3)
    c1.metric("User ID", f"#{user['id']}")
    c2.metric("Status", "Authenticated ✅")
    c3.metric("Token expires in", f"{minutes_left} min")

    st.write("")
    tab_profile, tab_token, tab_how = st.tabs(["👤  Profile", "🔎  Token Inspector", "📚  How it works"])

    with tab_profile:
        st.markdown("#### Profile (from `GET /auth/me`)")
        st.json(user)
        st.caption("Data was fetched from the protected endpoint using your JWT. "
                   "The password hash is never returned by the API.")

    with tab_token:
        st.markdown("#### Your JWT access token")
        st.code(token, language="text")
        a, b = st.columns(2)
        with a:
            st.markdown("**Header**")
            st.json(header)
        with b:
            st.markdown("**Payload**")
            st.json({
                **payload,
                "iat (readable)": datetime.fromtimestamp(payload["iat"], tz=timezone.utc).isoformat(),
                "exp (readable)": exp.isoformat(),
            })
        st.info("A JWT has 3 parts: header . payload . signature. The payload is only "
                "Base64-encoded (anyone can read it), so never put secrets inside. "
                "The signature is verified by the backend using the secret key, "
                "so nobody can modify the token.")

    with tab_how:
        st.markdown(
            """
            #### Authentication flow
            1. **Signup** → password is hashed with **Argon2** and stored in PostgreSQL.
            2. **Login** → backend verifies the password against the hash and issues a **signed JWT**.
            3. **Protected requests** → this app sends `Authorization: Bearer <token>`.
            4. **Backend** verifies the signature and expiry, then returns your profile.
            5. **Logout** → the token is deleted on the client side (JWTs are stateless).
            """
        )
        st.warning("Note: a stateless JWT stays technically valid until it expires. "
                   "True server-side revocation needs a token blacklist in the database.")