import os

import pytest
from langchain_tests.integration_tests import RetrieversIntegrationTests

from langchain_contextfetch import ContextFetchRetriever

# These call the live API (1 credit per search; this suite makes 6 searches).
pytestmark = pytest.mark.skipif(
    not os.environ.get("CONTEXTFETCH_API_KEY"), reason="CONTEXTFETCH_API_KEY not set"
)


class TestContextFetchRetriever(RetrieversIntegrationTests):
    @property
    def retriever_constructor(self) -> type[ContextFetchRetriever]:
        return ContextFetchRetriever

    @property
    def retriever_constructor_params(self) -> dict:
        return {"k": 2}

    @property
    def retriever_query_example(self) -> str:
        return "python asyncio tutorial"
