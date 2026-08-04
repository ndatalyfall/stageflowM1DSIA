from datetime import datetime
from enum import StrEnum
from pydantic import BaseModel, ConfigDict, Field


class OfferStatus(StrEnum):
	"""Etats possibles d'une offre."""

	draft = "draft"
	submitted = "submitted"
	published = "published"
	rejected = "rejected"


class OfferCreate(BaseModel):
	"""Donnees d'une offre creee par une entreprise."""

	model_config = ConfigDict(extra="forbid")

	title: str = Field(min_length=3, max_length=200)
	mission: str = Field(min_length=20)
	skills: list[str] = Field(min_length=1, max_length=30)


class OfferUpdate(BaseModel):
	"""Champs modifiables d'une offre encore editable."""

	model_config = ConfigDict(extra="forbid")

	title: str | None = Field(default=None, min_length=3, max_length=200)
	mission: str | None = Field(default=None, min_length=20)
	skills: list[str] | None = Field(default=None, min_length=1, max_length=30)


class OfferReview(BaseModel):
	"""Decision d'un responsable pedagogique sur une offre soumise."""

	decision: str = Field(pattern="^(publish|reject)$")
	comment: str | None = Field(default=None, max_length=1000)


class OfferRead(BaseModel):
	"""Representation d'une offre dans les reponses API."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	company_id: int
	title: str
	mission: str
	skills: list[str]
	status: OfferStatus
	created_at: datetime
	updated_at: datetime
