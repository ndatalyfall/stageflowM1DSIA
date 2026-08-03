"""Dependances centralisees d'autorisation par role."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.security import get_token_payload
from app.schemas.user import RoleName


def require_roles(*allowed_roles: RoleName) -> Callable:
	"""Construit une dependance qui autorise uniquement les roles fournis."""
	def dependency(payload: dict = Depends(get_token_payload)) -> dict:
		if payload.get("role") not in {role.value for role in allowed_roles}:
			raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role insuffisant.")
		return payload

	return dependency
