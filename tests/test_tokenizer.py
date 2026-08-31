from mini_search_engine.tokenizer import Tokenizer


def test_tokenize_normalizes_case_punctuation_and_underscores() -> None:
    tokenizer = Tokenizer()
    assert tokenizer.tokenize("Hello, HELLO_world!") == ["hello", "hello", "world"]


def test_tokenize_supports_unicode_text() -> None:
    tokenizer = Tokenizer()
    assert tokenizer.tokenize("کنترلِ مقاوم — Café") == ["کنترل", "مقاوم", "café"]


def test_tokenize_filters_short_terms_and_stop_words() -> None:
    tokenizer = Tokenizer.with_stop_words(["the", "AND"], min_token_length=2)
    assert tokenizer.tokenize("a fox and the hound") == ["fox", "hound"]


def test_unique_terms_preserves_first_seen_order() -> None:
    assert Tokenizer().unique_terms("beta alpha beta gamma") == ("beta", "alpha", "gamma")
