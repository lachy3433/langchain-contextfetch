from __future__ import annotations

import pytest
from contextfetch import PaymentRequiredError
from langchain_core.messages import ToolMessage
from langchain_core.tools import ToolException
from langchain_tests.unit_tests import ToolsUnitTests
from pydantic import SecretStr

from langchain_contextfetch import ContextFetchSearch
from tests.unit_tests.conftest import FakeAPI


class TestContextFetchSearchStandard(ToolsUnitTests):
    @property
    def tool_constructor(self) -> type[ContextFetchSearch]:
        return ContextFetchSearch

    @property
    def tool_constructor_params(self) -> dict:
        return {"api_key": "test-key"}

    @property
    def tool_invoke_params_example(self) -> dict:
        return {"query": "pgvector HNSW index parameters"}

    @property
    def init_from_env_params(self) -> tuple[dict, dict, dict]:
        return {"CONTEXTFETCH_API_KEY": "env-key"}, {}, {"api_key": "env-key"}


def _tool_call(args: dict) -> dict:
    return {"args": args, "id": "1", "name": "contextfetch_search", "type": "tool_call"}


def test_tool_call_returns_content_and_artifact(fake_api: FakeAPI) -> None:
    tool = ContextFetchSearch(num_results=2, api_key=SecretStr("test-key"))
    msg = tool.invoke(_tool_call({"query": "q", "include_domains": ["example.com"]}))

    assert isinstance(msg, ToolMessage)
    assert "URL: https://example.com/a" in msg.content
    assert "Relevant chunk of A." in msg.content  # pruned_context is the default
    assert "Full Markdown of A." not in msg.content
    assert "Published: unknown" in msg.content  # result b has no publishedDate
    assert msg.artifact["results"][0]["id"] == "r1"
    assert fake_api.calls == [
        {
            "path": "/v1/search",
            "body": {
                "query": "q",
                "numResults": 2,
                "includeDomains": ["example.com"],
                "contents": {"pruned_context": True},
            },
            "api_key": "test-key",
        }
    ]


def test_text_content(fake_api: FakeAPI) -> None:
    tool = ContextFetchSearch(content="text")
    msg = tool.invoke(_tool_call({"query": "q"}))
    assert "Full Markdown of A." in msg.content
    assert fake_api.calls[0]["body"]["contents"] == {"text": True}
    assert fake_api.calls[0]["api_key"] is None  # keyless tier


def test_no_results(fake_api: FakeAPI) -> None:
    fake_api.results = []
    msg = ContextFetchSearch().invoke(_tool_call({"query": "q"}))
    assert msg.content == "No results found."
    assert msg.artifact == {"requestId": "req", "results": []}


def test_api_error_is_tool_exception(fake_api: FakeAPI) -> None:
    fake_api.error = PaymentRequiredError("HTTP 402 Buy credits.", status=402)
    with pytest.raises(ToolException, match="Buy credits"):
        ContextFetchSearch().invoke({"query": "q"})

    tool = ContextFetchSearch(handle_tool_error=True)
    msg = tool.invoke(_tool_call({"query": "q"}))
    assert msg.status == "error"
    assert "Buy credits" in msg.content


async def test_async_invoke(fake_api: FakeAPI) -> None:
    msg = await ContextFetchSearch().ainvoke(_tool_call({"query": "q"}))
    assert "Page A" in msg.content


def test_api_key_is_secret() -> None:
    tool = ContextFetchSearch(api_key="test-key")  # type: ignore[arg-type]
    assert tool.api_key == SecretStr("test-key")
    assert "test-key" not in repr(tool)
