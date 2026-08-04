"""En-tetes HTTP minimaux de durcissement."""

from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
	"""Ajoute les en-tetes de protection demandes par le sujet."""

	async def dispatch(self, request, call_next):
		response = await call_next(request)
		response.headers["X-Content-Type-Options"] = "nosniff"
		response.headers["X-Frame-Options"] = "DENY"
		return response
