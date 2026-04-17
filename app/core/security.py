from datetime import datetime, timedelta
import secrets
from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt

SECRET_KEY = "change-moi-en-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

REFRESH_TOKEN_EXPIRE_DAYS = 30  # Durée de vie du refresh token

def create_refresh_token() -> tuple[str, datetime]:
    # Génère une chaîne aléatoire de 32 octets, encodée en base64 URL-safe
    # Exemple : "aB3xK9mP2nQr7sT4uV6wX8yZ1cD5eF0g"
    token = secrets.token_urlsafe(32)

    # Calcule la date d'expiration (maintenant + 30 jours)
    # C'est cette date qu'on stockera dans expires_at en base
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    # Retourne les deux — on a besoin des deux pour créer la ligne en base
    return token, expires_at