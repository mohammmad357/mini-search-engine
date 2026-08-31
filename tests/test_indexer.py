from pathlib import Path

import pytest

from mini_search_engine.errors import IndexBuildError
from mini_search_engine.indexer import Indexer


def test_build_indexes_nested_text_files(document_directory: Path) -> None:
    snapshot = Indexer().build(document_directory)
    assert snapshot.stats.documents == 3
    assert snapshot.stats.total_tokens > 0
    assert len(snapshot.postings["control"]) == 2
    assert {document.path for document in snapshot.documents.values()} == {
        "nonlinear.txt",
        "python.txt",
        "papers/robust.txt",
    }


def test_build_ignores_non_text_files(document_directory: Path) -> None:
    (document_directory / "ignored.md").write_text("control", encoding="utf-8")
    assert Indexer().build(document_directory).stats.documents == 3


def test_build_fails_for_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(IndexBuildError, match="No .txt documents"):
        Indexer().build(tmp_path)


def test_document_ids_are_stable(document_directory: Path) -> None:
    first = Indexer().build(document_directory)
    second = Indexer().build(document_directory)
    assert first.documents.keys() == second.documents.keys()
