"""Hachage des mots de passe et gestion des JWT."""

from datetime import datetime, timedelta, timezone
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
	"""Transforme un mot de passe en hash non reversible."""
	return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
	"""Compare un mot de passe en clair avec son hash."""
	return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
	"""Cree un JWT signe avec une date d'expiration."""
	expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
	payload = {"sub": subject, "role": role, "exp": expires_at}
	return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
	"""Decode un JWT ou leve une erreur d'authentification."""
	try:
		return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
	except jwt.PyJWTError as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expire.") from exc


def get_token_payload(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)) -> dict:
	"""Extrait et valide le bearer token fourni par le client."""
	if credentials is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise.")
	return decode_access_token(credentials.credentials)


def get_current_user(
	db: Session = Depends(get_db),
	payload: dict = Depends(get_token_payload),
) -> User:
	"""Retourne l'utilisateur authentifie decode depuis le JWT."""
	try:
		user_id = int(payload["sub"])
	except (KeyError, TypeError, ValueError) as exc:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide.") from exc

	user = db.get(User, user_id)
	if user is None or not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable ou inactif.")
	return user
