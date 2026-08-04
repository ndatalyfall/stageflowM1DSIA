"""Acces aux donnees des offres."""

from collections.abc import Iterable
from typing import Any

from sqlalchemy.orm import Session

from app.models.offer import Offer
from app.schemas.offer import OfferStatus


class OfferRepository:
	"""Repository CRUD pour les offres de stage."""

	def __init__(self, db: Session) -> None:
		self.db = db

	def get_by_id(self, offer_id: int) -> Offer | None:
		"""Retourne une offre par identifiant."""
		return self.db.get(Offer, offer_id)

	def list_all(self, *, published_only: bool = False) -> Iterable[Offer]:
		"""Retourne toutes les offres ou seulement les publiees."""
		query = self.db.query(Offer)
		if published_only:
			query = query.filter(Offer.status == OfferStatus.published)
		return query.order_by(Offer.created_at.desc()).all()

	def list_for_company(self, company_id: int) -> Iterable[Offer]:
		"""Retourne les offres d'une entreprise."""
		return self.db.query(Offer).filter(Offer.company_id == company_id).order_by(Offer.created_at.desc()).all()

	def count_by_status(self) -> dict[str, int]:
		"""Retourne le nombre d'offres groupe par statut."""
		offer_counts = {s.value: 0 for s in OfferStatus}
		for offer in self.db.query(Offer).all():
			offer_counts[offer.status.value] += 1
		return offer_counts

	def create(
		self,
		*,
		company_id: int,
		title: str,
		mission: str,
		skills: list[str],
		status: OfferStatus = OfferStatus.draft,
	) -> Offer:
		"""Cree une offre."""
		offer = Offer(
			company_id=company_id,
			title=title,
			mission=mission,
			skills=skills,
			status=status,
		)
		self.db.add(offer)
		self.db.commit()
		self.db.refresh(offer)
		return offer

	def update(self, offer: Offer, **data: Any) -> Offer:
		"""Met a jour les champs d'une offre."""
		for field, value in data.items():
			if value is not None and hasattr(offer, field):
				setattr(offer, field, value)
		self.db.add(offer)
		self.db.commit()
		self.db.refresh(offer)
		return offer

	def update_status(self, offer: Offer, status: OfferStatus) -> Offer:
		"""Met a jour l'etat d'une offre."""
		offer.status = status
		self.db.add(offer)
		self.db.commit()
		self.db.refresh(offer)
		return offer
