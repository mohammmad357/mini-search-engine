import pytest

from mini_search_engine.ranking import (
    inverse_document_frequency,
    rank_documents,
    term_frequency_weight,
)


def test_tf_weight_is_sublinear() -> None:
    assert term_frequency_weight(0) == 0
    assert term_frequency_weight(4) < 4


def test_idf_is_larger_for_rare_terms() -> None:
    assert inverse_document_frequency(10, 1) > inverse_document_frequency(10, 8)


def test_rank_documents_returns_empty_for_unknown_terms() -> None:
    assert rank_documents(["missing"], {}, {}, 3) == []


def test_rank_documents_prefers_better_cosine_match() -> None:
    postings = {"alpha": {"one": 3, "two": 1}, "beta": {"two": 4}}
    norms = {"one": 2.0, "two": 5.0}
    ranked = rank_documents(["alpha"], postings, norms, 2)
    assert ranked[0][0] == "one"
    assert ranked[0][1] == pytest.approx(term_frequency_weight(3) / 2.0)
