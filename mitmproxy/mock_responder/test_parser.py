from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import mock_responder.parser as parser_module
from mock_responder.parser import MockFileParser


def test_parse_reads_valid_mock_file(tmp_path: Path):
    path = tmp_path / "valid.mako"
    path.write_text(
        (
            "GET https://service.example/hello\n\n"
            "201\n"
            "Content-Type: text/plain\n"
            "X-Test: yes\n\n"
            "---\n"
            "hello\n"
        ),
        encoding="utf-8",
    )

    parsed = MockFileParser.parse(path)

    assert parsed is not None
    method, url, spec = parsed
    assert method == "GET"
    assert url == "https://service.example/hello"
    assert spec.status == 201
    assert spec.headers == {"Content-Type": "text/plain", "X-Test": "yes"}
    assert spec.remainder == "---\nhello\n"


def test_parse_returns_none_for_invalid_mock_file(monkeypatch, tmp_path: Path):
    path = tmp_path / "invalid.mako"
    path.write_text("GET https://service.example/only-one-section\n", encoding="utf-8")

    warnings: list[str] = []
    monkeypatch.setattr(
        parser_module,
        "ctx",
        SimpleNamespace(log=SimpleNamespace(warn=warnings.append)),
    )

    assert MockFileParser.parse(path) is None
    assert warnings
    assert "Failed to parse mock file invalid.mako" in warnings[0]


def test_parse_skips_malformed_header_lines(monkeypatch):
    warnings: list[str] = []
    monkeypatch.setattr(
        parser_module,
        "ctx",
        SimpleNamespace(log=SimpleNamespace(warn=warnings.append)),
    )

    method, url, spec = MockFileParser._parse_content(
        (
            "GET https://service.example/value\n\n"
            "200\n"
            "Content-Type: text/plain\n"
            "This is not a header\n\n"
            "---\n"
            "ok\n"
        ),
        "headers.mako",
    )

    assert method == "GET"
    assert url == "https://service.example/value"
    assert spec.headers == {"Content-Type": "text/plain"}
    assert warnings == [
        "Skipping malformed header in headers.mako: 'This is not a header'"
    ]
