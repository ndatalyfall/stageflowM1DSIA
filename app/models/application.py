"""Modele SQLAlchemy des candidatures."""

from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.schemas.application import ApplicationStatus


class Application(Base):
	"""Candidature d'un etudiant pour une offre."""

	__tablename__ = "applications"

	id: Mapped[int] = mapped_column(primary_key=True)
	student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
	offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id"), nullable=False, index=True)
	cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
	status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus, native_enum=False), default=ApplicationStatus.pending, nullable=False, index=True)
	created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
	updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

	student = relationship("User", back_populates="applications")
	offer = relationship("Offer", back_populates="applications")
