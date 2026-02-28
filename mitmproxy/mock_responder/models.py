from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

EXTERNAL_RESPONSE_EXCLUDED_HEADERS = frozenset(
    {"transfer-encoding", "content-length", "connection"}
)

HTTP2_OR_3_DISALLOWED_HEADERS = frozenset(
    {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailer",
        "transfer-encoding",
        "upgrade",
    }
)


@dataclass
class MockSpec:
    status: int
    headers: dict[str, str]
    remainder: str


class MockKey(NamedTuple):
    method: str
    url: str


class WildcardMock(NamedTuple):
    method: str
    pattern: str
    spec: MockSpec
