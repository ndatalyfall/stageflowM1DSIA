"""Acces aux donnees utilisateur."""

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import RoleName


class UserRepository:
	"""Repository CRUD pour les comptes utilisateurs."""

	def __init__(self, db: Session) -> None:
		self.db = db

	def get_by_id(self, user_id: int) -> User | None:
		"""Retourne un utilisateur par identifiant."""
		return self.db.get(User, user_id)

	def get_by_email(self, email: str) -> User | None:
		"""Retourne un utilisateur par adresse email."""
		return self.db.query(User).filter(User.email == email).first()

	def list_all(self) -> Iterable[User]:
		"""Retourne tous les utilisateurs."""
		return self.db.query(User).filter(User.is_active == True).order_by(User.id).all()

	def create(self, *, email: str, full_name: str, hashed_password: str, role: RoleName, is_active: bool = True) -> User:
		"""Cree un utilisateur."""
		user = User(
			email=email,
			full_name=full_name,
			hashed_password=hashed_password,
			role=role,
			is_active=is_active,
		)
		self.db.add(user)
		self.db.commit()
		self.db.refresh(user)
		return user

	def update_role(self, user: User, role: RoleName) -> User:
		"""Met a jour le role d'un utilisateur."""
		user.role = role
		self.db.add(user)
		self.db.commit()
		self.db.refresh(user)
		return user

	def deactivate(self, user: User) -> User:
		"""Desactive un utilisateur sans supprimer sa ligne."""
		user.is_active = False
		self.db.add(user)
		self.db.commit()
		self.db.refresh(user)
		return user
