from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from app.database.db import Base, engine, get_db
from app.database import models
from app.schema.user import UserCreate
from app.crud.user import create_user, get_user_by_email
from app.utils.hashing import hash_password, needs_password_rehash, verify_password
from app.schema.user import UserLogin
from app.schema.solar import SolarPlanRequest
from app.utils.solar_plan_pdf import create_solar_plan_pdf

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Liora API",
    version="1.0.0"
)

# Allows the project HTML pages to call the API while developing locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000", "null"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@app.get("/api")
def home():
    return {
        "message": "Welcome to Liora API 🌿"
    }


@app.get("/", include_in_schema=False)
def frontend():
    """Serve the Liora frontend from the same origin as the API."""
    return FileResponse(PROJECT_ROOT / "liora.html")


@app.get("/style.css", include_in_schema=False)
def stylesheet():
    return FileResponse(PROJECT_ROOT / "style.css", media_type="text/css")


@app.get("/script.js", include_in_schema=False)
def home_script():
    return FileResponse(PROJECT_ROOT / "script.js", media_type="text/javascript")


@app.get("/calculator", include_in_schema=False)

def calculator_page():
    return FileResponse(PROJECT_ROOT / "calculator.html")


@app.get("/calculator.css", include_in_schema=False)
def calculator_stylesheet():
    return FileResponse(PROJECT_ROOT / "calculator.css", media_type="text/css")


@app.get("/calculator.js", include_in_schema=False)
def calculator_script():
    return FileResponse(PROJECT_ROOT / "calculator.js", media_type="text/javascript")


@app.get("/solar-recommendation", include_in_schema=False)
def solar_recommendation_page():
    return FileResponse(PROJECT_ROOT / "solar-recommendation.html")


@app.get("/solar-recommendation.js", include_in_schema=False)
def solar_recommendation_script():
    return FileResponse(PROJECT_ROOT / "solar-recommendation.js", media_type="text/javascript")


@app.get("/login-page", include_in_schema=False)
def login_page():
    """Serve the login screen from the API origin."""
    return FileResponse(PROJECT_ROOT / "login (1).html")


@app.get("/login.js", include_in_schema=False)
def login_script():
    return FileResponse(PROJECT_ROOT / "login.js", media_type="text/javascript")

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

    return {"message": "Login Successful"}


@app.post("/solar-plan.pdf", include_in_schema=False)
def download_solar_plan(plan: SolarPlanRequest):
    pdf = create_solar_plan_pdf(plan)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=liora-solar-plan.pdf"},
    )
