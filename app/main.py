from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.routes import applications, auth, offers, users
from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.middlewares.request_id import RequestIdMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Initialise la base de données et crée l'administrateur par défaut au démarrage."""
	db = SessionLocal()
	try:
		init_db(db)
	except Exception:
		pass
	finally:
		db.close()
	yield


tags_metadata = [
	{
		"name": "auth",
		"description": "Gestion de l'authentification, de la création de compte étudiant et de l'émission de tokens JWT.",
	},
	{
		"name": "users",
		"description": "Consultation des profils utilisateurs et administration des rôles.",
	},
	{
		"name": "offers",
		"description": "Publication, gestion et revue pédagogique des offres de stage data.",
	},
	{
		"name": "applications",
		"description": "Dépôt, suivi et arbitrage des candidatures de stage.",
	},
	{
		"name": "statistics",
		"description": "Statistiques et métriques réservées aux responsables pédagogiques du Master DSIA.",
	},
]

app = FastAPI(
	title="StageFlow API",
	description=(
		"API sécurisée de gestion des stages data du Master DSIA.\n\n"
		"Permet aux étudiants d'explorer les offres et de candidater, "
		"aux entreprises d'en proposer et d'en suivre les retours, "
		"et aux responsables pédagogiques d'arbitrer le workflow."
	),
	version="1.0.0",
	openapi_tags=tags_metadata,
	docs_url="/docs",
	redoc_url="/redoc",
	lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health", include_in_schema=False)
async def health():
	"""Endpoint de verification de l'etat de l'API."""
	return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offers.router)
app.include_router(applications.router)
