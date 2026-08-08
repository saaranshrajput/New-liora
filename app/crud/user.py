from sqlalchemy.orm import Session
from app.database.models import User
from app.utils.hashing import hash_password


def create_user(db: Session, name: str, email: str, password: str):
    new_user = User(
        name=name,
        email=email,
        password=hash_password(password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

def get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()
