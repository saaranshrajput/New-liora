import hmac

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def _truncate_password(value):
    """Bcrypt only accepts up to 72 bytes; truncate safely before hashing."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        value = value[:72]
        return value.decode("utf-8", errors="ignore")
    encoded = value.encode("utf-8")
    if len(encoded) > 72:
        return encoded[:72].decode("utf-8", errors="ignore")
    return value


def hash_password(password: str):
    normalized = _truncate_password(password)
    return pwd_context.hash(normalized)


def verify_password(plain_password, hashed_password):
    """Verify a password without exposing malformed legacy values as 500s."""
    if not pwd_context.identify(hashed_password):
        # Accounts created before password hashing was added stored plaintext
        # passwords. This permits a successful login to migrate them below.
        return hmac.compare_digest(plain_password, hashed_password)

    normalized_password = _truncate_password(plain_password)

    try:
        return pwd_context.verify(normalized_password, hashed_password)
    except ValueError:
        return False


def needs_password_rehash(stored_password: str) -> bool:
    """Return whether a stored password should be replaced with a bcrypt hash."""
    return not pwd_context.identify(stored_password) or pwd_context.needs_update(stored_password)
