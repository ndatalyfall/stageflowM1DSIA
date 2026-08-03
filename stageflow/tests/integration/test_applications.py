import pytest
from httpx import AsyncClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
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
		mission="Developpement de pipelines ETL FastAPI et Spark.",
		skills=["Python", "FastAPI", "SQLAlchemy", "PyTest"],
		status=status,
	)
	db.add(offer)
	db.commit()
	db.refresh(offer)
	return offer


class TestApplicationIntegration:
	"""Tests d'integration pour le modele Application et ses endpoints."""

	# --- CREATION DE CANDIDATURE --- #

	@pytest.mark.asyncio
	async def test_create_application_success(
		self, student_client: AsyncClient, company_user: User, student_user: User, db_session: Session
	):
		"""Un etudiant authentifie postule avec succes a une offre publiee (201 Created)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		payload = {
			"cover_letter": "Je suis tres motive par ce poste de Stage Data Engineer Python au sein de votre equipe."
		}
		response = await student_client.post(f"/offers/{offer.id}/applications", json=payload)

		assert response.status_code == 201
		data = response.json()
		assert data["offer_id"] == offer.id
		assert data["student_id"] == student_user.id
		assert data["cover_letter"] == payload["cover_letter"]
		assert data["status"] == ApplicationStatus.pending.value
		assert "id" in data
		assert "created_at" in data
		assert "updated_at" in data

	@pytest.mark.asyncio
	async def test_create_application_draft_offer_rejected(
		self, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Impossible de postuler a une offre non publiee (400 Bad Request)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.draft)

		payload = {
			"cover_letter": "Candidature sur offre en brouillon qui devrait echouer lors du traitement."
		}
		response = await student_client.post(f"/offers/{offer.id}/applications", json=payload)

		assert response.status_code == 400
		assert response.json()["detail"] == "L'offre n'est pas publiee."

	@pytest.mark.asyncio
	async def test_create_application_forbidden_for_non_student(
		self, company_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Une entreprise ne peut pas deposer de candidature (403 Forbidden)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		payload = {
			"cover_letter": "Lettre de motivation envoyee par une entreprise."
		}
		response = await company_client.post(f"/offers/{offer.id}/applications", json=payload)

		assert response.status_code == 403
		assert response.json()["detail"] == "Role insuffisant."

	@pytest.mark.asyncio
	async def test_create_application_duplicate_active(
		self, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Un etudiant ne peut pas deposer deux candidatures actives sur la meme offre (409 Conflict)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		payload = {
			"cover_letter": "Premiere candidature valide pour l'offre de stage Data Engineer."
		}
		res1 = await student_client.post(f"/offers/{offer.id}/applications", json=payload)
		assert res1.status_code == 201

		# Deuxieme tentative
		res2 = await student_client.post(f"/offers/{offer.id}/applications", json=payload)
		assert res2.status_code == 409
		assert res2.json()["detail"] == "Une candidature active existe deja."

	@pytest.mark.asyncio
	async def test_create_application_cover_letter_too_short(
		self, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Lettre de motivation trop courte (<30 caracteres) -> 422 Unprocessable Entity."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		payload = {"cover_letter": "Trop court"}
		response = await student_client.post(f"/offers/{offer.id}/applications", json=payload)

		assert response.status_code == 422

	@pytest.mark.asyncio
	async def test_create_application_non_existent_offer(self, student_client: AsyncClient):
		"""ID d'offre inexistant -> 404 Not Found."""
		payload = {
			"cover_letter": "Candidature sur une offre qui n'existe pas dans la base de donnees."
		}
		response = await student_client.post("/offers/999999/applications", json=payload)

		assert response.status_code == 404
		assert response.json()["detail"] == "Offre introuvable."

	@pytest.mark.asyncio
	async def test_unauthenticated_request_rejected(self, client: AsyncClient):
		"""Sans token d'authentification -> 401 Unauthorized."""
		payload = {
			"cover_letter": "Candidature anonyme envoyee sans header d'autorisation."
		}
		response = await client.post("/offers/1/applications", json=payload)

		assert response.status_code == 401

	# --- LISTING DES CANDIDATURES --- #

	@pytest.mark.asyncio
	async def test_list_my_applications_student(
		self, student_client: AsyncClient, company_user: User, student_user: User, db_session: Session
	):
		"""Un etudiant consulte la liste de ses propres candidatures (200 OK)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		# Creer une candidature
		payload = {
			"cover_letter": "Ma candidature pour valider la liste personnelle sous le profil etudiant."
		}
		create_res = await student_client.post(f"/offers/{offer.id}/applications", json=payload)
		assert create_res.status_code == 201

		response = await student_client.get("/applications/me")
		assert response.status_code == 200
		data = response.json()
		assert isinstance(data, list)
		assert len(data) == 1
		assert data[0]["student_id"] == student_user.id
		assert data[0]["offer_id"] == offer.id

	@pytest.mark.asyncio
	async def test_list_my_applications_forbidden_non_student(self, company_client: AsyncClient):
		"""Seul un etudiant peut consulter /applications/me (403 Forbidden)."""
		response = await company_client.get("/applications/me")
		assert response.status_code == 403
		assert response.json()["detail"] == "Role insuffisant."

	@pytest.mark.asyncio
	async def test_list_offer_applications_company_owner(
		self, student_client: AsyncClient, company_client: AsyncClient, company_user: User, db_session: Session
	):
		"""L'entreprise propriétaire d'une offre peut voir les candidatures (200 OK)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		payload = {
			"cover_letter": "Candidature destinee a l'entreprise proprietaire de la fiche de poste."
		}
		await student_client.post(f"/offers/{offer.id}/applications", json=payload)

		response = await company_client.get(f"/offers/{offer.id}/applications")
		assert response.status_code == 200
		data = response.json()
		assert len(data) == 1
		assert data[0]["offer_id"] == offer.id

	@pytest.mark.asyncio
	async def test_list_offer_applications_other_company_forbidden(
		self, client: AsyncClient, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Une autre entreprise ne peut pas voir les candidatures d'une offre qui ne lui appartient pas (403)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)

		# Postuler
		await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature pour tester le controle d'acces inter-entreprises."},
		)

		# Creer une autre entreprise
		other_company = User(
			email="other_company@example.com",
			full_name="Autre Entreprise",
			hashed_password="hash",
			role=RoleName.company,
			is_active=True,
		)
		db_session.add(other_company)
		db_session.commit()
		db_session.refresh(other_company)

		other_token = create_access_token(subject=str(other_company.id), role=RoleName.company.value)
		client.headers["Authorization"] = f"Bearer {other_token}"

		response = await client.get(f"/offers/{offer.id}/applications")
		assert response.status_code == 403
		assert response.json()["detail"] == "Vous ne pouvez pas voir ces candidatures."

	@pytest.mark.asyncio
	async def test_list_offer_applications_program_manager(
		self, student_client: AsyncClient, manager_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Le responsable pedagogique peut consulter les candidatures de n'importe quelle offre (200 OK)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature visible par le responsable pedagogique du master."},
		)

		response = await manager_client.get(f"/offers/{offer.id}/applications")
		assert response.status_code == 200
		assert len(response.json()) == 1

	# --- DECISION PEDAGOGIQUE --- #

	@pytest.mark.asyncio
	async def test_decide_application_accept(
		self, student_client: AsyncClient, manager_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Le responsable pedagogique accepte une candidature en attente (status -> accepted)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature a accepter par le responsable pedagogique."},
		)
		app_id = res.json()["id"]

		decision_payload = {"decision": "accept", "comment": "Candidature conforme au profil."}
		response = await manager_client.patch(f"/applications/{app_id}/decision", json=decision_payload)

		assert response.status_code == 200
		data = response.json()
		assert data["id"] == app_id
		assert data["status"] == ApplicationStatus.accepted.value

	@pytest.mark.asyncio
	async def test_decide_application_reject(
		self, student_client: AsyncClient, manager_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Le responsable pedagogique refuse une candidature en attente (status -> rejected)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature a refuser par le responsable pedagogique."},
		)
		app_id = res.json()["id"]

		decision_payload = {"decision": "reject", "comment": "Competences insuffisantes."}
		response = await manager_client.patch(f"/applications/{app_id}/decision", json=decision_payload)

		assert response.status_code == 200
		data = response.json()
		assert data["status"] == ApplicationStatus.rejected.value

	@pytest.mark.asyncio
	async def test_decide_application_forbidden_for_student(
		self, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Un etudiant ne peut pas statuer sur une candidature (403 Forbidden)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Tentative de decision par l'etudiant lui-meme."},
		)
		app_id = res.json()["id"]

		response = await student_client.patch(f"/applications/{app_id}/decision", json={"decision": "accept"})
		assert response.status_code == 403

	@pytest.mark.asyncio
	async def test_decide_application_not_pending(
		self, student_client: AsyncClient, manager_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Impossible de statuer sur une candidature deja traitee (400 Bad Request)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature qui sera traitee une premiere fois puis re-testee."},
		)
		app_id = res.json()["id"]

		# Premiere decision : accept
		await manager_client.patch(f"/applications/{app_id}/decision", json={"decision": "accept"})

		# Deuxieme tentative
		res2 = await manager_client.patch(f"/applications/{app_id}/decision", json={"decision": "reject"})
		assert res2.status_code == 400
		assert res2.json()["detail"] == "La candidature n'est plus en attente."

	# --- RETRAIT DE CANDIDATURE --- #

	@pytest.mark.asyncio
	async def test_withdraw_application_success(
		self, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""L'etudiant peut retirer sa candidature en attente (204 No Content)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature que l'etudiant souhaite retirer avant validation."},
		)
		app_id = res.json()["id"]

		response = await student_client.delete(f"/applications/{app_id}")
		assert response.status_code == 204

		# Verifier le statut passe a withdrawn
		app_in_db = db_session.get(Application, app_id)
		assert app_in_db.status == ApplicationStatus.withdrawn

	@pytest.mark.asyncio
	async def test_withdraw_application_other_student_forbidden(
		self, client: AsyncClient, student_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Un autre etudiant ne peut pas retirer la candidature d'un tiers (403 Forbidden)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature d'un premier etudiant a proteger contre les tiers."},
		)
		app_id = res.json()["id"]

		# Autre etudiant
		other_student = User(
			email="other_student@example.com",
			full_name="Autre Etudiant",
			hashed_password="hash",
			role=RoleName.student,
			is_active=True,
		)
		db_session.add(other_student)
		db_session.commit()
		db_session.refresh(other_student)

		other_token = create_access_token(subject=str(other_student.id), role=RoleName.student.value)
		client.headers["Authorization"] = f"Bearer {other_token}"

		response = await client.delete(f"/applications/{app_id}")
		assert response.status_code == 403
		assert response.json()["detail"] == "Vous ne pouvez pas retirer cette candidature."

	@pytest.mark.asyncio
	async def test_withdraw_application_not_pending(
		self, student_client: AsyncClient, manager_client: AsyncClient, company_user: User, db_session: Session
	):
		"""Impossible de retirer une candidature si elle n'est plus en attente (400 Bad Request)."""
		offer = create_test_offer(db_session, company_user, status=OfferStatus.published)
		res = await student_client.post(
			f"/offers/{offer.id}/applications",
			json={"cover_letter": "Candidature qui sera acceptee avant de tenter un retrait."},
		)
		app_id = res.json()["id"]

		# Accepter la candidature
		await manager_client.patch(f"/applications/{app_id}/decision", json={"decision": "accept"})

		# Tenter de la retirer
		response = await student_client.delete(f"/applications/{app_id}")
		assert response.status_code == 400
		assert response.json()["detail"] == "Seule une candidature en attente peut etre retiree."

	@pytest.mark.asyncio
	async def test_withdraw_application_not_found(self, student_client: AsyncClient):
		"""Tentative de retrait d'un ID inexistant (404 Not Found)."""
		response = await student_client.delete("/applications/999999")
		assert response.status_code == 404
		assert response.json()["detail"] == "Candidature introuvable."
