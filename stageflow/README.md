# StageFlow - API de gestion sécurisée des stages data

**StageFlow** est l'API REST interne d'un Master DSIA pour suivre et sécuriser le workflow complet des stages de données : publication des offres, candidatures des étudiants, arbitrages pédagogiques et administration des accès.

---

## 🎯 Architecture & Invariants métier

L'application respecte strictement le **Repository Pattern** : aucune route FastAPI n'appelle directement SQLAlchemy pour lire ou modifier le domaine. Les responsabilités sont isolées en sous-modules :

```text
stageflow/
├── app/
│   ├── main.py              # Point d'entrée FastAPI & configuration OpenAPI
│   ├── api/
│   │   └── routes/          # Endpoints REST (auth, users, offers, applications)
│   ├── core/                # Sécurité (JWT, bcrypt), permissions RBAC, config
│   ├── db/                  # Session SQLAlchemy & Base déclarative
│   ├── models/              # Modèles ORM (User, Offer, Application)
│   ├── schemas/             # DTOs Pydantic v2 d'entrée/sortie
│   ├── repositories/        # Repository Pattern (UserRepository, OfferRepository, ApplicationRepository)
│   ├── middlewares/         # Middlewares (request_id, security_headers)
│   └── utils/               # Utilitaires (hashing, pagination, time)
├── tests/
│   ├── unit/                # Tests unitaires (sécurité, JWT, mdp)
│   ├── integration/         # Tests d'intégration (candidatures, offres, rôles)
│   └── fixtures/            # Factories & fixtures pytest
├── alembic/                 # Migrations de base de données
├── .github/workflows/ci.yml # Pipeline GitHub Actions & Codecov
├── Dockerfile               # Image Docker non-root
└── docker-compose.yml       # Orchestration locale (API + PostgreSQL)
```

---

## 🔐 Matrice des Rôles & Habilitations (RBAC)

L'API gère 4 rôles utilisateurs distincts :

| Rôle | Description & Droits d'accès |
| :--- | :--- |
| **`student`** | Consulter les offres publiées, déposer sa candidature sur une offre (1 seule active par offre), consulter ses candidatures (`/applications/me`) et retirer une candidature tant qu'elle est en attente (`pending`). |
| **`company`** | Créer des offres de stage en brouillon (`draft`), modifier ses offres brouillon, soumettre une offre (`submitted`) et consulter les candidatures sur ses propres offres. |
| **`program_manager`** | Publier ou refuser une offre soumise (`publish`/`reject`), valider ou refuser une candidature (`accept`/`reject`), et consulter les statistiques globales (`/offers/stats/summary`). |
| **`admin`** | Consulter la liste de tous les utilisateurs, modifier le rôle d'un compte et désactiver un utilisateur (`soft delete`) avec traçabilité dans les logs. |

---

## ⚙️ Configuration & Variables d'environnement

1. Copier le fichier d'exemple `.env.example` vers `.env` :
   ```bash
   cp .env.example .env
   ```

2. Adapter les variables d'environnement si nécessaire :
   ```ini
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/stageflow
   DEBUG=True
   APP_NAME=StageFlow API
   ENVIRONMENT=development
   JWT_SECRET_KEY=development-secret-change-me-32-chars
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   ```

---

## 🚀 Lancement local (sans Docker)

### 1. Installation des dépendances
```bash
pip install -r requirements.txt
```

### 2. Exécution des migrations Alembic
```bash
PYTHONPATH=. alembic upgrade head
```

### 3. Démarrage du serveur Uvicorn
```bash
PYTHONPATH=. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API est accessible sur `http://127.0.0.1:8000`.
- Documentation **Swagger UI** : `http://127.0.0.1:8000/docs`
- Documentation **ReDoc** : `http://127.0.0.1:8000/redoc`

---

## 🐳 Lancement via Docker & Docker-Compose

Pour démarrer l'ensemble des services (Base de données PostgreSQL 16 + API FastAPI) en une commande :

```bash
docker-compose up --build
```

- L'API écoute sur le port `8000`.
- La base PostgreSQL est automatiquement configurée avec un *healthcheck* et des volumes persistants.
- L'image de l'API utilise un utilisateur non-privilégié (`appuser`) pour respecter les règles de sécurité en production.

---

## 🧪 Lancement des Tests & Couverture

Les tests unitaires et d'intégration utilisent **pytest** et une base de données SQLite en mémoire isolée par test.

### Exécuter l'ensemble des tests :
```bash
PYTHONPATH=. pytest tests/ -v
```

### Exécuter les tests avec rapport de couverture de code :
```bash
PYTHONPATH=. pytest --cov=app --cov-report=term-missing
```

---

## 🛠️ Pipeline CI/CD GitHub Actions & Codecov

Le fichier `.github/workflows/ci.yml` exécute automatiquement à chaque `push` ou `pull_request` sur la branche `main` :
1. Démarrage d'un service PostgreSQL 16 de test.
2. Exécution de la suite complète de tests pytest.
3. Génération du rapport de couverture XML (`coverage.xml`).
4. Transmission du rapport de couverture vers **Codecov**.
5. Construction et vérification de l'image Docker de production.
