import pytest
from httpx import AsyncClient

from app.schemas.user import RoleName


class TestUserAdminCreation:
	"""Tests d'intégration pour la création d'utilisateurs par un administrateur (POST /users)."""

	@pytest.mark.asyncio
	async def test_admin_create_user_with_role_company(self, admin_client: AsyncClient):
		"""Un administrateur authentifié peut créer une entreprise avec le rôle choisi (201 Created)."""
		payload = {
			"email": "new_company@example.com",
			"full_name": "Nouvelle Entreprise Tech",
			"password": "password123",
			"role": RoleName.company.value,
		}
		response = await admin_client.post("/users", json=payload)

		assert response.status_code == 201
		data = response.json()
		assert data["email"] == "new_company@example.com"
		assert data["full_name"] == "Nouvelle Entreprise Tech"
		assert data["role"] == RoleName.company.value
		assert "id" in data

	@pytest.mark.asyncio
	async def test_admin_create_user_with_role_program_manager(self, admin_client: AsyncClient):
		"""Un administrateur authentifié peut créer un responsable pédagogique (201 Created)."""
		payload = {
			"email": "new_manager@example.com",
			"full_name": "Nouveau Manager",
			"password": "password123",
			"role": RoleName.program_manager.value,
		}
		response = await admin_client.post("/users", json=payload)

		assert response.status_code == 201
		data = response.json()
		assert data["role"] == RoleName.program_manager.value

	@pytest.mark.asyncio
	async def test_non_admin_create_user_forbidden(self, student_client: AsyncClient):
		"""Un utilisateur non-admin ne peut pas créer d'utilisateur (403 Forbidden)."""
		payload = {
			"email": "hacker@example.com",
			"full_name": "Tentative Non Admin",
			"password": "password123",
			"role": RoleName.admin.value,
		}
		response = await student_client.post("/users", json=payload)

		assert response.status_code == 403

	@pytest.mark.asyncio
	async def test_unauthenticated_create_user_unauthorized(self, client: AsyncClient):
		"""Un utilisateur non connecté ne peut pas créer d'utilisateur (401 Unauthorized)."""
		payload = {
			"email": "anon@example.com",
			"full_name": "Anonyme",
			"password": "password123",
			"role": RoleName.student.value,
		}
		response = await client.post("/users", json=payload)

		assert response.status_code == 401

	@pytest.mark.asyncio
	async def test_admin_create_user_duplicate_email(self, admin_client: AsyncClient):
		"""Tenter de créer un utilisateur avec une adresse email existante retourne 409 Conflict."""
		payload = {
			"email": "dup@example.com",
			"full_name": "Utilisateur Test",
			"password": "password123",
			"role": RoleName.student.value,
		}
		res1 = await admin_client.post("/users", json=payload)
		assert res1.status_code == 201

		res2 = await admin_client.post("/users", json=payload)
		assert res2.status_code == 409
		assert res2.json()["detail"] == "Cette adresse email existe deja."
