"""Stockage temporaire en memoire pour visualiser les routes.

Ce module sera remplace par les repositories et la base de donnees plus tard.
"""

from datetime import datetime, timezone

from fastapi import HTTPException

from app.schemas.user import RoleName

users: dict[int, dict] = {}
offers: dict[int, dict] = {}
applications: dict[int, dict] = {}

users.update(
    {
        1: {
            "id": 1,
            "email": "student@stageflow.example.com",
            "full_name": "Etudiant Demo",
            "password": "password123",
            "role": RoleName.student,
            "is_active": True,
        },
        2: {
            "id": 2,
            "email": "company@stageflow.example.com",
            "full_name": "Entreprise Demo",
            "password": "password123",
            "role": RoleName.company,
            "is_active": True,
        },
        3: {
            "id": 3,
            "email": "manager@stageflow.example.com",
            "full_name": "Responsable Pedagogique Demo",
            "password": "password123",
            "role": RoleName.program_manager,
            "is_active": True,
        },
        4: {
            "id": 4,
            "email": "admin@stageflow.example.com",
            "full_name": "Administrateur Demo",
            "password": "password123",
            "role": RoleName.admin,
            "is_active": True,
        },
    }
)

_next_user_id = 5
_next_offer_id = 1
_next_application_id = 1


def get_user(user_id: int) -> dict:
    """Retourne un utilisateur ou leve une erreur si son compte est absent."""
    user = users.get(user_id)
    if user is None or not user["is_active"]:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable ou inactif.")
    return user


def require_role(user_id: int, *roles: RoleName) -> dict:
    """Verifie que l'utilisateur possede un des roles autorises."""
    user = get_user(user_id)
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="Ce role ne peut pas effectuer cette action.")
    return user


def utc_now() -> datetime:
    """Retourne la date UTC utilisee par les ressources de demonstration."""
    return datetime.now(timezone.utc)


def next_user_id() -> int:
    """Genere un identifiant temporaire pour un utilisateur."""
    global _next_user_id
    user_id = _next_user_id
    _next_user_id += 1
    return user_id


def next_offer_id() -> int:
    """Genere un identifiant temporaire pour une offre."""
    global _next_offer_id
    offer_id = _next_offer_id
    _next_offer_id += 1
    return offer_id


def next_application_id() -> int:
    """Genere un identifiant temporaire pour une candidature."""
    global _next_application_id
    application_id = _next_application_id
    _next_application_id += 1
    return application_id
