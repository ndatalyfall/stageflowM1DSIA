"""Endpoints de gestion des utilisateurs."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.permissions import require_roles
from app.core.security import get_current_user, hash_password
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import RoleName, UserCreate, UserRead, UserUpdateRole

router = APIRouter(prefix="/users", tags=["users"])
logger = logging.getLogger(__name__)


@router.get(
	"/me",
	response_model=UserRead,
	summary="Obtenir le profil de l'utilisateur authentifié",
	description="Retourne les informations du compte actuellement connecté.",
	responses={
		200: {"description": "Profil utilisateur retourné."},
		401: {"description": "Non authentifié ou jeton invalide."},
	},
)
def read_current_user(current_user: User = Depends(get_current_user)) -> User:
	"""Retourne l'utilisateur authentifie."""
	return current_user


@router.get(
	"",
	response_model=list[UserRead],
	summary="Lister tous les comptes (Admin uniquement)",
	description="Retourne la liste complète de tous les utilisateurs actifs. Réservé à l'administrateur.",
	responses={
		200: {"description": "Liste des utilisateurs retournée."},
		401: {"description": "Non authentifié."},
		403: {"description": "Accès refusé (Rôle Admin requis)."},
	},
)
def list_users(
	db: Session = Depends(get_db),
	_: dict = Depends(require_roles(RoleName.admin)),
) -> list[User]:
	"""Liste les comptes via UserRepository, réservé à l'administrateur."""
	user_repo = UserRepository(db)
	return list(user_repo.list_all())


@router.post(
	"/create_user",
	response_model=UserRead,
	status_code=status.HTTP_201_CREATED,
	summary="Créer un utilisateur avec rôle (Admin uniquement)",
	description="Permet à un administrateur authentifié de créer un nouvel utilisateur en choisissant son rôle (student, company, program_manager, admin).",
	responses={
		201: {"description": "Utilisateur créé avec succès."},
		401: {"description": "Non authentifié."},
		403: {"description": "Accès refusé (Rôle Admin requis)."},
		409: {"description": "Cette adresse email existe déjà."},
		422: {"description": "Erreur de validation du corps de la requête."},
	},
)
def create_user(
	payload: UserCreate,
	db: Session = Depends(get_db),
	_: dict = Depends(require_roles(RoleName.admin)),
) -> User:
	"""Crée un utilisateur avec le rôle choisi, réservé à l'administrateur."""
	user_repo = UserRepository(db)
	if user_repo.get_by_email(str(payload.email)) is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cette adresse email existe deja.")

	return user_repo.create(
		email=str(payload.email),
		full_name=payload.full_name,
		hashed_password=hash_password(payload.password),
		role=payload.role,
		is_active=True,
	)


@router.patch(
	"/update/{user_id}/role",
	response_model=UserRead,
	summary="Modifier le rôle d'un utilisateur (Admin uniquement)",
	description="Force l'attribution d'un nouveau rôle à un compte et consigne la modification dans les logs applicatifs.",
	responses={
		200: {"description": "Rôle modifié avec succès."},
		401: {"description": "Non authentifié."},
		403: {"description": "Accès refusé (Rôle Admin requis)."},
		404: {"description": "Utilisateur introuvable ou inactif."},
	},
)
def update_user_role(
	user_id: int,
	payload: UserUpdateRole,
	db: Session = Depends(get_db),
	_: dict = Depends(require_roles(RoleName.admin)),
) -> User:
	"""Force le role d'un compte via UserRepository et trace la modification."""
	user_repo = UserRepository(db)
	user = user_repo.get_by_id(user_id)
	if user is None or not user.is_active:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable ou inactif.")

	old_role = user.role
	updated_user = user_repo.update_role(user, payload.role)
	logger.info("Role utilisateur modifie: user_id=%s old_role=%s new_role=%s", user_id, old_role, payload.role)
	return updated_user


@router.delete(
	"/delete/{user_id}",
	status_code=status.HTTP_204_NO_CONTENT,
	summary="Désactiver un compte utilisateur (Admin uniquement)",
	description="Désactive un compte utilisateur (soft delete). Action réservée à l'administrateur.",
	responses={
		204: {"description": "Compte utilisateur désactivé avec succès."},
		401: {"description": "Non authentifié."},
		403: {"description": "Accès refusé (Rôle Admin requis)."},
		404: {"description": "Utilisateur introuvable ou inactif."},
	},
)
def delete_user(
	user_id: int,
	db: Session = Depends(get_db),
	_: dict = Depends(require_roles(RoleName.admin)),
) -> None:
	"""Desactive un compte utilisateur via UserRepository."""
	user_repo = UserRepository(db)
	user = user_repo.get_by_id(user_id)
	if user is None or not user.is_active:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable ou inactif.")

	user_repo.deactivate(user)
	logger.info("Utilisateur desactive: user_id=%s", user_id)
