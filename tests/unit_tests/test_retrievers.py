from __future__ import annotations

import pytest
from langchain_core.documents import Document
from pydantic import SecretStr

from langchain_contextfetch import ContextFetchRetriever
from tests.unit_tests.conftest import FakeAPI


def test_invoke_returns_markdown_documents(fake_api: FakeAPI) -> None:
    retriever = ContextFetchRetriever(
        k=2,
        api_key=SecretStr("test-key"),
        exclude_domains=["pinterest.com"],
        start_published_date="2026-01-01",
    )
    docs = retriever.invoke("q")

    assert docs == [
        Document(
            page_content="# Page A\n\nFull Markdown of A.",
            metadata={
                "id": "r1",
                "url": "https://example.com/a",
                "title": "Page A",
                "score": 0.9,
                "published_date": "2026-01-02",
                "author": None,
            },
        ),
        Document(
            page_content="# Page B",
            metadata={
                "id": "r2",
                "url": "https://example.com/b",
                "title": None,
                "score": 0.5,
                "published_date": None,
                "author": None,
            },
        ),
    ]
    assert fake_api.calls == [
        {
            "path": "/v1/search",
            "body": {
                "query": "q",
                "numResults": 2,
                "excludeDomains": ["pinterest.com"],
                "startPublishedDate": "2026-01-01",
                "contents": {"text": True},
            },
            "api_key": "test-key",
        }
    ]


def test_pruned_context_and_k_kwarg(fake_api: FakeAPI) -> None:
    retriever = ContextFetchRetriever(k=5, content="pruned_context")
    docs = retriever.invoke("q", k=1)
    assert [d.page_content for d in docs] == ["Relevant chunk of A."]
    assert fake_api.calls[0]["body"]["numResults"] == 1
    assert fake_api.calls[0]["body"]["contents"] == {"pruned_context": True}


def test_key_from_env(fake_api: FakeAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONTEXTFETCH_API_KEY", "env-key")
    ContextFetchRetriever().invoke("q")
    assert fake_api.calls[0]["api_key"] == "env-key"
    assert fake_api.calls[0]["body"]["numResults"] == 5


async def test_ainvoke(fake_api: FakeAPI) -> None:
    docs = await ContextFetchRetriever(k=1).ainvoke("q")
    assert docs[0].metadata["url"] == "https://example.com/a"
