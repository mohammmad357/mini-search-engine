from __future__ import annotations

import json
from pathlib import Path

from mini_search_engine.cli import main


def test_cli_index_and_search(document_directory: Path, tmp_path: Path, capsys) -> None:
    index_path = tmp_path / "index.json"
    assert main(["index", str(document_directory), "--output", str(index_path)]) == 0
    assert "Indexed 3 documents" in capsys.readouterr().out

    assert main(["search", "robust", "system", "--index", str(index_path), "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["query"] == "robust system"
    assert payload["results"][0]["path"] == "papers/robust.txt"

    assert main(["search", "control", "--index", str(index_path), "--limit", "1"]) == 0
    human_output = capsys.readouterr().out
    assert 'Search: "control"' in human_output
    assert "█" in human_output


def test_cli_reports_expected_errors(tmp_path: Path, capsys) -> None:
    assert main(["search", "hello", "--index", str(tmp_path / "missing.json")]) == 2
    assert "Run the index command first" in capsys.readouterr().err
