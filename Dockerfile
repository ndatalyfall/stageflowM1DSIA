# FROM python:3.12.2
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# RUN useradd --create-home --shell /usr/sbin/nologin appuser
# USER appuser
# EXPOSE 8000
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ---- Stage 1 : Build des dépendances ----
FROM python:3.12-slim AS builder

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

WORKDIR /build

RUN python -m venv "${VIRTUAL_ENV}"
# Copier SEULEMENT les requirements (cache Docker)
COPY requirements.txt .

RUN pip install --upgrade pip && \
pip install --no-cache-dir -r requirements.txt

# ---- Stage 2 : Image de production (légère) ----
FROM python:3.12-slim AS production

# Déclarer les variables d'environnement pour l'environnement virtuel
ENV VIRTUAL_ENV=/opt/venv
# Déclarer le PATH pour utiliser l'environnement virtuel
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
# Sécurité : utilisateur non-root
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
# Copier le code de l'application
COPY --chown=appuser:appgroup app/ ./papp/

COPY --chown=appuser:appgroup alembic/ ./alembic/
COPY --chown=appuser:appgroup alembic.ini .

USER appuser
# Variables d'environnement par défaut
ENV PYTHONDONTWRITEBYTECODE=1 \
PYTHONUNBUFFERED=1 \
PORT=8000

EXPOSE $PORT

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
CMD python -c "import httpx; httpx.get('http://localhost:$PORT/health')" || exit 1

# Gunicorn + Uvicorn workers (production)
CMD ["sh", "-c", \
"gunicorn app.main:app \
-k uvicorn_worker.UvicornWorker \
--workers 4 \
--bind 0.0.0.0:$PORT \
--timeout 60 \
--access-logfile - \
--error-logfile -"]
