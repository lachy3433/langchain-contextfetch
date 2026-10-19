"""LangChain integration for ContextFetch."""

from importlib import metadata

from langchain_contextfetch.retrievers import ContextFetchRetriever
from langchain_contextfetch.tools import ContextFetchSearch

try:
    __version__ = metadata.version(__package__ or "langchain_contextfetch")
except metadata.PackageNotFoundError:
    # Case where package metadata is not available.
    __version__ = ""
del metadata  # optional, avoids polluting the results of dir(__package__)

__all__ = [
    "ContextFetchRetriever",
    "ContextFetchSearch",
    "__version__",
]
