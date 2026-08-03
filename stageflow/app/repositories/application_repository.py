"""Acces aux donnees des candidatures."""

from collections.abc import Iterable

from sqlalchemy.orm import Session

from app.models.application import Application
from app.schemas.application import ApplicationStatus


class ApplicationRepository:
	"""Repository CRUD pour les candidatures."""

	def __init__(self, db: Session) -> None:
		self.db = db

	def get_by_id(self, application_id: int) -> Application | None:
		"""Retourne une candidature par identifiant."""
		return self.db.get(Application, application_id)

	def get_active_application(self, student_id: int, offer_id: int) -> Application | None:
		"""Retourne une candidature active d'un etudiant pour une offre si elle existe."""
		return (
			self.db.query(Application)
			.filter(
				Application.student_id == student_id,
				Application.offer_id == offer_id,
				Application.status.in_({ApplicationStatus.pending, ApplicationStatus.accepted}),
			)
			.first()
		)

	def list_for_student(self, student_id: int) -> Iterable[Application]:
		"""Retourne les candidatures d'un etudiant."""
		return self.db.query(Application).filter(Application.student_id == student_id).order_by(Application.created_at.desc()).all()

	def list_for_offer(self, offer_id: int) -> Iterable[Application]:
		"""Retourne les candidatures d'une offre."""
		return self.db.query(Application).filter(Application.offer_id == offer_id).order_by(Application.created_at.desc()).all()

	def count_by_status(self) -> dict[str, int]:
		"""Retourne le nombre de candidatures groupe par statut."""
		app_counts = {s.value: 0 for s in ApplicationStatus}
		for application in self.db.query(Application).all():
			app_counts[application.status.value] += 1
		return app_counts

	def create(self, *, student_id: int, offer_id: int, cover_letter: str, status: ApplicationStatus = ApplicationStatus.pending) -> Application:
		"""Cree une candidature."""
		application = Application(
			student_id=student_id,
			offer_id=offer_id,
			cover_letter=cover_letter,
			status=status,
		)
		self.db.add(application)
		self.db.commit()
		self.db.refresh(application)
		return application

	def update_status(self, application: Application, status: ApplicationStatus) -> Application:
		"""Met a jour l'etat d'une candidature."""
		application.status = status
		self.db.add(application)
		self.db.commit()
		self.db.refresh(application)
		return application
