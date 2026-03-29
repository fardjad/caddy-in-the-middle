from __future__ import annotations

import logging
from pathlib import Path

from mitmproxy import ctx

from .models import MockSpec


def _log_warn(message: str) -> None:
    logger = getattr(ctx, "log", None)
    if logger is not None:
        logger.warn(message)
        return
    logging.getLogger(__name__).warning(message)


class MockFileParser:
    @staticmethod
    def parse(path: Path) -> tuple[str, str, MockSpec] | None:
        try:
            content = path.read_text(encoding="utf-8")
            return MockFileParser._parse_content(content, path.name)
        except Exception as exc:
            _log_warn(f"Failed to parse mock file {path.name}: {exc}")
            return None

    @staticmethod
    def _parse_content(content: str, filename: str) -> tuple[str, str, MockSpec]:
        sections = content.split("\n\n", 2)

        if len(sections) < 2:
            raise ValueError(
                "Mock file must have at least request line and status sections"
            )

        method, url = MockFileParser._parse_request_line(sections[0])
        status, headers = MockFileParser._parse_status_and_headers(
            sections[1], filename
        )
        remainder = sections[2] if len(sections) == 3 else ""

        return (
            method,
            url,
            MockSpec(status=status, headers=headers, remainder=remainder),
        )

    @staticmethod
    def _parse_request_line(section: str) -> tuple[str, str]:
        first_line = section.strip().split("\n")[0]
        if not first_line:
            raise ValueError("Missing request line (METHOD URL)")

        parts = first_line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"Request line must be 'METHOD URL', got: {first_line}")

        return parts[0].upper(), parts[1]

    @staticmethod
    def _parse_status_and_headers(
        section: str, filename: str
    ) -> tuple[int, dict[str, str]]:
        lines = [line.strip() for line in section.splitlines() if line.strip()]
        if not lines:
            raise ValueError("Missing status code")

        try:
            status = int(lines[0])
        except ValueError as exc:
            raise ValueError(f"Invalid status code: {lines[0]}") from exc

        headers: dict[str, str] = {}
        for line in lines[1:]:
            if ":" not in line:
                _log_warn(f"Skipping malformed header in {filename}: '{line}'")
                continue

            key, value = line.split(":", 1)
            headers[key.strip()] = value.strip()

        return status, headers
