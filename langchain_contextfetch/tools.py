"""ContextFetch tools."""

from __future__ import annotations

from typing import Literal

from contextfetch import ContextFetchError, SearchResponse
from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool, ToolException
from langchain_core.utils import secret_from_env
from pydantic import BaseModel, Field, SecretStr

from langchain_contextfetch._utilities import Content, page_content, search


class ContextFetchSearchInput(BaseModel):
    """Input schema for the ContextFetch search tool.

    The Field descriptions are sent to the model when performing tool calling.
    """

    query: str = Field(description="The web search query.")
    include_domains: list[str] | None = Field(
        default=None, description="Only return results from these domains."
    )
    exclude_domains: list[str] | None = Field(
        default=None, description="Never return results from these domains."
    )
    start_published_date: str | None = Field(
        default=None,
        description="Only return pages published on or after this date (YYYY-MM-DD).",
    )


class ContextFetchSearch(BaseTool):  # type: ignore[override]
    """ContextFetch web search tool.

    Setup:
        Install `langchain-contextfetch` and set the environment variable
        `CONTEXTFETCH_API_KEY`. Without a key, requests use the keyless tier.

        ```bash
        pip install -U langchain-contextfetch
        export CONTEXTFETCH_API_KEY="your-api-key"
        ```

    Instantiation:
        ```python
        from langchain_contextfetch import ContextFetchSearch

        tool = ContextFetchSearch(num_results=3)
        ```

    Invocation with args:
        ```python
        tool.invoke({"query": "pgvector HNSW index parameters"})
        ```

    Invocation with ToolCall:
        ```python
        tool.invoke(
            {
                "args": {"query": "pgvector HNSW index parameters"},
                "id": "1",
                "name": tool.name,
                "type": "tool_call",
            }
        )
        ```

        Returns a `ToolMessage` whose `content` lists each result's title, URL,
        published date and page content, and whose `artifact` is the raw API
        response (a dict with `results`).
    """

    name: str = "contextfetch_search"
    """The name that is passed to the model when performing tool calling."""
    description: str = (
        "Search the web. Returns the top results, each with its title, URL, "
        "published date and page content as Markdown."
    )
    """The description that is passed to the model when performing tool calling."""
    args_schema: type[BaseModel] = ContextFetchSearchInput
    """The schema that is passed to the model when performing tool calling."""
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    num_results: int = Field(default=5, ge=1, le=25)
    """Number of results per search (1 to 25)."""
    content: Content = "pruned_context"
    """`"pruned_context"` (query-relevant chunks of each page, the default) or
    `"text"` (whole page as Markdown)."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("CONTEXTFETCH_API_KEY", default=None)
    )
    """ContextFetch API key. Defaults to the `CONTEXTFETCH_API_KEY` env var."""

    # Async: BaseTool runs this method in a thread executor, since the
    # contextfetch SDK is synchronous (stdlib urllib).
    def _run(
        self,
        query: str,
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        start_published_date: str | None = None,
        *,
        run_manager: CallbackManagerForToolRun | None = None,
    ) -> tuple[str, SearchResponse]:
        try:
            response = search(
                self.api_key,
                query,
                num_results=self.num_results,
                content=self.content,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                start_published_date=start_published_date,
            )
        except ContextFetchError as e:
            # Raised as ToolException so handle_tool_error can pass it to the model.
            raise ToolException(str(e)) from e
        results = response.get("results", [])
        if not results:
            return "No results found.", response
        content = "\n\n---\n\n".join(
            f"Title: {r.get('title') or ''}\n"
            f"URL: {r.get('url', '')}\n"
            f"Published: {r.get('publishedDate') or 'unknown'}\n\n"
            f"{page_content(r, self.content)}"
            for r in results
        )
        return content, response
