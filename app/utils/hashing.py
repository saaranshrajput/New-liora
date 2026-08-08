import hmac

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    """Verify a password without exposing malformed legacy values as 500s."""
    if not pwd_context.identify(hashed_password):
        # Accounts created before password hashing was added stored plaintext
        # passwords. This permits a successful login to migrate them below.
        return hmac.compare_digest(plain_password, hashed_password)

    if isinstance(plain_password, str):
        plain_password = plain_password.encode("utf-8")
    if len(plain_password) > 72:
        plain_password = plain_password[:72]

    try:
        return pwd_context.verify(
            plain_password.decode("utf-8", errors="ignore"),
            hashed_password,
        )
    except ValueError:
        return False


def needs_password_rehash(stored_password: str) -> bool:
    """Return whether a stored password should be replaced with a bcrypt hash."""
    return not pwd_context.identify(stored_password) or pwd_context.needs_update(stored_password)
