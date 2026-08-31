"""Command-line interface for the mini search engine."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from mini_search_engine import __version__
from mini_search_engine.errors import SearchEngineError
from mini_search_engine.search_engine import SearchEngine

DEFAULT_INDEX_PATH = Path(".mini-search-index.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mini-search",
        description="Index and search a directory of UTF-8 text documents.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--verbose", action="store_true", help="show debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    index_parser = subparsers.add_parser("index", help="build an index from text files")
    index_parser.add_argument("directory", type=Path, help="directory to scan recursively")
    index_parser.add_argument(
        "-o", "--output", type=Path, default=DEFAULT_INDEX_PATH, help="index JSON path"
    )

    search_parser = subparsers.add_parser("search", help="search a previously built index")
    search_parser.add_argument("query", nargs="+", help="one or more search terms")
    search_parser.add_argument(
        "-i", "--index", type=Path, default=DEFAULT_INDEX_PATH, help="index JSON path"
    )
    search_parser.add_argument("-n", "--limit", type=_positive_integer, default=10)
    search_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    search_parser.add_argument(
        "--no-snippets", action="store_true", help="do not read source files for snippets"
    )

    stats_parser = subparsers.add_parser("stats", help="show index statistics")
    stats_parser.add_argument(
        "-i", "--index", type=Path, default=DEFAULT_INDEX_PATH, help="index JSON path"
    )
    stats_parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _configure_output_streams()
    parser = build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )
    try:
        if args.command == "index":
            return _index_command(args)
        if args.command == "search":
            return _search_command(args)
        if args.command == "stats":
            return _stats_command(args)
    except SearchEngineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    parser.error(f"Unknown command: {args.command}")
    return 2


def _index_command(args: argparse.Namespace) -> int:
    started_at = time.perf_counter()
    engine = SearchEngine.from_directory(args.directory)
    saved_path = engine.save(args.output)
    elapsed = time.perf_counter() - started_at
    stats = engine.stats
    print(f"Indexed {stats.documents:,} documents")
    print(f"Vocabulary size: {stats.vocabulary_size:,} words")
    print(f"Total tokens: {stats.total_tokens:,}")
    print(f"Index saved to: {saved_path}")
    print(f"Completed in {elapsed:.3f} seconds")
    return 0


def _search_command(args: argparse.Namespace) -> int:
    query = " ".join(args.query)
    engine = SearchEngine.from_index(args.index)
    started_at = time.perf_counter()
    results = engine.search(query, limit=args.limit, include_snippets=not args.no_snippets)
    elapsed = time.perf_counter() - started_at

    if args.json:
        print(
            json.dumps(
                {
                    "query": query,
                    "result_count": len(results),
                    "elapsed_seconds": round(elapsed, 6),
                    "results": [result.to_dict() for result in results],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(f'Search: "{query}"\n')
    if not results:
        print("No results found.")
    for position, result in enumerate(results, start=1):
        bar = "█" * max(1, round(result.score * 16))
        print(f"{position:>2}. {result.path:<38} {bar:<16} {result.score:.3f}")
        if result.snippet:
            print(f"    {result.snippet}")
    print(f"\nSearch completed in {elapsed:.3f} seconds")
    return 0


def _stats_command(args: argparse.Namespace) -> int:
    stats = SearchEngine.from_index(args.index).stats
    if args.json:
        print(json.dumps(stats.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Documents:       {stats.documents:,}")
        print(f"Vocabulary:      {stats.vocabulary_size:,}")
        print(f"Total tokens:    {stats.total_tokens:,}")
        print(f"Source directory: {stats.source_directory}")
        print(f"Created at:       {stats.created_at}")
    return 0


def _positive_integer(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def _configure_output_streams() -> None:
    """Prefer UTF-8 so result bars and multilingual snippets are portable."""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            # Some embedded and test streams cannot be reconfigured.
            continue
