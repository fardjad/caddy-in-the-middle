import tempfile
import time
import unittest
from pathlib import Path

from dnslib import DNSRecord, QTYPE

from dns_forwarder import (
    DiscoveryCache,
    DnsRecordSet,
    ResolvConfManager,
    build_local_response,
    find_matching_record_set,
    matches_suffix,
    select_best_suffix_match,
)


class TestSuffixMatching(unittest.TestCase):
    def test_matches_label_boundary_suffix(self):
        self.assertTrue(matches_suffix("a.b", "a.b"))
        self.assertTrue(matches_suffix("x.a.b", "a.b"))
        self.assertTrue(matches_suffix("y.x.a.b", "a.b"))

    def test_does_not_match_without_label_boundary(self):
        self.assertFalse(matches_suffix("xa.b", "a.b"))
        self.assertFalse(matches_suffix("a.bb", "a.b"))

    def test_uses_longest_suffix_match(self):
        records = {
            "b": DnsRecordSet(ipv4=("10.0.0.1",), ipv6=()),
            "a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=()),
            "x.a.b": DnsRecordSet(ipv4=("10.0.0.3",), ipv6=()),
        }
        self.assertEqual(select_best_suffix_match("z.x.a.b", records), "x.a.b")


class TestRecordPolicy(unittest.TestCase):
    def test_a_query_returns_ipv4_answers(self):
        request = DNSRecord.question("svc.a.b", qtype="A")
        response = build_local_response(
            request,
            record_set=DnsRecordSet(ipv4=("10.0.0.2", "10.0.0.3"), ipv6=()),
            ttl_seconds=30,
        )
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual([rr.rtype for rr in response.rr], [QTYPE.A, QTYPE.A])

    def test_aaaa_query_returns_ipv6_answers(self):
        request = DNSRecord.question("svc.a.b", qtype="AAAA")
        response = build_local_response(
            request,
            record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
            ttl_seconds=30,
        )
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual([rr.rtype for rr in response.rr], [QTYPE.AAAA])

    def test_aaaa_query_with_no_ipv6_returns_nodata(self):
        request = DNSRecord.question("svc.a.b", qtype="AAAA")
        response = build_local_response(
            request,
            record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=()),
            ttl_seconds=30,
        )
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual(response.header.rcode, 0)
        self.assertEqual(len(response.rr), 0)

    def test_any_query_returns_a_then_aaaa(self):
        request = DNSRecord.question("svc.a.b", qtype="ANY")
        response = build_local_response(
            request,
            record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
            ttl_seconds=30,
        )
        self.assertIsNotNone(response)
        assert response is not None
        self.assertEqual([rr.rtype for rr in response.rr], [QTYPE.A, QTYPE.AAAA])

    def test_non_address_query_returns_none_for_upstream_forward(self):
        request = DNSRecord.question("svc.a.b", qtype="TXT")
        response = build_local_response(
            request,
            record_set=DnsRecordSet(ipv4=("10.0.0.2",), ipv6=("fd00::2",)),
            ttl_seconds=30,
        )
        self.assertIsNone(response)


class TestCacheBehavior(unittest.TestCase):
    def test_cache_reuses_entries_within_ttl(self):
        calls = {"count": 0}

        def load_records():
            calls["count"] += 1
            return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

        cache = DiscoveryCache(0.5, load_records)
        cache.get_records()
        cache.get_records()
        self.assertEqual(calls["count"], 1)

    def test_cache_refreshes_after_ttl(self):
        calls = {"count": 0}

        def load_records():
            calls["count"] += 1
            return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

        cache = DiscoveryCache(0.1, load_records)
        cache.get_records()
        time.sleep(0.2)
        cache.get_records()
        self.assertEqual(calls["count"], 2)

    def test_cache_miss_triggers_force_refresh(self):
        calls = {"count": 0}

        def load_records():
            calls["count"] += 1
            if calls["count"] == 1:
                return {}
            return {"a.b": DnsRecordSet(ipv4=("10.0.0.2",), ipv6=())}

        cache = DiscoveryCache(60, load_records)
        result = find_matching_record_set("x.a.b", cache)
        self.assertIsNotNone(result)
        self.assertEqual(calls["count"], 2)


class TestResolvConfManager(unittest.TestCase):
    def test_activate_and_restore(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            resolv_path = Path(temp_dir) / "resolv.conf"
            backup_path = Path(temp_dir) / "resolv.conf.bak"
            original_content = "nameserver 1.1.1.1\nnameserver 127.0.0.1\n"
            resolv_path.write_text(original_content, encoding="utf-8")

            manager = ResolvConfManager(
                resolv_path=str(resolv_path),
                backup_path=str(backup_path),
            )

            self.assertEqual(manager.get_upstream_nameservers(), ["1.1.1.1"])

            manager.activate_localhost()
            self.assertEqual(
                resolv_path.read_text(encoding="utf-8"),
                "nameserver 127.0.0.1\n",
            )

            manager.restore()
            self.assertEqual(
                resolv_path.read_text(encoding="utf-8"),
                original_content,
            )
            self.assertFalse(backup_path.exists())


if __name__ == "__main__":
    unittest.main()
