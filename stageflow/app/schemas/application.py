from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ApplicationStatus(StrEnum):
	"""Etats possibles d'une candidature."""

	# Une candidature commence en attente, puis devient acceptee, rejetee ou retiree.
	pending = "pending"
	accepted = "accepted"
	rejected = "rejected"
	withdrawn = "withdrawn"


class ApplicationCreate(BaseModel):
	"""Candidature deposee par un etudiant."""

	# Les champs non prevus par le contrat API sont refuses.
	model_config = ConfigDict(extra="forbid")

	# Cette validation evite les lettres vides ou trop longues avant la logique metier.
	cover_letter: str = Field(min_length=30, max_length=5000)


class ApplicationDecision(BaseModel):
	"""Decision prise par un responsable pedagogique."""

	# Le schema limite les decisions aux deux sorties du workflow.
	decision: str = Field(pattern="^(accept|reject)$")
	comment: str | None = Field(default=None, max_length=1000)


class ApplicationRead(BaseModel):
	"""Representation d'une candidature dans les reponses API."""

	model_config = ConfigDict(from_attributes=True)

	id: int
	student_id: int
	offer_id: int
	cover_letter: str
	status: ApplicationStatus
	created_at: datetime
	updated_at: datetime
