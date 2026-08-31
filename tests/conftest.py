from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def document_directory(tmp_path: Path) -> Path:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "nonlinear.txt").write_text(
        "Nonlinear Control\nA nonlinear control system uses feedback and a robust controller.",
        encoding="utf-8",
    )
    (documents / "python.txt").write_text(
        "Python Data Structures\nPython dictionaries provide efficient key lookup.",
        encoding="utf-8",
    )
    nested = documents / "papers"
    nested.mkdir()
    (nested / "robust.txt").write_text(
        "Robust Control\nRobust control handles uncertainty in a dynamic system.",
        encoding="utf-8",
    )
    return documents
