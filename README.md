# langchain-contextfetch

This package contains the LangChain integration with [ContextFetch](https://contextfetch.dev), a web search API that returns pages as Markdown.

- `ContextFetchRetriever`: a retriever that returns search results as `Document`s.
- `ContextFetchSearch`: a search tool for agents and tool-calling models.

## Installation

```bash
pip install -U langchain-contextfetch
```

Requires Python 3.10 or later.

## Credentials

Set your API key in the `CONTEXTFETCH_API_KEY` environment variable, or pass `api_key=` to either class:

```bash
export CONTEXTFETCH_API_KEY="your-api-key"
```

Without a key, requests use ContextFetch's keyless tier, which has a small daily allowance per IP address. See the [API reference](https://contextfetch.dev/docs/reference) for keys and credits.

## Retriever

```python
from langchain_contextfetch import ContextFetchRetriever

retriever = ContextFetchRetriever(k=3)
docs = retriever.invoke("pgvector HNSW index parameters")

for doc in docs:
    print(doc.metadata["url"], doc.metadata["title"])
```

Each `Document` has:

- `page_content`: the page as Markdown (`content="text"`, the default), or only the chunks of the page relevant to the query (`content="pruned_context"`).
- `metadata`: `id`, `url`, `title`, `score`, `published_date` and `author`. Fields the API does not return are `None`.

Options:

| Parameter | Default | Description |
| --- | --- | --- |
| `k` | `5` | Number of results (1 to 25). Can also be passed per call: `retriever.invoke(query, k=10)`. |
| `content` | `"text"` | `"text"` or `"pruned_context"`. |
| `include_domains` | `None` | Only return results from these domains. |
| `exclude_domains` | `None` | Never return results from these domains. |
| `start_published_date` | `None` | Only return pages published on or after this date (`YYYY-MM-DD`). |
| `api_key` | `CONTEXTFETCH_API_KEY` | API key. |

## Search tool

```python
from langchain_contextfetch import ContextFetchSearch

tool = ContextFetchSearch(num_results=3)
tool.invoke({"query": "pgvector HNSW index parameters"})
```

The model can set `query`, `include_domains`, `exclude_domains` and `start_published_date`. `num_results` (default 5, maximum 25), `content` and `api_key` are set when the tool is created. The tool's default `content` is `"pruned_context"`, so each result contributes only its query-relevant chunks to the model's context; use `content="text"` for whole pages.

The tool uses `response_format="content_and_artifact"`. Called with plain args as above, it returns the content string: each result's title, URL, published date and content. Called with a `ToolCall`, it returns a `ToolMessage` with that `content` and the raw API response as its `artifact`.

```python
msg = tool.invoke(
    {
        "args": {"query": "pgvector HNSW index parameters"},
        "id": "1",
        "name": tool.name,
        "type": "tool_call",
    }
)
msg.artifact["results"][0]["url"]
```

API errors (for example HTTP 402 when credits run out) are raised as `ToolException`. To pass the error message to the model instead, create the tool with `handle_tool_error=True`.

### Use in an agent

```python
from langchain.agents import create_agent

agent = create_agent(model="claude-sonnet-4-6", tools=[tool])
agent.invoke({"messages": [{"role": "user", "content": "What changed in Python 3.14?"}]})
```

## Async

Both classes support `ainvoke`. The underlying `contextfetch` SDK is synchronous, so async calls run in a thread executor (LangChain's default for tools and retrievers).

## Development

```bash
make test               # unit tests, network disabled
make integration_test   # live API tests; skipped unless CONTEXTFETCH_API_KEY is set
make lint
```

The unit tests include LangChain's standard `ToolsUnitTests`. The integration tests run the standard `ToolsIntegrationTests` and `RetrieversIntegrationTests` suites, which make 10 searches in total.
