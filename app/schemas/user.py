from enum import StrEnum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RoleName(StrEnum):
	student = "student"
	company = "company"
	program_manager = "program_manager"
	admin = "admin"


class UserCreate(BaseModel):
	"""Données requises pour la création d'un utilisateur par un administrateur."""

	model_config = ConfigDict(extra="forbid")

	email: EmailStr
	full_name: str = Field(min_length=2, max_length=150)
	password: str = Field(min_length=8, max_length=128)
	role: RoleName = RoleName.student


class UserUpdateRole(BaseModel):
	"""Nouveau role attribue par un administrateur."""

	role: RoleName


class UserRead(BaseModel):
	"""Representation publique d'un utilisateur."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	email: EmailStr
	full_name: str
	role: RoleName
	is_active: bool
