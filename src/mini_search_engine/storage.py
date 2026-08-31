"""Versioned and validated JSON persistence for search indexes."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from mini_search_engine.errors import IndexFormatError
from mini_search_engine.models import Document, IndexSnapshot

SCHEMA_VERSION = 1


def save_index(snapshot: IndexSnapshot, destination: str | Path) -> Path:
    """Atomically serialize *snapshot* to a human-readable JSON file."""

    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source_directory": snapshot.source_directory,
        "created_at": snapshot.created_at,
        "documents": {
            document_id: document.to_dict()
            for document_id, document in sorted(snapshot.documents.items())
        },
        "postings": {
            term: dict(sorted(term_postings.items()))
            for term, term_postings in sorted(snapshot.postings.items())
        },
        "document_norms": dict(sorted(snapshot.document_norms.items())),
    }

    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_name = temporary_file.name
            json.dump(payload, temporary_file, ensure_ascii=False, indent=2)
            temporary_file.write("\n")
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.replace(temporary_name, path)
    except OSError as exc:
        if temporary_name:
            Path(temporary_name).unlink(missing_ok=True)
        raise IndexFormatError(f"Could not save index to '{path}': {exc}") from exc
    return path


def load_index(source: str | Path) -> IndexSnapshot:
    """Load and validate a JSON index from disk."""

    path = Path(source).expanduser().resolve()
    if not path.is_file():
        raise IndexFormatError(f"Index file does not exist: {path}. Run the index command first.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IndexFormatError(f"Could not read index '{path}': {exc}") from exc

    try:
        _validate_payload(payload)
        documents = {
            document_id: Document(**document_data)
            for document_id, document_data in payload["documents"].items()
        }
        postings = {
            str(term): {str(document_id): int(count) for document_id, count in values.items()}
            for term, values in payload["postings"].items()
        }
        norms = {
            str(document_id): float(value)
            for document_id, value in payload["document_norms"].items()
        }
    except (KeyError, TypeError, ValueError) as exc:
        raise IndexFormatError(f"Index '{path}' contains invalid data: {exc}") from exc

    unknown_ids = {
        document_id
        for term_postings in postings.values()
        for document_id in term_postings
        if document_id not in documents
    }
    if unknown_ids:
        raise IndexFormatError(f"Index '{path}' contains postings for unknown documents")

    return IndexSnapshot(
        source_directory=payload["source_directory"],
        created_at=payload["created_at"],
        documents=documents,
        postings=postings,
        document_norms=norms,
    )


def _validate_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise IndexFormatError("Index root must be a JSON object")
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise IndexFormatError(
            f"Unsupported index schema version: {payload.get('schema_version')!r}; "
            f"expected {SCHEMA_VERSION}"
        )
    expected_types = {
        "source_directory": str,
        "created_at": str,
        "documents": dict,
        "postings": dict,
        "document_norms": dict,
    }
    for field, expected_type in expected_types.items():
        if not isinstance(payload.get(field), expected_type):
            raise IndexFormatError(f"Index field '{field}' must be {expected_type.__name__}")
