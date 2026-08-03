from fastapi import FastAPI

from app.api.routes import applications, auth, offers, users
from app.middlewares.request_id import RequestIdMiddleware
from app.middlewares.security_headers import SecurityHeadersMiddleware

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
)

app.add_middleware(RequestIdMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(offers.router)
app.include_router(applications.router)
