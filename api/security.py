from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)

ADJUSTER = "adjuster"


def get_state(request: Request):
    return request.app.state.claimpilot


def _matches(credentials: HTTPAuthorizationCredentials | None, expected: str | None) -> bool:
    if credentials is None or expected is None:
        return False
    return hmac.compare_digest(credentials.credentials.encode(), expected.encode())


def require_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> None:
    """DEMO_API_TOKEN (or the adjuster token); open only if unset and ALLOW_OPEN_API=1."""
    settings = get_state(request).settings
    if settings.demo_api_token is None:
        if settings.allow_open_api:
            return
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "API token not configured")
    if _matches(credentials, settings.demo_api_token) or _matches(
        credentials, settings.adjuster_api_token
    ):
        return
    raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing or invalid bearer token")


def require_adjuster(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> str:
    """Adjuster credential from ADJUSTER_API_TOKEN; returns the reviewer identity.

    Fails closed: without ADJUSTER_API_TOKEN nobody can review, even if the API is open.
    """
    expected = get_state(request).settings.adjuster_api_token
    if expected is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "claim review is disabled: ADJUSTER_API_TOKEN is not set"
        )
    if credentials is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "adjuster bearer token required")
    if not _matches(credentials, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "adjuster role required")
    return ADJUSTER
