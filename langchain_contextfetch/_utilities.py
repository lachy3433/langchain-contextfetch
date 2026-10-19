"""Helpers shared by the retriever and the tool."""

from __future__ import annotations

from typing import Any, Literal

from contextfetch import ContextFetch, Result, SearchResponse
from pydantic import SecretStr

Content = Literal["text", "pruned_context"]
"""Which result content to use: the whole page as Markdown, or only the chunks
relevant to the query."""

_RESULT_KEY = {"text": "text", "pruned_context": "prunedContext"}


def search(
    api_key: SecretStr | None,
    query: str,
    *,
    num_results: int,
    content: Content,
    include_domains: list[str] | None = None,
    exclude_domains: list[str] | None = None,
    start_published_date: str | None = None,
) -> SearchResponse:
    """Run one search, asking the API only for the content that will be used."""
    # ContextFetch() falls back to CONTEXTFETCH_API_KEY, then to the keyless tier.
    client = ContextFetch(api_key.get_secret_value() if api_key else None)
    return client.search(
        query,
        num_results=num_results,
        include_domains=include_domains,
        exclude_domains=exclude_domains,
        start_published_date=start_published_date,
        text=content == "text",
        pruned_context=content == "pruned_context",
    )


def page_content(result: Result, content: Content) -> str:
    """The text of a result for the chosen content type."""
    return result.get(_RESULT_KEY[content]) or ""  # type: ignore[return-value]


def metadata(result: Result) -> dict[str, Any]:
    """Result fields other than the page content."""
    return {
        "id": result.get("id"),
        "url": result.get("url"),
        "title": result.get("title"),
        "score": result.get("score"),
        "published_date": result.get("publishedDate"),
        "author": result.get("author"),
    }
