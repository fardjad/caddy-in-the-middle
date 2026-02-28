from __future__ import annotations

import logging
from fnmatch import fnmatch

from mitmproxy import ctx

from .models import MockKey, MockSpec, WildcardMock


def _log_info(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.info(message)
        return
    logging.getLogger(__name__).info(message)


class MockStore:
    def __init__(self) -> None:
        self.exact_matches: dict[MockKey, MockSpec] = {}
        self.wildcard_matches: list[WildcardMock] = []

    def clear(self) -> None:
        self.exact_matches.clear()
        self.wildcard_matches.clear()

    def add_exact(self, method: str, url: str, spec: MockSpec) -> None:
        key = MockKey(method, url)
        self.exact_matches[key] = spec
        _log_info(f"Loaded exact mock: {method} {url}")

    def add_wildcard(self, method: str, pattern: str, spec: MockSpec) -> None:
        self.wildcard_matches.append(WildcardMock(method, pattern, spec))
        _log_info(f"Loaded wildcard mock: {method} ~{pattern}")

    def find_mock(self, method: str, url: str) -> MockSpec | None:
        key = MockKey(method, url)
        if key in self.exact_matches:
            _log_info(f"Exact match found for: {method} {url}")
            return self.exact_matches[key]

        for wildcard in self.wildcard_matches:
            if wildcard.method == method and fnmatch(url, wildcard.pattern):
                _log_info(
                    f"Wildcard match found for: {method} {url} "
                    f"(pattern: {wildcard.pattern})"
                )
                return wildcard.spec

        return None
