"""Modele SQLAlchemy des comptes utilisateurs."""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.user import RoleName


class User(Base):
	"""Compte avec un role et un mot de passe uniquement stocke sous forme de hash."""

	__tablename__ = "users"

	id: Mapped[int] = mapped_column(primary_key=True)
	email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
	full_name: Mapped[str] = mapped_column(String(150), nullable=False)
	hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
	role: Mapped[RoleName] = mapped_column(Enum(RoleName, native_enum=False), nullable=False)
	is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	offers = relationship("Offer", back_populates="company")
	applications = relationship("Application", back_populates="student")
