from __future__ import annotations

from mock_responder.models import MockSpec
from mock_responder.store import MockStore


def test_find_mock_prefers_exact_match_over_wildcard():
    store = MockStore()
    wildcard = MockSpec(status=200, headers={"X-Case": "wildcard"}, remainder="---\nA")
    exact = MockSpec(status=201, headers={"X-Case": "exact"}, remainder="---\nB")

    store.add_wildcard("GET", "https://service.example/items/*", wildcard)
    store.add_exact("GET", "https://service.example/items/42", exact)

    matched = store.find_mock("GET", "https://service.example/items/42")

    assert matched is exact


def test_find_mock_uses_wildcard_when_exact_match_does_not_exist():
    store = MockStore()
    wildcard = MockSpec(status=202, headers={"X-Case": "wildcard"}, remainder="---\nA")
    store.add_wildcard("GET", "https://service.example/items/*", wildcard)

    matched = store.find_mock("GET", "https://service.example/items/7")

    assert matched is wildcard


def test_find_mock_returns_none_when_no_pattern_matches():
    store = MockStore()
    store.add_wildcard(
        "POST",
        "https://service.example/items/*",
        MockSpec(status=200, headers={}, remainder="---\nA"),
    )

    matched = store.find_mock("GET", "https://service.example/items/7")

    assert matched is None
