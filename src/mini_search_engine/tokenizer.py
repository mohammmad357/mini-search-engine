"""Unicode-aware text normalization and tokenization."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field

# ``[^\W_]`` means any Unicode alphanumeric character except underscore.
_TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)?", flags=re.UNICODE)


@dataclass(frozen=True, slots=True)
class Tokenizer:
    """Normalize text and split it into deterministic searchable terms."""

    min_token_length: int = 2
    stop_words: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        if self.min_token_length < 1:
            raise ValueError("min_token_length must be at least 1")

    @staticmethod
    def normalize(text: str) -> str:
        """Apply compatibility normalization and language-aware lowercasing."""

        return unicodedata.normalize("NFKC", text).casefold()

    def tokenize(self, text: str) -> list[str]:
        """Return normalized terms, preserving their original order."""

        normalized = self.normalize(text.replace("_", " "))
        return [
            token
            for token in _TOKEN_PATTERN.findall(normalized)
            if len(token) >= self.min_token_length and token not in self.stop_words
        ]

    def unique_terms(self, text: str) -> tuple[str, ...]:
        """Return unique query terms in first-seen order."""

        return tuple(dict.fromkeys(self.tokenize(text)))

    @classmethod
    def with_stop_words(cls, stop_words: Iterable[str], *, min_token_length: int = 2) -> Tokenizer:
        """Build a tokenizer with a normalized custom stop-word collection."""

        normalized = frozenset(cls.normalize(word) for word in stop_words)
        return cls(min_token_length=min_token_length, stop_words=normalized)
