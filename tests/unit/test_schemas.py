import pytest
from pydantic import ValidationError

from app.schemas.user import RoleName, UserCreate


class TestUserCreateSchema:
	def test_user_create_default_role(self):
		data = {
			"email": "user@example.com",
			"full_name": "Jean Dupont",
			"password": "password123",
		}
		user_in = UserCreate(**data)
		assert user_in.email == "user@example.com"
		assert user_in.role == RoleName.student

	def test_user_create_explicit_role(self):
		data = {
			"email": "company@example.com",
			"full_name": "Entreprise Tech",
			"password": "password123",
			"role": "company",
		}
		user_in = UserCreate(**data)
		assert user_in.role == RoleName.company

	def test_user_create_invalid_role(self):
		data = {
			"email": "user@example.com",
			"full_name": "Test User",
			"password": "password123",
			"role": "superman",
		}
		with pytest.raises(ValidationError):
			UserCreate(**data)

	def test_user_create_forbidden_extra_fields(self):
		data = {
			"email": "user@example.com",
			"full_name": "Test User",
			"password": "password123",
			"is_admin": True,
		}
		with pytest.raises(ValidationError):
			UserCreate(**data)
