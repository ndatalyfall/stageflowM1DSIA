from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
	"""Identifiants envoyes lors de la connexion."""

	email: EmailStr
	password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
	"""Donnees necessaires a la creation d'un compte etudiant."""

	model_config = ConfigDict(extra="forbid")

	email: EmailStr
	full_name: str = Field(min_length=2, max_length=150)
	password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
	"""Jeton retourne apres une authentification reussie."""

	access_token: str
	token_type: str = "bearer"
