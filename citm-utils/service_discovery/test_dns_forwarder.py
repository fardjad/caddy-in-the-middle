from __future__ import annotations

import socket
import time

from dnslib import DNSHeader, DNSRecord, QTYPE, RCODE

import service_discovery.dns_forwarder as dns_forwarder
from service_discovery.dns_forwarder import (
    DiscoveryCache,
    DnsRecordSet,
    ResolvConfManager,
    build_local_response,
    find_matching_record_set,
    matches_suffix,
    select_best_suffix_match,
)


def _make_forwarder(monkeypatch, *, discovered_records=None, upstream_nameservers=None):
    discovered_records = discovered_records or {}
    upstream_nameservers = upstream_nameservers or []
    monkeypatch.setattr(
        dns_forwarder,
        "get_citm_dns_record_sets",
        lambda _docker_client, network_name=None: discovered_records,
    )
    return dns_forwarder.DnsForwarder(
        docker_client=object(),
        upstream_nameservers=upstream_nameservers,
        cache_ttl_seconds=60,
        upstream_timeout_seconds=1.0,
    )


def test_matches_label_boundary_suffix():
    assert matches_suffix("a.b", "a.b")
    assert matches_suffix("x.a.b", "a.b")
    assert matches_suffix("y.x.a.b", "a.b")


def test_does_not_match_without_label_boundary():
    assert not matches_suffix("xa.b", "a.b")
    assert not matches_suffix("a.bb", "a.b")


def test_selects_longest_suffix_match():
    records = {
        "b": DnsRecordSet(ipv4=("10.0.0.1",), ipv6=()),
        "a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=()),
        "x.a.b": DnsRecordSet(ipv4=("10.0.0.3",), ipv6=()),
    }
    assert select_best_suffix_match("z.x.a.b", records) == "x.a.b"


def test_build_local_response_returns_ipv4_for_a_query():
    request = DNSRecord.question("svc.a.b", qtype="A")
    response = build_local_response(
        request,
        record_set=DnsRecordSet(ipv4=("10.0.0.2", "10.0.0.3"), ipv6=()),
        ttl_seconds=30,
    )
    assert response is not None
    assert [rr.rtype for rr in response.rr] == [QTYPE.A, QTYPE.A]


def test_build_local_response_returns_ipv6_for_aaaa_query():
    request = DNSRecord.question("svc.a.b", qtype="AAAA")
    response = build_local_response(
        request,
        record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
        ttl_seconds=30,
    )
    assert response is not None
    assert [rr.rtype for rr in response.rr] == [QTYPE.AAAA]


def test_build_local_response_returns_nodata_when_no_aaaa_records():
    request = DNSRecord.question("svc.a.b", qtype="AAAA")
    response = build_local_response(
        request,
        record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=()),
        ttl_seconds=30,
    )
    assert response is not None
    assert response.header.rcode == 0
    assert len(response.rr) == 0


def test_build_local_response_returns_a_then_aaaa_for_any():
    request = DNSRecord.question("svc.a.b", qtype="ANY")
    response = build_local_response(
        request,
        record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
        ttl_seconds=30,
    )
    assert response is not None
    assert [rr.rtype for rr in response.rr] == [QTYPE.A, QTYPE.AAAA]


def test_build_local_response_returns_none_for_non_address_query():
    request = DNSRecord.question("svc.a.b", qtype="TXT")
    response = build_local_response(
        request,
        record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
        ttl_seconds=30,
    )
    assert response is None


def test_cache_reuses_entries_within_ttl():
    calls = {"count": 0}

    def load_records():
        calls["count"] += 1
        return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

    cache = DiscoveryCache(0.5, load_records)
    cache.get_records()
    cache.get_records()
    assert calls["count"] == 1


def test_cache_refreshes_after_ttl():
    calls = {"count": 0}

    def load_records():
        calls["count"] += 1
        return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

    cache = DiscoveryCache(0.1, load_records)
    cache.get_records()
    time.sleep(0.2)
    cache.get_records()
    assert calls["count"] == 2


def test_cache_miss_triggers_force_refresh():
    calls = {"count": 0}

    def load_records():
        calls["count"] += 1
        if calls["count"] == 1:
            return {}
        return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

    cache = DiscoveryCache(60, load_records)
    result = find_matching_record_set("x.a.b", cache)
    assert result is not None
    assert calls["count"] == 2


def test_resolv_conf_manager_activate_and_restore(tmp_path):
    resolv_path = tmp_path / "resolv.conf"
    backup_path = tmp_path / "resolv.conf.bak"
    original_content = "nameserver 1.1.1.1\nnameserver 127.0.0.1\n"
    resolv_path.write_text(original_content, encoding="utf-8")

    manager = ResolvConfManager(
        resolv_path=str(resolv_path),
        backup_path=str(backup_path),
    )

    assert manager.get_upstream_nameservers() == ["1.1.1.1"]

    manager.activate_localhost()
    assert resolv_path.read_text(encoding="utf-8") == "nameserver 127.0.0.1\n"

    manager.restore()
    assert resolv_path.read_text(encoding="utf-8") == original_content
    assert not backup_path.exists()


def test_resolve_returns_empty_bytes_for_invalid_request(monkeypatch):
    forwarder = _make_forwarder(monkeypatch)
    assert forwarder.resolve(b"invalid-packet", via_tcp=False) == b""


def test_resolve_returns_formerr_when_no_questions(monkeypatch):
    forwarder = _make_forwarder(monkeypatch)
    request_bytes = DNSRecord(DNSHeader(id=7)).pack()

    response_bytes = forwarder.resolve(request_bytes, via_tcp=False)
    response = DNSRecord.parse(response_bytes)

    assert response.header.id == 7
    assert response.header.rcode == RCODE.FORMERR


def test_resolve_prefers_local_records_over_upstream(monkeypatch):
    forwarder = _make_forwarder(
        monkeypatch,
        discovered_records={
            "svc.local": DnsRecordSet(ipv4=("10.0.0.8",), ipv6=()),
        },
    )
    upstream_calls = {"count": 0}

    def fake_forward_upstream(_request_bytes, *, via_tcp):
        assert via_tcp is False
        upstream_calls["count"] += 1
        return b"ignored"

    monkeypatch.setattr(forwarder, "_forward_upstream", fake_forward_upstream)
    response_bytes = forwarder.resolve(
        DNSRecord.question("api.svc.local", qtype="A").pack(),
        via_tcp=False,
    )
    response = DNSRecord.parse(response_bytes)

    assert upstream_calls["count"] == 0
    assert response.header.rcode == RCODE.NOERROR
    assert [str(rr.rdata) for rr in response.rr] == ["10.0.0.8"]


def test_resolve_forwards_non_address_query_when_local_name_matches(monkeypatch):
    forwarder = _make_forwarder(
        monkeypatch,
        discovered_records={
            "svc.local": DnsRecordSet(ipv4=("10.0.0.8",), ipv6=()),
        },
    )
    monkeypatch.setattr(
        forwarder, "_forward_upstream", lambda *_args, **_kwargs: b"upstream"
    )

    response = forwarder.resolve(
        DNSRecord.question("api.svc.local", qtype="TXT").pack(),
        via_tcp=False,
    )

    assert response == b"upstream"


def test_resolve_returns_servfail_when_upstream_unavailable(monkeypatch):
    forwarder = _make_forwarder(
        monkeypatch,
        discovered_records={},
        upstream_nameservers=[],
    )

    response_bytes = forwarder.resolve(
        DNSRecord.question("no-match.local", qtype="A").pack(),
        via_tcp=False,
    )
    response = DNSRecord.parse(response_bytes)

    assert response.header.rcode == RCODE.SERVFAIL


def test_forward_upstream_retries_over_tcp_for_truncated_udp(monkeypatch):
    forwarder = _make_forwarder(
        monkeypatch,
        discovered_records={},
        upstream_nameservers=["1.1.1.1"],
    )
    request_bytes = DNSRecord.question("svc.local", qtype="A").pack()
    udp_response = DNSRecord.question("svc.local", qtype="A").reply()
    udp_response.header.tc = 1

    calls: list[tuple[str, str]] = []

    def fake_udp(nameserver: str, _request_bytes: bytes) -> bytes:
        calls.append(("udp", nameserver))
        return udp_response.pack()

    def fake_tcp(nameserver: str, _request_bytes: bytes) -> bytes:
        calls.append(("tcp", nameserver))
        return b"tcp-response"

    monkeypatch.setattr(forwarder, "_forward_udp", fake_udp)
    monkeypatch.setattr(forwarder, "_forward_tcp", fake_tcp)

    result = forwarder._forward_upstream(request_bytes, via_tcp=False)

    assert result == b"tcp-response"
    assert calls == [("udp", "1.1.1.1"), ("tcp", "1.1.1.1")]


def test_forward_upstream_returns_none_when_all_nameservers_fail(monkeypatch):
    forwarder = _make_forwarder(
        monkeypatch,
        discovered_records={},
        upstream_nameservers=["1.1.1.1", "8.8.8.8"],
    )

    def failing_udp(_nameserver: str, _request_bytes: bytes) -> bytes:
        raise TimeoutError("timed out")

    monkeypatch.setattr(forwarder, "_forward_udp", failing_udp)
    result = forwarder._forward_upstream(
        DNSRecord.question("svc.local", qtype="A").pack(),
        via_tcp=False,
    )

    assert result is None
