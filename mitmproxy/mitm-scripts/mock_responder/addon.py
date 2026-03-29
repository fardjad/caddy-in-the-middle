from __future__ import annotations

import logging
import os
from pathlib import Path

from mitmproxy import ctx, http

from .models import MockSpec
from .parser import MockFileParser
from .protocol import normalize_response_headers
from .rendering import fetch_external, render_and_extract_body, should_fetch_external
from .store import MockStore


def _log_info(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.info(message)
        return
    logging.getLogger(__name__).info(message)


def _log_warn(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.warn(message)
        return
    logging.getLogger(__name__).warning(message)


class MockResponder:
    def __init__(self) -> None:
        self.mock_patterns = self._get_mock_patterns()
        self.enabled = len(self.mock_patterns) > 0
        self.store = MockStore()

        if not self.enabled:
            _log_info("MockResponder disabled: MOCK_PATHS environment variable not set")

    @staticmethod
    def _get_mock_patterns() -> list[str]:
        mock_paths_env = os.environ.get("MOCK_PATHS")
        if not mock_paths_env:
            return []

        patterns = [part.strip() for part in mock_paths_env.split(",") if part.strip()]
        _log_info(f"Mock patterns configured: {patterns}")
        return patterns

    def load(self, loader) -> None:
        if self.enabled:
            self._load_mocks()

    def request(self, flow: http.HTTPFlow) -> None:
        if not self.enabled:
            return

        self._load_mocks()

        method = flow.request.method.upper()
        url = flow.request.url
        _log_info(f"Checking for mock: {method} {url}")

        spec = self.store.find_mock(method, url)
        if spec is None:
            return

        status, headers, body = self._build_response(spec, flow)
        _log_info(f"Serving mock response: {method} {url} -> {status}")
        flow.response = http.Response.make(status, body, headers)

    def _load_mocks(self) -> None:
        self.store.clear()
        all_mock_files: list[Path] = []

        for pattern in self.mock_patterns:
            all_mock_files.extend(self._find_files_by_pattern(pattern))

        if not all_mock_files:
            _log_info(f"No mock files found matching patterns: {self.mock_patterns}")
            return

        _log_info(f"Found {len(all_mock_files)} mock file(s)")
        for path in sorted(all_mock_files):
            self._load_mock_file(path)

    @staticmethod
    def _find_files_by_pattern(pattern: str) -> list[Path]:
        if pattern.startswith("/"):
            base_path = Path("/")
            relative_pattern = pattern[1:]
        else:
            base_path = Path.cwd()
            relative_pattern = pattern

        try:
            if "**" in relative_pattern:
                prefix, suffix = relative_pattern.split("**", 1)
                base_dir = base_path / prefix.strip("/")
                sub_pattern = suffix.strip("/")
                matches = list(base_dir.rglob(sub_pattern)) if base_dir.exists() else []
            else:
                parent = base_path / Path(relative_pattern).parent
                if parent.exists():
                    matches = list(parent.glob(Path(relative_pattern).name))
                else:
                    matches = []

            _log_info(f"Pattern '{pattern}' matched {len(matches)} file(s)")
            return [path for path in matches if path.is_file()]
        except Exception as exc:
            _log_warn(f"Error processing pattern '{pattern}': {exc}")
            return []

    def _load_mock_file(self, path: Path) -> None:
        parsed = MockFileParser.parse(path)
        if parsed is None:
            return

        method, url, spec = parsed
        if url.startswith("~"):
            self.store.add_wildcard(method, url[1:].strip(), spec)
            return

        self.store.add_exact(method, url, spec)

    def _build_response(
        self, spec: MockSpec, flow: http.HTTPFlow
    ) -> tuple[int, dict[str, str], bytes]:
        rendered_body = render_and_extract_body(spec.remainder, flow)

        if should_fetch_external(rendered_body):
            status, headers, body = fetch_external(
                rendered_body,
                mock_status=spec.status,
                mock_headers=spec.headers,
            )
        else:
            status = spec.status
            headers = dict(spec.headers)
            body = rendered_body.encode("utf-8")

        normalized_headers = normalize_response_headers(
            headers, flow.request.http_version
        )
        return status, normalized_headers, body
