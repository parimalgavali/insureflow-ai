from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def akb_fixture_pdf() -> Path:
    return FIXTURES / "akb_2015_first2pages.pdf"


class FakeResponse:
    def __init__(self, status_code: int = 200, body: bytes = b"", text: str = ""):
        self.status_code = status_code
        self._body = body
        self.text = text

    def iter_content(self, chunk_size: int = 1 << 16):
        for i in range(0, len(self._body), chunk_size):
            yield self._body[i : i + chunk_size]

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeSession:
    """Maps URL -> FakeResponse (or a list of responses served in order) and records calls."""

    def __init__(self, routes: dict[str, FakeResponse | list[FakeResponse]]):
        self.routes = routes
        self.calls: list[str] = []

    def get(self, url: str, **_: object) -> FakeResponse:
        self.calls.append(url)
        route = self.routes.get(url)
        if route is None:
            return FakeResponse(404)
        if isinstance(route, list):
            return route.pop(0)
        return route
