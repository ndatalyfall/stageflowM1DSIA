"""Script d'initialisation de la base de données et de création de l'administrateur par défaut."""

import logging
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.user import RoleName

logger = logging.getLogger(__name__)

DEFAULT_ADMIN_EMAIL = "ndataly@live.fr"
DEFAULT_ADMIN_NAME = "ndataly"
DEFAULT_ADMIN_PASSWORD = "thiercoum"


def init_db(db: Session) -> None:
	"""Crée l'utilisateur administrateur par défaut s'il n'existe pas déjà."""
	user_repo = UserRepository(db)
	existing_admin = user_repo.get_by_email(DEFAULT_ADMIN_EMAIL)
	if existing_admin is None:
		user_repo.create(
			email=DEFAULT_ADMIN_EMAIL,
			full_name=DEFAULT_ADMIN_NAME,
			hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),
			role=RoleName.admin,
			is_active=True,
		)
		logger.info("Admin par défaut créé avec succès : %s", DEFAULT_ADMIN_EMAIL)
	else:
		logger.info("L'admin par défaut existe déjà : %s", DEFAULT_ADMIN_EMAIL)


def main() -> None:
	db = SessionLocal()
	try:
		init_db(db)
	finally:
		db.close()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	main()
