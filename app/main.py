from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import secrets
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request as URLRequest, urlopen

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database.db import Base, engine, get_db
from app.database.models import PasswordResetToken, User
from app.schema.user import OAuthIdentity, PasswordReset, PasswordResetRequest, UserCreate
from app.crud.user import create_user, get_user_by_email
from app.utils.hashing import hash_password, needs_password_rehash, verify_password
from app.schema.user import UserLogin
from app.schema.solar import SolarPlanRequest
from app.schema.chat import ChatRequest
from app.schema.contact import ContactRequest
from app.utils.solar_plan_pdf import create_solar_plan_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Liora API",
    version="1.0.0"
)


def get_allowed_origins() -> list[str]:
    """Support both local development and public deployment origins."""
    configured = os.getenv("ALLOWED_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]

    for env_name in ("PUBLIC_URL", "FRONTEND_URL", "API_URL"):
        value = os.getenv(env_name)
        if value:
            origins.append(value.rstrip("/"))

    defaults = [
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "null",
    ]
    origins.extend(defaults)

    return list(dict.fromkeys(origins))


# Allows the app to accept requests from the public site as well as local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
FRONTEND_PAGES = FRONTEND_ROOT / "pages"
FRONTEND_CSS = FRONTEND_ROOT / "css"
FRONTEND_JS = FRONTEND_ROOT / "js"
RESET_TOKEN_LIFETIME = timedelta(minutes=30)
OAUTH_PROVIDERS = {
    "google": {
        "client_id_env": "GOOGLE_CLIENT_ID",
        "jwks_url": "https://www.googleapis.com/oauth2/v3/certs",
        "issuers": {"https://accounts.google.com", "accounts.google.com"},
    },
    "apple": {
        "client_id_env": "APPLE_CLIENT_ID",
        "jwks_url": "https://appleid.apple.com/auth/keys",
        "issuers": {"https://appleid.apple.com"},
    },
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _send_reset_email(email: str, reset_url: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is not configured. Set RESEND_API_KEY on the server.",
        )

    payload = json.dumps({
        "from": os.getenv("CONTACT_FROM_EMAIL", "Liora <onboarding@resend.dev>"),
        "to": [email],
        "subject": "Reset your Liora password",
        "text": (
            "We received a request to reset your Liora password. "
            f"Use this one-time link within 30 minutes: {reset_url}\n\n"
            "If you did not request a reset, you can ignore this email."
        ),
    }).encode("utf-8")
    provider_request = URLRequest(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(provider_request, timeout=15):
            pass
    except (HTTPError, URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Password reset email could not be sent. Please try again later.",
        ) from error


def _verify_oauth_identity(provider: str, identity_token: str, nonce: str) -> dict:
    config = OAUTH_PROVIDERS[provider]
    client_id = os.getenv(config["client_id_env"])
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider.title()} sign-in is not configured.",
        )

    try:
        with urlopen(config["jwks_url"], timeout=10) as response:
            jwks = json.loads(response.read().decode("utf-8"))["keys"]
        header = jwt.get_unverified_header(identity_token)
        signing_key = next(key for key in jwks if key.get("kid") == header.get("kid"))
        claims = jwt.decode(
            identity_token,
            signing_key,
            algorithms=["RS256"],
            audience=client_id,
            options={"verify_iss": False},
        )
    except (HTTPError, URLError, TimeoutError, KeyError, StopIteration, ValueError, JWTError) as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The identity provider returned an invalid sign-in token.",
        ) from error

    if claims.get("iss") not in config["issuers"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The identity provider returned an invalid sign-in token.",
        )
    expected_nonce = hashlib.sha256(nonce.encode("utf-8")).hexdigest()
    if claims.get("nonce") not in {nonce, expected_nonce}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The identity provider returned an invalid sign-in token.",
        )
    if claims.get("email_verified") not in {True, "true"}:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A verified email address is required to sign in.",
        )
    return claims


@app.get("/api")
def home():
    return {
        "message": "Welcome to Liora API 🌿"
    }


@app.get("/", include_in_schema=False)
def frontend():
    """Serve the Liora frontend from the same origin as the API."""
    return FileResponse(FRONTEND_PAGES / "liora.html")


@app.get("/style.css", include_in_schema=False)
def stylesheet():
    return FileResponse(FRONTEND_CSS / "style.css", media_type="text/css")


@app.get("/script.js", include_in_schema=False)
def home_script():
    return FileResponse(FRONTEND_JS / "script.js", media_type="text/javascript")


@app.get("/talk-to-liora", include_in_schema=False)
def talk_to_liora_page():
    return FileResponse(FRONTEND_PAGES / "talk-to-liora.html")


@app.get("/chatbot", include_in_schema=False)
def chatbot_page():
    return FileResponse(FRONTEND_PAGES / "talk-to-liora.html")


@app.get("/calculator", include_in_schema=False)
def calculator_page():
    return FileResponse(FRONTEND_PAGES / "calculator.html")


@app.get("/calculator.css", include_in_schema=False)
def calculator_stylesheet():
    return FileResponse(FRONTEND_CSS / "calculator.css", media_type="text/css")


@app.get("/calculator.js", include_in_schema=False)
def calculator_script():
    return FileResponse(FRONTEND_JS / "calculator.js", media_type="text/javascript")


@app.get("/solar-recommendation", include_in_schema=False)
def solar_recommendation_page():
    return FileResponse(FRONTEND_PAGES / "solar-recommendation.html")


@app.get("/solar-recommendation.js", include_in_schema=False)
def solar_recommendation_script():
    return FileResponse(FRONTEND_JS / "solar-recommendation.js", media_type="text/javascript")


@app.get("/login-page", include_in_schema=False)
def login_page():
    """Serve the login screen from the API origin."""
    return FileResponse(FRONTEND_PAGES / "login.html")


@app.get("/login.js", include_in_schema=False)
def login_script():
    return FileResponse(FRONTEND_JS / "login.js", media_type="text/javascript")


@app.get("/chat.js", include_in_schema=False)
def chat_script():
    return FileResponse(FRONTEND_JS / "chat.js", media_type="text/javascript")


@app.post("/chat")
def chat(request: ChatRequest):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI chat is not configured. Set OPENAI_API_KEY on the server.",
        )

    system_prompt = (
        "You are Liora, a helpful solar energy assistant. Answer clearly and briefly. "
        "Help users understand solar sizing, generation, savings, costs, batteries, "
        "and installation considerations. Use the user's provided plan context when "
        "available. Do not guarantee exact savings, prices, approvals, or payback; "
        "explain that local installers should confirm estimates. If asked about an "
        "unrelated topic, politely steer the conversation back to solar."
    )
    messages = [{"role": "system", "content": system_prompt}]
    if request.context:
        context = "; ".join(f"{key}: {value}" for key, value in request.context.items())
        messages.append({"role": "system", "content": f"Current user context: {context}"})
    messages.extend(message.model_dump() for message in request.history[-20:])
    messages.append({"role": "user", "content": request.message})

    payload = json.dumps({
        "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 500,
    }).encode("utf-8")
    provider_request = URLRequest(
        os.getenv("OPENAI_API_URL", "https://api.openai.com/v1/chat/completions"),
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urlopen(provider_request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        answer = result["choices"][0]["message"]["content"].strip()
    except (HTTPError, URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError) as error:
        detail = "The AI assistant is temporarily unavailable. Please try again."
        if isinstance(error, HTTPError) and error.code in {401, 403}:
            detail = "The AI provider rejected the server credentials. Check OPENAI_API_KEY."
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=detail) from error

    return {"answer": answer}


@app.post("/contact")
def contact(request: ContactRequest):
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Contact email is not configured yet. Set RESEND_API_KEY on the server.",
        )

    payload = json.dumps({
        "from": os.getenv("CONTACT_FROM_EMAIL", "Liora website <onboarding@resend.dev>"),
        "to": ["ompurnima2930@gmail.com"],
        "reply_to": request.email,
        "subject": f"Liora contact message from {request.name}",
        "text": f"Name: {request.name}\nEmail: {request.email}\n\n{request.message}",
    }).encode("utf-8")
    provider_request = URLRequest(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urlopen(provider_request, timeout=15):
            pass
    except (HTTPError, URLError, TimeoutError) as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The message could not be sent. Please try again later.",
        ) from error

    return {"message": "Your message was sent successfully."}

@app.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):

    existing_user = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered.",
        )

    new_user = create_user(
        db=db,
        name=user.name,
        email=user.email,
        password=user.password
    )

    return {
        "message": "User registered successfully!",
        "id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

@app.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):

    db_user = get_user_by_email(db, user.email)

    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    result = verify_password(user.password, db_user.password)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    # Migrate passwords created before hashing was enabled after a successful
    # verification, so existing accounts keep working without retaining plaintext.
    if needs_password_rehash(db_user.password):
        db_user.password = hash_password(user.password)
        db.commit()

    return {
        "message": "Login Successful",
        "name": db_user.name,
        "email": db_user.email,
    }


@app.get("/auth/config")
def auth_config():
    return {
        "google_client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "apple_client_id": os.getenv("APPLE_CLIENT_ID"),
    }


@app.post("/auth/{provider}")
def oauth_login(provider: str, identity: OAuthIdentity, db: Session = Depends(get_db)):
    if provider not in OAUTH_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unsupported sign-in provider.",
        )

    claims = _verify_oauth_identity(provider, identity.identity_token, identity.nonce)
    email = claims.get("email")
    if not isinstance(email, str) or not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="The identity provider did not supply an email address.",
        )

    db_user = get_user_by_email(db, email)
    if db_user is None:
        name = claims.get("name") if provider == "google" else None
        db_user = create_user(
            db=db,
            name=name or email.split("@", 1)[0],
            email=email,
            password=secrets.token_urlsafe(48),
        )

    return {
        "message": "Login Successful",
        "name": db_user.name,
        "email": db_user.email,
    }


@app.post("/forgot-password")
def forgot_password(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
):
    if not os.getenv("RESEND_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset email is not configured. Set RESEND_API_KEY on the server.",
        )
    public_url = os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL")
    if not public_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Password reset links are not configured. Set PUBLIC_URL on the server.",
        )

    user = get_user_by_email(db, str(payload.email))
    if user is None:
        return {"message": "If that email is registered, a reset link has been sent."}

    now = _utc_now()
    existing_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).first()
    if (
        existing_token is not None
        and existing_token.expires_at > now
        and existing_token.created_at > now - timedelta(minutes=1)
    ):
        return {"message": "If that email is registered, a reset link has been sent."}

    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).delete(synchronize_session=False)
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=now + RESET_TOKEN_LIFETIME,
    ))
    db.commit()

    public_url = public_url.rstrip("/")
    reset_url = f"{public_url}/login-page#reset_token={raw_token}"
    try:
        _send_reset_email(str(payload.email), reset_url)
    except HTTPException:
        db.query(PasswordResetToken).filter(
            PasswordResetToken.token_hash == token_hash
        ).delete(synchronize_session=False)
        db.commit()
        raise

    return {"message": "If that email is registered, a reset link has been sent."}


@app.post("/reset-password")
def reset_password(payload: PasswordReset, db: Session = Depends(get_db)):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    reset_token = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash
    ).first()
    if reset_token is None or reset_token.expires_at <= _utc_now():
        if reset_token is not None:
            db.delete(reset_token)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or expired. Request a new one.",
        )

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    if user is None:
        db.delete(reset_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password reset link is invalid or expired. Request a new one.",
        )

    user.password = hash_password(payload.password)
    db.delete(reset_token)
    db.commit()
    return {"message": "Password updated. You can now sign in."}


@app.post("/solar-plan.pdf", include_in_schema=False)
def download_solar_plan(plan: SolarPlanRequest):
    pdf = create_solar_plan_pdf(plan)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=liora-solar-plan.pdf"},
    )
