"""Domain-specific exceptions exposed by the search engine."""


class SearchEngineError(Exception):
    """Base exception for expected application errors."""


class IndexBuildError(SearchEngineError):
    """Raised when a document collection cannot be indexed."""


class IndexFormatError(SearchEngineError):
    """Raised when a persisted index is missing, corrupt, or incompatible."""


class QueryError(SearchEngineError):
    """Raised when a search query cannot be processed."""
