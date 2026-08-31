"""High-level API for building, loading, saving, and querying indexes."""

from __future__ import annotations

import re
from pathlib import Path

from mini_search_engine.errors import QueryError
from mini_search_engine.indexer import Indexer
from mini_search_engine.models import IndexSnapshot, IndexStats, SearchResult
from mini_search_engine.ranking import rank_documents
from mini_search_engine.storage import load_index, save_index
from mini_search_engine.tokenizer import Tokenizer


class SearchEngine:
    """Coordinate indexing, persistence, and ranked retrieval."""

    def __init__(self, snapshot: IndexSnapshot, tokenizer: Tokenizer | None = None) -> None:
        self.snapshot = snapshot
        self.tokenizer = tokenizer or Tokenizer()

    @classmethod
    def from_directory(
        cls, directory: str | Path, tokenizer: Tokenizer | None = None
    ) -> SearchEngine:
        """Build a fresh engine from a document directory."""

        selected_tokenizer = tokenizer or Tokenizer()
        return cls(Indexer(selected_tokenizer).build(directory), selected_tokenizer)

    @classmethod
    def from_index(cls, path: str | Path, tokenizer: Tokenizer | None = None) -> SearchEngine:
        """Load an engine from a persisted index."""

        return cls(load_index(path), tokenizer)

    @property
    def stats(self) -> IndexStats:
        return self.snapshot.stats

    def save(self, destination: str | Path) -> Path:
        return save_index(self.snapshot, destination)

    def search(
        self, query: str, *, limit: int = 10, include_snippets: bool = True
    ) -> list[SearchResult]:
        """Return the top documents for *query*, ordered by cosine similarity."""

        if limit < 1:
            raise QueryError("Result limit must be at least 1")
        query_terms = self.tokenizer.tokenize(query)
        if not query_terms:
            raise QueryError("Query must contain at least one searchable term")

        ranked = rank_documents(
            query_terms,
            self.snapshot.postings,
            self.snapshot.document_norms,
            len(self.snapshot.documents),
        )
        unique_query_terms = tuple(dict.fromkeys(query_terms))
        results: list[SearchResult] = []
        for document_id, score in ranked[:limit]:
            document = self.snapshot.documents[document_id]
            matched_terms = tuple(
                term
                for term in unique_query_terms
                if document_id in self.snapshot.postings.get(term, {})
            )
            snippet = self._make_snippet(document.path, matched_terms) if include_snippets else None
            results.append(
                SearchResult(
                    path=document.path,
                    title=document.title,
                    score=score,
                    matched_terms=matched_terms,
                    snippet=snippet,
                )
            )
        return results

    def _make_snippet(
        self, relative_path: str, terms: tuple[str, ...], width: int = 180
    ) -> str | None:
        path = Path(self.snapshot.source_directory) / relative_path
        try:
            text = " ".join(path.read_text(encoding="utf-8").split())
        except (OSError, UnicodeError):
            return None
        if not text:
            return None

        normalized = self.tokenizer.normalize(text)
        positions = [normalized.find(term) for term in terms]
        first_match = min((position for position in positions if position >= 0), default=0)
        start = max(0, first_match - width // 3)
        end = min(len(text), start + width)
        snippet = text[start:end].strip()
        if start > 0:
            snippet = f"…{snippet}"
        if end < len(text):
            snippet = f"{snippet}…"
        for term in sorted(terms, key=len, reverse=True):
            snippet = re.sub(
                re.escape(term),
                lambda match: f"[{match.group(0)}]",
                snippet,
                flags=re.IGNORECASE,
            )
        return snippet
