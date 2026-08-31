"""Build an inverted index from a directory of UTF-8 text files."""

from __future__ import annotations

import hashlib
import logging
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from mini_search_engine.errors import IndexBuildError
from mini_search_engine.models import Document, IndexSnapshot
from mini_search_engine.ranking import calculate_document_norms
from mini_search_engine.tokenizer import Tokenizer

LOGGER = logging.getLogger(__name__)


class Indexer:
    """Discover documents and construct an in-memory inverted index."""

    def __init__(self, tokenizer: Tokenizer | None = None) -> None:
        self.tokenizer = tokenizer or Tokenizer()

    def build(self, directory: str | Path) -> IndexSnapshot:
        """Recursively index all ``.txt`` files under *directory*."""

        root = Path(directory).expanduser().resolve()
        if not root.exists():
            raise IndexBuildError(f"Document directory does not exist: {root}")
        if not root.is_dir():
            raise IndexBuildError(f"Document path is not a directory: {root}")

        paths = sorted(
            (path for path in root.rglob("*.txt") if path.is_file()),
            key=lambda path: path.relative_to(root).as_posix().casefold(),
        )
        if not paths:
            raise IndexBuildError(f"No .txt documents found under: {root}")

        documents: dict[str, Document] = {}
        postings: dict[str, dict[str, int]] = {}

        for path in paths:
            relative_path = path.relative_to(root).as_posix()
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise IndexBuildError(f"Could not read UTF-8 document '{path}': {exc}") from exc

            terms = self.tokenizer.tokenize(text)
            document_id = self._document_id(relative_path)
            documents[document_id] = Document(
                document_id=document_id,
                path=relative_path,
                title=self._extract_title(text, path.stem),
                token_count=len(terms),
            )
            for term, count in Counter(terms).items():
                postings.setdefault(term, {})[document_id] = count

            LOGGER.debug("Indexed %s (%d tokens)", relative_path, len(terms))

        norms = calculate_document_norms(postings, len(documents))
        # Empty files have zero-length vectors but remain part of corpus statistics.
        for document_id in documents:
            norms.setdefault(document_id, 0.0)

        return IndexSnapshot(
            source_directory=str(root),
            created_at=datetime.now(timezone.utc).isoformat(),
            documents=documents,
            postings=postings,
            document_norms=norms,
        )

    @staticmethod
    def _document_id(relative_path: str) -> str:
        return hashlib.sha256(relative_path.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _extract_title(text: str, fallback: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), fallback)
        title = first_line.removeprefix("#").strip()
        return title[:120] or fallback
