from __future__ import annotations

from fastapi import APIRouter, Depends

from api.security import get_state

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(state=Depends(get_state)) -> dict:
    return state.health()
