from pathlib import Path

import pytest

from mini_search_engine.errors import IndexFormatError, QueryError
from mini_search_engine.search_engine import SearchEngine


def test_search_ranks_relevant_document_first(document_directory: Path) -> None:
    engine = SearchEngine.from_directory(document_directory)
    results = engine.search("nonlinear controller")
    assert results[0].path == "nonlinear.txt"
    assert results[0].score > 0
    assert set(results[0].matched_terms) == {"nonlinear", "controller"}
    assert "[nonlinear]" in results[0].snippet.casefold()


def test_search_honors_limit(document_directory: Path) -> None:
    results = SearchEngine.from_directory(document_directory).search("control system", limit=1)
    assert len(results) == 1


def test_search_returns_empty_for_unknown_term(document_directory: Path) -> None:
    assert SearchEngine.from_directory(document_directory).search("astronomy") == []


def test_search_rejects_empty_query(document_directory: Path) -> None:
    with pytest.raises(QueryError, match="searchable term"):
        SearchEngine.from_directory(document_directory).search("a !")


def test_index_round_trip(document_directory: Path, tmp_path: Path) -> None:
    index_path = tmp_path / "index.json"
    original = SearchEngine.from_directory(document_directory)
    original.save(index_path)
    loaded = SearchEngine.from_index(index_path)
    assert loaded.stats.documents == original.stats.documents
    assert loaded.search("robust system")[0].path == "papers/robust.txt"


def test_loading_missing_index_has_helpful_error(tmp_path: Path) -> None:
    with pytest.raises(IndexFormatError, match="Run the index command first"):
        SearchEngine.from_index(tmp_path / "missing.json")
