# Mini Search Engine

[![CI](https://github.com/mohammmad357/mini-search-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/mohammmad357/mini-search-engine/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A compact, dependency-free document search engine written in Python. It recursively indexes UTF-8
text files, builds a persistent inverted index, and ranks queries with cosine-normalized TF-IDF.
The ranking and indexing algorithms are implemented from scratch—no search framework or machine-
learning package is hiding the interesting parts.

## Why this project exists

Mini Search Engine is a portfolio-sized implementation of real information-retrieval ideas. It is
small enough to read in one sitting, while still demonstrating package design, data structures,
algorithms, persistence, validation, type hints, logging, command-line UX, and automated testing.

## Highlights

- Recursive `.txt` discovery with deterministic document IDs
- Unicode-aware normalization and tokenization
- Inverted index with per-document term frequencies
- Sublinear TF, smoothed IDF, and cosine-similarity ranking
- Atomic, versioned, human-readable JSON persistence
- Ranked terminal output, contextual snippets, and JSON output
- Friendly domain errors and optional debug logging
- Zero third-party runtime dependencies
- Pytest suite and a four-version GitHub Actions matrix

## Quick start

Python 3.10 or newer is required.

```bash
git clone https://github.com/mohammmad357/mini-search-engine.git
cd mini-search-engine
python main.py index ./data/sample_documents
python main.py search "robust nonlinear controller"
```

Example output:

```text
Indexed 8 documents
Vocabulary size: 196 words
Total tokens: 311
Index saved to: .mini-search-index.json

Search: "robust nonlinear controller"

 1. nonlinear_control.txt                  █████            0.282
 2. sliding_mode_control.txt               ████             0.240
 3. robust_control.txt                     ████             0.230

Search completed in 0.001 seconds
```

The exact scores and timings can vary as the sample corpus evolves.

## Installation

The repository-level `main.py` works without installation. To expose the `mini-search` command in
your environment, install the package:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .

mini-search index ./data/sample_documents
mini-search search "feedback stability"
```

For development tools:

```bash
python -m pip install -r requirements-dev.txt
```

## Command-line reference

Build an index (nested directories are included):

```bash
python main.py [--verbose] index PATH [--output INDEX_FILE]
```

Search an index:

```bash
python main.py search QUERY [--index INDEX_FILE] [--limit N] [--json] [--no-snippets]
```

Inspect corpus statistics:

```bash
python main.py stats [--index INDEX_FILE] [--json]
```

The default index path is `.mini-search-index.json`. Queries can be quoted as one argument or
provided as several words. JSON mode is suitable for scripts and integrations.

## How ranking works

During indexing, each term points to the documents containing it and its raw frequency in each
document:

```text
"control" -> {doc_a: 3, doc_b: 1, doc_c: 2}
```

The engine assigns term weights using sublinear term frequency and smoothed inverse document
frequency:

```text
TF(t, d)  = 1 + ln(count(t, d))
IDF(t)    = ln((N + 1) / (DF(t) + 1)) + 1
weight    = TF × IDF
```

It then treats the query and every candidate document as vectors and computes cosine similarity.
This rewards documents that match distinctive query terms while avoiding an automatic advantage
for long documents.

Typical costs, where `T` is the number of indexed tokens and `P` is the combined length of the
query terms' posting lists:

| Operation | Time | Space |
| --- | ---: | ---: |
| Build index | `O(T)` average | `O(T)` worst case |
| Candidate retrieval and scoring | `O(P)` | `O(C)` candidates |
| Persist/load | `O(index size)` | `O(index size)` |

## Project structure

```text
mini-search-engine/
├── .github/workflows/ci.yml
├── data/sample_documents/
├── src/mini_search_engine/
│   ├── cli.py             # argparse commands and output formatting
│   ├── indexer.py         # corpus discovery and inverted-index construction
│   ├── ranking.py         # TF-IDF and cosine similarity
│   ├── search_engine.py   # public orchestration API and snippets
│   ├── storage.py         # atomic, validated JSON persistence
│   ├── tokenizer.py       # Unicode normalization and tokenization
│   └── models.py          # typed dataclasses
├── tests/
├── main.py
└── pyproject.toml
```

## Python API

```python
from mini_search_engine import SearchEngine

engine = SearchEngine.from_directory("data/sample_documents")
engine.save("documents.index.json")

for result in engine.search("robust control", limit=5):
    print(result.path, result.score)
```

## Test and lint

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest --cov=mini_search_engine --cov-report=term-missing
```

## Current scope and roadmap

Version 1 intentionally focuses on plain UTF-8 text and exact normalized terms. Natural next steps
include positional postings for phrase search, BM25 ranking, incremental indexing, field-aware
weights, stemming, and readers for formats such as Markdown and PDF.

## License

Released under the [MIT License](LICENSE).
