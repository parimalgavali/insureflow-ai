from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


def get_state(request: Request):
    return request.app.state.claimpilot


def require_token(
    request: Request, credentials: HTTPAuthorizationCredentials | None = Depends(bearer)
) -> None:
    """Single demo token from DEMO_API_TOKEN; when unset (local dev) the API is open."""
    expected = get_state(request).settings.demo_api_token
    if expected is None:
        return
    if credentials is None or credentials.credentials != expected:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "missing or invalid bearer token")
