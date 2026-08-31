"""Data models shared across indexing, persistence, and search."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Document:
    """Metadata for one indexed text document."""

    document_id: str
    path: str
    title: str
    token_count: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SearchResult:
    """One ranked result returned for a query."""

    path: str
    title: str
    score: float
    matched_terms: tuple[str, ...]
    snippet: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "score": round(self.score, 6),
            "matched_terms": list(self.matched_terms),
            "snippet": self.snippet,
        }


@dataclass(frozen=True, slots=True)
class IndexStats:
    """Summary information about a built index."""

    documents: int
    vocabulary_size: int
    total_tokens: int
    source_directory: str
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class IndexSnapshot:
    """Complete in-memory representation of a persisted index."""

    source_directory: str
    created_at: str
    documents: dict[str, Document]
    postings: dict[str, dict[str, int]]
    document_norms: dict[str, float]

    @property
    def stats(self) -> IndexStats:
        return IndexStats(
            documents=len(self.documents),
            vocabulary_size=len(self.postings),
            total_tokens=sum(document.token_count for document in self.documents.values()),
            source_directory=self.source_directory,
            created_at=self.created_at,
        )
