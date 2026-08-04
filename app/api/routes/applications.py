"""Endpoints de gestion des candidatures aux stages."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.application import Application
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.offer_repository import OfferRepository
from app.schemas.application import (
	ApplicationCreate,
	ApplicationDecision,
	ApplicationRead,
	ApplicationStatus,
)
from app.schemas.offer import OfferStatus
from app.schemas.user import RoleName

router = APIRouter(tags=["applications"])


@router.post(
	"/offers/{offer_id}/applications",
	response_model=ApplicationRead,
	status_code=status.HTTP_201_CREATED,
	summary="Déposer une candidature sur une offre (Étudiant)",
	description="Permet à un étudiant de déposer sa lettre de motivation pour une offre de stage actuellement publiée.",
	responses={
		201: {"description": "Candidature déposée avec succès (statut 'pending')."},
		400: {"description": "L'offre n'est pas à l'état publiée ('published')."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé au rôle étudiant ('student')."},
		404: {"description": "Offre introuvable."},
		409: {"description": "Une candidature active (en attente ou acceptée) existe déjà pour cette offre."},
		422: {"description": "Lettre de motivation invalide (moins de 30 caractères)."},
	},
)
def create_application(
	offer_id: int,
	payload: ApplicationCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Application:
	"""Depose une candidature via ApplicationRepository et OfferRepository."""
	if current_user.role != RoleName.student:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")
	if offer.status != OfferStatus.published:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'offre n'est pas publiee.")

	app_repo = ApplicationRepository(db)
	active_application = app_repo.get_active_application(current_user.id, offer_id)
	if active_application is not None:
		raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Une candidature active existe deja.")

	return app_repo.create(
		student_id=current_user.id,
		offer_id=offer_id,
		cover_letter=payload.cover_letter,
		status=ApplicationStatus.pending,
	)


@router.get(
	"/applications/me",
	response_model=list[ApplicationRead],
	summary="Consulter mes candidatures (Étudiant)",
	description="Retourne la liste de toutes les candidatures déposées par l'étudiant authentifié.",
	responses={
		200: {"description": "Liste des candidatures de l'étudiant retournée."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé au rôle étudiant ('student')."},
	},
)
def list_my_applications(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[Application]:
	"""Liste les candidatures de l'etudiant authentifie via ApplicationRepository."""
	if current_user.role != RoleName.student:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	app_repo = ApplicationRepository(db)
	return list(app_repo.list_for_student(current_user.id))


@router.get(
	"/offers/{offer_id}/applications",
	response_model=list[ApplicationRead],
	summary="Consulter les candidatures d'une offre (Entreprise propriétaire / Responsable)",
	description="Retourne les candidatures soumises pour une offre spécifique. Accessible au responsable pédagogique ou à l'entreprise propriétaire de l'offre.",
	responses={
		200: {"description": "Liste des candidatures de l'offre retournée."},
		401: {"description": "Non authentifié."},
		403: {"description": "Accès refusé pour une entreprise ne possédant pas l'offre ou pour d'autres rôles."},
		404: {"description": "Offre introuvable."},
	},
)
def list_offer_applications(
	offer_id: int,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> list[Application]:
	"""Liste les candidatures d'une offre via ApplicationRepository et OfferRepository."""
	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")

	app_repo = ApplicationRepository(db)
	if current_user.role == RoleName.program_manager:
		return list(app_repo.list_for_offer(offer_id))
	if current_user.role == RoleName.company and offer.company_id == current_user.id:
		return list(app_repo.list_for_offer(offer_id))

	raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez pas voir ces candidatures.")


@router.patch(
	"/applications/{application_id}/decision",
	response_model=ApplicationRead,
	summary="Statuer sur une candidature (Responsable uniquement)",
	description="Permet au responsable pédagogique d'accepter ('accept') ou de refuser ('reject') une candidature en attente.",
	responses={
		200: {"description": "Décision enregistrée avec succès."},
		400: {"description": "La candidature n'est plus à l'état en attente ('pending')."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé au responsable pédagogique ('program_manager')."},
		404: {"description": "Candidature introuvable."},
	},
)
def decide_application(
	application_id: int,
	payload: ApplicationDecision,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Application:
	"""Accepte ou refuse une candidature via ApplicationRepository."""
	if current_user.role != RoleName.program_manager:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	app_repo = ApplicationRepository(db)
	application = app_repo.get_by_id(application_id)
	if application is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature introuvable.")
	if application.status != ApplicationStatus.pending:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La candidature n'est plus en attente.")

	new_status = ApplicationStatus.accepted if payload.decision == "accept" else ApplicationStatus.rejected
	return app_repo.update_status(application, new_status)


@router.delete(
	"/applications/{application_id}",
	status_code=status.HTTP_204_NO_CONTENT,
	summary="Retirer une candidature en attente (Étudiant)",
	description="Permet à un étudiant de retirer sa candidature tant qu'elle est à l'état en attente ('pending').",
	responses={
		204: {"description": "Candidature retirée avec succès (statut 'withdrawn')."},
		400: {"description": "Seule une candidature en attente peut être retirée."},
		401: {"description": "Non authentifié."},
		403: {"description": "Vous ne pouvez pas retirer une candidature qui ne vous appartient pas."},
		404: {"description": "Candidature introuvable."},
	},
)
def withdraw_application(
	application_id: int,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> None:
	"""Retire une candidature via ApplicationRepository."""
	if current_user.role != RoleName.student:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	app_repo = ApplicationRepository(db)
	application = app_repo.get_by_id(application_id)
	if application is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidature introuvable.")
	if application.student_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Vous ne pouvez pas retirer cette candidature.")
	if application.status != ApplicationStatus.pending:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seule une candidature en attente peut etre retiree.")

	app_repo.update_status(application, ApplicationStatus.withdrawn)
