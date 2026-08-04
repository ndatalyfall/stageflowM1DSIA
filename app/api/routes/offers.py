"""Endpoints de gestion des offres de stage."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.offer import Offer
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.repositories.offer_repository import OfferRepository
from app.schemas.offer import OfferCreate, OfferRead, OfferReview, OfferStatus, OfferUpdate
from app.schemas.user import RoleName

router = APIRouter(prefix="/offers", tags=["offers"])


@router.post(
	"/create_offer",
	response_model=OfferRead,
	status_code=status.HTTP_201_CREATED,
	summary="Créer une offre de stage (Entreprise)",
	description="Crée une nouvelle offre de stage à l'état de brouillon ('draft') pour l'entreprise authentifiée.",
	responses={
		201: {"description": "Offre brouillon créée avec succès."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé aux comptes de rôle entreprise ('company')."},
	},
)
def create_offer(
	payload: OfferCreate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Offer:
	"""Cree une offre brouillon via OfferRepository."""
	if current_user.role != RoleName.company:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce role ne peut pas effectuer cette action.")

	offer_repo = OfferRepository(db)
	return offer_repo.create(
		company_id=current_user.id,
		title=payload.title,
		mission=payload.mission,
		skills=payload.skills,
		status=OfferStatus.draft,
	)


@router.get(
	"/published",
	response_model=list[OfferRead],
	summary="Lister les offres de stage",
	description="Retourne la liste des offres publiées.",
	responses={
		200: {"description": "Liste des offres publiées retournée."},
	},
)
def list_published_offers(db: Session = Depends(get_db)) -> list[Offer]:
	"""Liste les offres via OfferRepository."""
	offer_repo = OfferRepository(db)
	return list(offer_repo.list_all(published_only=True))


@router.get(
	"/my_offers",
	response_model=list[OfferRead],
	summary="Lister toutes les offres de stage de l'entreprise",
	description="Retourne la liste de toutes les offres de l'entreprise.",
	responses={
		200: {"description": "Liste des offres retournée."},
	},
)
def list_my_offers(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user)
) -> list[Offer]:
	"""Liste les offres via OfferRepository."""
	if current_user.role != RoleName.company:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Ce role ne peut pas effectuer cette action.")

	offer_repo = OfferRepository(db)
	return list(offer_repo.list_all(created_by=current_user.id))


@router.get(
	"/stats/summary",
	tags=["statistics"],
	summary="Obtenir les statistiques globales (Responsable uniquement)",
	description="Retourne le décompte des offres et des candidatures par statut. Réservé au responsable pédagogique.",
	responses={
		200: {"description": "Statistiques retournées avec succès."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé au responsable pédagogique ('program_manager')."},
	},
)
def offer_statistics(
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> dict[str, dict[str, int]]:
	"""Retourne les nombres d'offres et de candidatures par statut via les Repositories."""
	if current_user.role != RoleName.program_manager:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	offer_repo = OfferRepository(db)
	app_repo = ApplicationRepository(db)

	return {
		"offers_by_status": offer_repo.count_by_status(),
		"applications_by_status": app_repo.count_by_status(),
	}


@router.get(
	"/{offer_id}",
	response_model=OfferRead,
	summary="Obtenir une offre par identifiant",
	description="Retourne la fiche détaillée d'une offre de stage à partir de son identifiant.",
	responses={
		200: {"description": "Fiche de l'offre retournée."},
		404: {"description": "Offre introuvable."},
	},
)
def read_offer(offer_id: int, db: Session = Depends(get_db)) -> Offer:
	"""Retourne une offre par son identifiant via OfferRepository."""
	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")
	return offer


@router.patch(
	"/{offer_id}",
	response_model=OfferRead,
	summary="Modifier une offre brouillon (Entreprise)",
	description="Permet à une entreprise de modifier son offre tant qu'elle est encore à l'état brouillon ('draft').",
	responses={
		200: {"description": "Offre mise à jour avec succès."},
		400: {"description": "Seule une offre en état brouillon est modifiable."},
		401: {"description": "Non authentifié."},
		403: {"description": "L'offre appartient à une autre entreprise ou rôle insuffisant."},
		404: {"description": "Offre introuvable."},
	},
)
def update_offer(
	offer_id: int,
	payload: OfferUpdate,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Offer:
	"""Modifie une offre brouillon via OfferRepository."""
	if current_user.role != RoleName.company:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")
	if offer.company_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette offre appartient a une autre entreprise.")
	if offer.status != OfferStatus.draft:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seule une offre brouillon est modifiable.")

	update_data = payload.model_dump(exclude_unset=True)
	return offer_repo.update(offer, **update_data)


@router.patch(
	"/{offer_id}/submit",
	response_model=OfferRead,
	summary="Soumettre une offre pour validation (Entreprise)",
	description="Fait passer une offre de l'état brouillon ('draft') à soumis ('submitted') pour revue pédagogique.",
	responses={
		200: {"description": "Offre soumise avec succès."},
		400: {"description": "L'offre est incomplète ou n'est pas à l'état brouillon."},
		401: {"description": "Non authentifié."},
		403: {"description": "L'offre appartient à une autre entreprise."},
		404: {"description": "Offre introuvable."},
	},
)
def submit_offer(
	offer_id: int,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Offer:
	"""Soumet une offre complete via OfferRepository."""
	if current_user.role != RoleName.company:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")
	if offer.company_id != current_user.id:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cette offre appartient a une autre entreprise.")
	if offer.status != OfferStatus.draft:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seule une offre brouillon peut etre soumise.")
	if not offer.title or not offer.mission or not offer.skills or not offer.company_id:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="L'offre est incomplete.")

	return offer_repo.update_status(offer, OfferStatus.submitted)


@router.patch(
	"/{offer_id}/review",
	response_model=OfferRead,
	summary="Publier ou refuser une offre (Responsable uniquement)",
	description="Permet au responsable pédagogique de valider ('publish') ou de rejeter ('reject') une offre soumise.",
	responses={
		200: {"description": "Décision enregistrée avec succès."},
		400: {"description": "Seule une offre soumise ('submitted') peut être revue."},
		401: {"description": "Non authentifié."},
		403: {"description": "Réservé au responsable pédagogique ('program_manager')."},
		404: {"description": "Offre introuvable."},
	},
)
def review_offer(
	offer_id: int,
	payload: OfferReview,
	db: Session = Depends(get_db),
	current_user: User = Depends(get_current_user),
) -> Offer:
	"""Publie ou refuse une offre soumise via OfferRepository."""
	if current_user.role != RoleName.program_manager:
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")

	offer_repo = OfferRepository(db)
	offer = offer_repo.get_by_id(offer_id)
	if offer is None:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable.")
	if offer.status != OfferStatus.submitted:
		raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seule une offre soumise peut etre revue.")

	new_status = OfferStatus.published if payload.decision == "publish" else OfferStatus.rejected
	return offer_repo.update_status(offer, new_status)
