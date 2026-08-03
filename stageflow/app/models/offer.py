"""Modele SQLAlchemy des offres et de leur workflow."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.offer import OfferStatus


class Offer(Base):
	"""Offre associee a l'entreprise qui l'a creee."""

	__tablename__ = "offers"

	id: Mapped[int] = mapped_column(primary_key=True)
	company_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	title: Mapped[str] = mapped_column(String(200), nullable=False)
	mission: Mapped[str] = mapped_column(Text, nullable=False)
	skills: Mapped[list[str]] = mapped_column(JSON, nullable=False)
	status: Mapped[OfferStatus] = mapped_column(Enum(OfferStatus, native_enum=False), default=OfferStatus.draft, nullable=False, index=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

	company = relationship("User", back_populates="offers")
	applications = relationship("Application", back_populates="offer", cascade="all, delete-orphan")
