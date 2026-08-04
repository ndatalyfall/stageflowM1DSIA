"""Ajout d'un identifiant de correlation aux requetes et reponses."""

from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
	"""Ajoute X-Request-ID aux reponses pour faciliter le suivi des logs."""

	async def dispatch(self, request, call_next):
		request_id = request.headers.get("X-Request-ID", str(uuid4()))
		request.state.request_id = request_id
		response = await call_next(request)
		response.headers["X-Request-ID"] = request_id
		return response
