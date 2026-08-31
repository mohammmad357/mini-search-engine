"""TF-IDF weighting and cosine-similarity ranking primitives."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Mapping, Sequence


def inverse_document_frequency(document_count: int, document_frequency: int) -> float:
    """Return smoothed IDF, which remains defined for every valid corpus."""

    return math.log((document_count + 1) / (document_frequency + 1)) + 1.0


def term_frequency_weight(count: int) -> float:
    """Compress raw term counts using sublinear TF scaling."""

    return 0.0 if count <= 0 else 1.0 + math.log(count)


def calculate_document_norms(
    postings: Mapping[str, Mapping[str, int]], document_count: int
) -> dict[str, float]:
    """Pre-compute the Euclidean length of every document TF-IDF vector."""

    squared_norms: dict[str, float] = {}
    for term_postings in postings.values():
        idf = inverse_document_frequency(document_count, len(term_postings))
        for document_id, count in term_postings.items():
            weight = term_frequency_weight(count) * idf
            squared_norms[document_id] = squared_norms.get(document_id, 0.0) + weight**2
    return {document_id: math.sqrt(value) for document_id, value in squared_norms.items()}


def rank_documents(
    query_terms: Sequence[str],
    postings: Mapping[str, Mapping[str, int]],
    document_norms: Mapping[str, float],
    document_count: int,
) -> list[tuple[str, float]]:
    """Rank candidate documents by cosine similarity with the query vector."""

    query_counts = Counter(query_terms)
    query_weights: dict[str, float] = {}
    for term, count in query_counts.items():
        term_postings = postings.get(term)
        if term_postings:
            query_weights[term] = term_frequency_weight(count) * inverse_document_frequency(
                document_count, len(term_postings)
            )

    query_norm = math.sqrt(sum(weight**2 for weight in query_weights.values()))
    if query_norm == 0.0:
        return []

    dot_products: dict[str, float] = {}
    for term, query_weight in query_weights.items():
        term_postings = postings[term]
        idf = inverse_document_frequency(document_count, len(term_postings))
        for document_id, count in term_postings.items():
            document_weight = term_frequency_weight(count) * idf
            dot_products[document_id] = (
                dot_products.get(document_id, 0.0) + query_weight * document_weight
            )

    scores = [
        (document_id, dot_product / (query_norm * document_norms[document_id]))
        for document_id, dot_product in dot_products.items()
        if document_norms.get(document_id, 0.0) > 0.0
    ]
    return sorted(scores, key=lambda item: (-item[1], item[0]))
