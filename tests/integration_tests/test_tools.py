import os

import pytest
from langchain_tests.integration_tests import ToolsIntegrationTests

from langchain_contextfetch import ContextFetchSearch

# These call the live API (1 credit per search; this suite makes 4 searches).
pytestmark = pytest.mark.skipif(
    not os.environ.get("CONTEXTFETCH_API_KEY"), reason="CONTEXTFETCH_API_KEY not set"
)


class TestContextFetchSearch(ToolsIntegrationTests):
    @property
    def tool_constructor(self) -> type[ContextFetchSearch]:
        return ContextFetchSearch

    @property
    def tool_constructor_params(self) -> dict:
        return {"num_results": 2}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "python asyncio tutorial"}
