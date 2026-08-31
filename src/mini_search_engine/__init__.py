"""A small, dependency-free document search engine."""

from mini_search_engine.models import IndexStats, SearchResult
from mini_search_engine.search_engine import SearchEngine
from mini_search_engine.tokenizer import Tokenizer

__all__ = ["IndexStats", "SearchEngine", "SearchResult", "Tokenizer"]
__version__ = "1.0.0"
