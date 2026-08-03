"""Endpoints d'authentification et de gestion de compte."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import RoleName, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
	"/register",
	response_model=UserRead,
	status_code=status.HTTP_201_CREATED,
	summary="Inscrire un nouvel étudiant",
	description="Crée un compte étudiant dans la base de données. L'adresse email doit être unique.",
	responses={
		201: {"description": "Compte utilisateur créé avec succès."},
		409: {"description": "L'adresse email est déjà utilisée."},
		422: {"description": "Erreur de validation du corps de la requête."},
	},
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:
	"""Crée un compte étudiant dans la base de données via le UserRepository."""
	user_repo = UserRepository(db)
	if user_repo.get_by_email(str(payload.email)) is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette adresse email existe deja.")

	return user_repo.create(
		email=str(payload.email),
		full_name=payload.full_name,
		hashed_password=hash_password(payload.password),
		role=RoleName.student,
		is_active=True,
	)


@router.post(
	"/login",
	response_model=TokenResponse,
	summary="Se connecter et obtenir un token JWT",
	description="Vérifie les identifiants de l'utilisateur et retourne un token d'accès JWT valide.",
	responses={
		200: {"description": "Authentification réussie, jeton JWT fourni."},
		401: {"description": "Identifiants invalides ou compte inactif."},
	},
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
	"""Vérifie les identifiants via UserRepository et retourne un jeton JWT."""
	user_repo = UserRepository(db)
	user = user_repo.get_by_email(str(payload.email))
	if user is None or not verify_password(payload.password, user.hashed_password):
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides.")
	if not user.is_active:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Compte inactif.")

	access_token = create_access_token(subject=str(user.id), role=user.role.value)
	return TokenResponse(access_token=access_token)
