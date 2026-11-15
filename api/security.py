from __future__ import annotations

import hmac

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


def get_state(request: Request):
    return request.app.state.claimpilot


def require_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> None:
    """Bearer token from DEMO_API_TOKEN; open only if unset and ALLOW_OPEN_API=1."""
    settings = get_state(request).settings
    expected = settings.demo_api_token
    if expected is None:
        if settings.allow_open_api:
            return
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "API token not configured")
    if credentials is None or not hmac.compare_digest(
        credentials.credentials.encode(), expected.encode()
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing or invalid bearer token")
