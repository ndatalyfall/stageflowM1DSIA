import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.models.application import Application
from app.models.offer import Offer
from app.models.user import User
from app.schemas.application import ApplicationStatus
from app.schemas.offer import OfferStatus
from app.schemas.user import RoleName


def create_test_offer(db: Session, company_user: User, status: OfferStatus = OfferStatus.published) -> Offer:
	"""Helper pour creer une offre de stage en base de donnees."""
	offer = Offer(
		company_id=company_user.id,
		title="Stage Data Engineer Python",
		mission="Developpement de pipelines ETL FastAPI et Spark pour une solution de data platform.",
		skills=["Python", "FastAPI", "SQLAlchemy", "PyTest"],
		status=status,
	)
	db.add(offer)
	db.commit()
	db.refresh(offer)
	return offer


class TestOfferIntegration:
	"""Tests d'integration pour les endpoints d'offres."""

	@pytest.mark.asyncio
	async def test_create_offer_success_by_company(self, company_client: AsyncClient, company_user: User):
		"""Une entreprise authentifiee peut creer une offre brouillon (201 Created)."""
		payload = {
			"title": "Stage Data Engineer",
			"mission": "Je vais construire des pipelines ETL robustes et monitorer l'integration des donnees.",
			"skills": ["Python", "FastAPI", "SQLAlchemy"],
		}
		response = await company_client.post("/offers/create_offer", json=payload)

		assert response.status_code == 201
		data = response.json()
		assert data["company_id"] == company_user.id
		assert data["title"] == payload["title"]
		assert data["status"] == OfferStatus.draft.value

	@pytest.mark.asyncio
	async def test_create_offer_forbidden_for_non_company(self, student_client: AsyncClient):
		"""Un etudiant ne peut pas creer une offre (403 Forbidden)."""
		payload = {
			"title": "Stage Data Engineer",
			"mission": "Je vais construire des pipelines ETL robustes et monitorer l'integration des donnees.",
			"skills": ["Python", "FastAPI", "SQLAlchemy"],
		}
		response = await student_client.post("/offers/create_offer", json=payload)

		assert response.status_code == 403
		assert response.json()["detail"] == "Ce role ne peut pas effectuer cette action."

	@pytest.mark.asyncio
	async def test_list_published_offers(self, client: AsyncClient, company_user: User, db_session: Session):
		"""La route publique retourne uniquement les offres publiees."""
		create_test_offer(db_session, company_user, status=OfferStatus.published)
		create_test_offer(db_session, company_user, status=OfferStatus.draft)

		response = await client.get("/offers/published")

		assert response.status_code == 200
		data = response.json()
		assert len(data) == 1
		assert data[0]["status"] == OfferStatus.published.value

	@pytest.mark.asyncio
	async def test_list_my_offers_for_company(self, company_client: AsyncClient, company_user: User, db_session: Session):
		"""Une entreprise authentifiee liste ses offres propres."""
		create_test_offer(db_session, company_user, status=OfferStatus.draft)
		create_test_offer(db_session, company_user, status=OfferStatus.draft)

		response = await company_client.get("/offers/my_offers")

		assert response.status_code == 200
		data = response.json()
		assert len(data) == 2
		assert all(item["company_id"] == company_user.id for item in data)

	@pytest.mark.asyncio
	async def test_offer_statistics_for_program_manager(
		self,
		manager_client: AsyncClient,
		company_user: User,
		student_user: User,
		db_session: Session,
	):
		"""Le responsable peut consulter un resume de statistiques offres/candidatures."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		application = Application(
			student_id=student_user.id,
			offer_id=offer.id,
			cover_letter="Je veux vraiment ce stage et je mets en avant mes motivations.",
			status=ApplicationStatus.pending,
		)
		db_session.add(application)
		db_session.commit()

		response = await manager_client.get("/offers/stats/summary")

		assert response.status_code == 200
		data = response.json()
		assert "offers_by_status" in data
		assert "applications_by_status" in data
		assert data["offers_by_status"][OfferStatus.published.value] >= 1
		assert data["applications_by_status"][ApplicationStatus.pending.value] >= 1

	@pytest.mark.asyncio
	async def test_read_offer_by_id(self, client: AsyncClient, company_user: User, db_session: Session):
		"""Une offre existante peut etre lue par identifiant."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		response = await client.get(f"/offers/{offer.id}")

		assert response.status_code == 200
		data = response.json()
		assert data["id"] == offer.id
		assert data["title"] == offer.title

	@pytest.mark.asyncio
	async def test_update_offer_success_by_company(self, company_client: AsyncClient, company_user: User, db_session: Session):
		"""Une entreprise peut modifier son offre brouillon."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.draft)
		payload = {"title": "Nouveau titre d'offre", "mission": "Mission mise a jour pour le stage de data engineer.", "skills": ["Python", "SQLAlchemy"]}

		response = await company_client.patch(f"/offers/{offer.id}", json=payload)

		assert response.status_code == 200
		data = response.json()
		assert data["title"] == payload["title"]
		assert data["mission"] == payload["mission"]
		assert data["skills"] == payload["skills"]

	@pytest.mark.asyncio
	async def test_submit_offer_success_by_company(self, company_client: AsyncClient, company_user: User, db_session: Session):
		"""Une entreprise peut soumettre une offre brouillon pour revue."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.draft)

		response = await company_client.patch(f"/offers/{offer.id}/submit")

		assert response.status_code == 200
		data = response.json()
		assert data["status"] == OfferStatus.submitted.value

	@pytest.mark.asyncio
	async def test_review_offer_publish_by_manager(self, manager_client: AsyncClient, company_user: User, db_session: Session):
		"""Un responsable peut publier une offre soumise."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.submitted)
		payload = {"decision": "publish"}

		response = await manager_client.patch(f"/offers/{offer.id}/review", json=payload)

		assert response.status_code == 200
		data = response.json()
		assert data["status"] == OfferStatus.published.value
