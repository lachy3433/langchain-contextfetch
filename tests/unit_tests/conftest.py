"""Unit test fixtures: a fake ContextFetch transport, so no test touches the network."""

from __future__ import annotations

import json
from typing import Any

import pytest
from contextfetch import ContextFetch

RESULTS: list[dict[str, Any]] = [
    {
        "id": "r1",
        "url": "https://example.com/a",
        "title": "Page A",
        "score": 0.9,
        "publishedDate": "2026-01-02",
        "text": "# Page A\n\nFull Markdown of A.",
        "prunedContext": "Relevant chunk of A.",
    },
    {
        "id": "r2",
        "url": "https://example.com/b",
        "title": None,
        "score": 0.5,
        "text": "# Page B",
        "prunedContext": "Relevant chunk of B.",
    },
]


class FakeAPI:
    """Records each request body and answers with RESULTS (or raises `error`)."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.results: list[dict[str, Any]] = RESULTS
        self.error: Exception | None = None

    def request(
        self, client: ContextFetch, method: str, path: str, body: Any = None, **_: Any
    ) -> tuple[bytes, dict]:
        self.calls.append({"path": path, "body": body, "api_key": client.api_key})
        if self.error:
            raise self.error
        response = {"requestId": "req", "results": self.results[: body["numResults"]]}
        return json.dumps(response).encode(), {}


@pytest.fixture
def fake_api(monkeypatch: pytest.MonkeyPatch) -> FakeAPI:
    api = FakeAPI()
    monkeypatch.delenv("CONTEXTFETCH_API_KEY", raising=False)
    # Patch only the SDK's HTTP call, so its request building and parsing still run.
    monkeypatch.setattr(
        ContextFetch, "_request", lambda self, *a, **k: api.request(self, *a, **k)
    )
    return api
