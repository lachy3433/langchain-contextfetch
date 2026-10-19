"""ContextFetch retrievers."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.utils import secret_from_env
from pydantic import Field, SecretStr

from langchain_contextfetch._utilities import Content, metadata, page_content, search


class ContextFetchRetriever(BaseRetriever):
    """ContextFetch web search retriever.

    Setup:
        Install `langchain-contextfetch` and set the environment variable
        `CONTEXTFETCH_API_KEY`. Without a key, requests use the keyless tier.

        ```bash
        pip install -U langchain-contextfetch
        export CONTEXTFETCH_API_KEY="your-api-key"
        ```

    Key init args:
        k: int
            Number of results to return (1 to 25). Default 5.
        content: "text" | "pruned_context"
            `"text"` uses the whole page as Markdown; `"pruned_context"` uses only
            the chunks of the page relevant to the query. Default `"text"`.
        include_domains: list[str] | None
            Only return results from these domains.
        exclude_domains: list[str] | None
            Never return results from these domains.
        start_published_date: str | None
            Only return pages published on or after this ISO date.
        api_key: SecretStr | None
            ContextFetch API key. Defaults to `CONTEXTFETCH_API_KEY`.

    Instantiate:
        ```python
        from langchain_contextfetch import ContextFetchRetriever

        retriever = ContextFetchRetriever(k=3)
        ```

    Usage:
        ```python
        docs = retriever.invoke("pgvector HNSW index parameters")
        docs[0].metadata["url"]
        ```

    Use within a chain:
        ```python
        from langchain_core.output_parsers import StrOutputParser
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.runnables import RunnablePassthrough
        from langchain_anthropic import ChatAnthropic

        prompt = ChatPromptTemplate.from_template(
            \"\"\"Answer the question based only on the context provided.

        Context: {context}

        Question: {question}\"\"\"
        )

        model = ChatAnthropic(model="claude-sonnet-4-6")


        def format_docs(docs):
            return "\\n\\n".join(doc.page_content for doc in docs)


        chain = (
            {"context": retriever | format_docs, "question": RunnablePassthrough()}
            | prompt
            | model
            | StrOutputParser()
        )

        chain.invoke("How do I tune HNSW in pgvector?")
        ```
    """

    k: int = Field(default=5, ge=1, le=25)
    """Number of results to return (1 to 25)."""
    content: Content = "text"
    """`"text"` (whole page as Markdown, the default) or `"pruned_context"`
    (query-relevant chunks of each page)."""
    include_domains: list[str] | None = None
    """Only return results from these domains."""
    exclude_domains: list[str] | None = None
    """Never return results from these domains."""
    start_published_date: str | None = None
    """Only return pages published on or after this ISO date (YYYY-MM-DD)."""
    api_key: SecretStr | None = Field(
        default_factory=secret_from_env("CONTEXTFETCH_API_KEY", default=None)
    )
    """ContextFetch API key. Defaults to the `CONTEXTFETCH_API_KEY` env var."""

    # Async: BaseRetriever runs this method in a thread executor, since the
    # contextfetch SDK is synchronous (stdlib urllib).
    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun, **kwargs: Any
    ) -> list[Document]:
        response = search(
            self.api_key,
            query,
            num_results=kwargs.get("k", self.k),
            content=self.content,
            include_domains=self.include_domains,
            exclude_domains=self.exclude_domains,
            start_published_date=self.start_published_date,
        )
        return [
            Document(page_content=page_content(r, self.content), metadata=metadata(r))
            for r in response.get("results", [])
        ]
