import atexit
import ipaddress
import os
import shutil
import signal
import socket
import socketserver
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import docker
from dnslib import A, AAAA, DNSHeader, DNSRecord, QTYPE, RCODE, RR

from .discovery import DnsRecordSet, get_citm_dns_record_sets

ENV_CACHE_TTL_SECONDS = "CITM_DNS_CACHE_TTL_SECONDS"
ENV_LISTEN_HOST = "CITM_DNS_LISTEN_HOST"
ENV_LISTEN_PORT = "CITM_DNS_LISTEN_PORT"
ENV_UPSTREAM_TIMEOUT_SECONDS = "CITM_DNS_UPSTREAM_TIMEOUT_SECONDS"
ENV_DISCOVERY_NETWORK = "CITM_DNS_NETWORK"

DEFAULT_CACHE_TTL_SECONDS = 1.0
DEFAULT_LISTEN_HOST = "0.0.0.0"
DEFAULT_LISTEN_PORT = 53
DEFAULT_UPSTREAM_TIMEOUT_SECONDS = 2.0
DEFAULT_RECORD_TTL_SECONDS = 30

RESOLV_CONF_PATH = "/etc/resolv.conf"
RESOLV_CONF_BACKUP_PATH = "/etc/resolv.conf.bak"

DNS_PORT = 53

STATIC_RECORDS: dict[str, DnsRecordSet] = {
    "localhost": DnsRecordSet(ipv4=("127.0.0.1",), ipv6=()),
    "citm.internal": DnsRecordSet(ipv4=("127.0.0.1",), ipv6=()),
}


def _normalize_dns_name(name: str) -> str:
    return name.strip().lower().rstrip(".")


def matches_suffix(name: str, suffix: str) -> bool:
    normalized_name = _normalize_dns_name(name)
    normalized_suffix = _normalize_dns_name(suffix)
    return normalized_name == normalized_suffix or normalized_name.endswith(
        f".{normalized_suffix}"
    )


def select_best_suffix_match(name: str, records: dict[str, DnsRecordSet]) -> str | None:
    normalized_name = _normalize_dns_name(name)
    matches = [
        suffix for suffix in records.keys() if matches_suffix(normalized_name, suffix)
    ]
    if not matches:
        return None
    return max(matches, key=len)


def build_local_response(
    request: DNSRecord,
    *,
    record_set: DnsRecordSet,
    ttl_seconds: int,
) -> DNSRecord | None:
    qtype = request.q.qtype
    if qtype not in {QTYPE.A, QTYPE.AAAA, QTYPE.ANY}:
        return None

    reply = request.reply()
    qname = request.q.qname

    if qtype in {QTYPE.A, QTYPE.ANY}:
        for ip in record_set.ipv4:
            reply.add_answer(
                RR(
                    rname=qname,
                    rtype=QTYPE.A,
                    rclass=1,
                    ttl=ttl_seconds,
                    rdata=A(ip),
                )
            )

    if qtype in {QTYPE.AAAA, QTYPE.ANY}:
        for ip in record_set.ipv6:
            reply.add_answer(
                RR(
                    rname=qname,
                    rtype=QTYPE.AAAA,
                    rclass=1,
                    ttl=ttl_seconds,
                    rdata=AAAA(ip),
                )
            )

    return reply


def _is_loopback_address(address: str) -> bool:
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return False


def _address_family(address: str) -> socket.AddressFamily:
    return (
        socket.AF_INET6
        if ipaddress.ip_address(address).version == 6
        else socket.AF_INET
    )


def _socket_target(
    address: str, port: int
) -> tuple[str, int] | tuple[str, int, int, int]:
    if _address_family(address) == socket.AF_INET6:
        return (address, port, 0, 0)
    return (address, port)


def _read_exact(stream: socket.socket, size: int) -> bytes | None:
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = stream.recv(remaining)
        if not chunk:
            return None
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _to_float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = float(raw)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        print(f"Invalid {name}={raw!r}. Falling back to {default}.", flush=True)
        return default


def _to_int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        print(f"Invalid {name}={raw!r}. Falling back to {default}.", flush=True)
        return default


@dataclass(frozen=True)
class MatchResult:
    suffix: str
    records: DnsRecordSet


class DiscoveryCache:
    def __init__(
        self, ttl_seconds: float, loader: Callable[[], dict[str, DnsRecordSet]]
    ):
        self._ttl_seconds = ttl_seconds
        self._loader = loader
        self._records: dict[str, DnsRecordSet] = {}
        self._expires_at = 0.0
        self._lock = threading.Lock()

    def get_records(self, *, force: bool = False) -> dict[str, DnsRecordSet]:
        now = time.monotonic()
        with self._lock:
            if force or now >= self._expires_at:
                self._records = self._loader()
                self._expires_at = now + self._ttl_seconds
            return dict(self._records)


def find_matching_record_set(name: str, cache: DiscoveryCache) -> MatchResult | None:
    records = cache.get_records()
    matched_suffix = select_best_suffix_match(name, records)
    if not matched_suffix:
        records = cache.get_records(force=True)
        matched_suffix = select_best_suffix_match(name, records)
        if not matched_suffix:
            return None
    return MatchResult(suffix=matched_suffix, records=records[matched_suffix])


class ResolvConfManager:
    def __init__(
        self,
        *,
        resolv_path: str = RESOLV_CONF_PATH,
        backup_path: str = RESOLV_CONF_BACKUP_PATH,
    ):
        self._resolv_path = resolv_path
        self._backup_path = backup_path
        self._is_activated = False
        self._lock = threading.Lock()

    def get_upstream_nameservers(self) -> list[str]:
        if not os.path.exists(self._resolv_path):
            return []
        nameservers: list[str] = []
        with open(self._resolv_path, encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line.startswith("nameserver"):
                    continue
                parts = line.split()
                if len(parts) < 2:
                    continue
                nameserver = parts[1].strip()
                if _is_loopback_address(nameserver):
                    continue
                nameservers.append(nameserver)
        return nameservers

    def activate_localhost(self) -> None:
        with self._lock:
            shutil.copyfile(self._resolv_path, self._backup_path)
            with open(self._resolv_path, "w", encoding="utf-8") as handle:
                handle.write("nameserver 127.0.0.1\n")
            self._is_activated = True

    def restore(self) -> None:
        with self._lock:
            if not self._is_activated:
                return
            if os.path.exists(self._backup_path):
                shutil.copyfile(self._backup_path, self._resolv_path)
                os.remove(self._backup_path)
            self._is_activated = False


class DnsForwarder:
    def __init__(
        self,
        *,
        docker_client: docker.DockerClient,
        upstream_nameservers: list[str],
        cache_ttl_seconds: float,
        upstream_timeout_seconds: float,
        discovery_network: str | None = None,
    ):
        self._docker_client = docker_client
        self._upstream_nameservers = upstream_nameservers
        self._upstream_timeout_seconds = upstream_timeout_seconds
        self._discovery_network = discovery_network
        self._cache = DiscoveryCache(cache_ttl_seconds, self._load_discovery_records)

    def _load_discovery_records(self) -> dict[str, DnsRecordSet]:
        discovered = get_citm_dns_record_sets(
            self._docker_client,
            network_name=self._discovery_network,
        )
        merged = dict(discovered)
        for name, static_record in STATIC_RECORDS.items():
            merged[name] = static_record
        return merged

    def _to_servfail_response(self, request: DNSRecord) -> bytes:
        response = request.reply()
        response.header.rcode = RCODE.SERVFAIL
        return response.pack()

    def _to_formerr_response(self, request_id: int) -> bytes:
        response = DNSRecord(
            DNSHeader(
                id=request_id,
                qr=1,
                ra=1,
                rcode=RCODE.FORMERR,
            )
        )
        return response.pack()

    def _forward_udp(self, nameserver: str, request_bytes: bytes) -> bytes:
        family = _address_family(nameserver)
        with socket.socket(family, socket.SOCK_DGRAM) as upstream_socket:
            upstream_socket.settimeout(self._upstream_timeout_seconds)
            upstream_socket.sendto(request_bytes, _socket_target(nameserver, DNS_PORT))
            response, _ = upstream_socket.recvfrom(65535)
        return response

    def _forward_tcp(self, nameserver: str, request_bytes: bytes) -> bytes:
        family = _address_family(nameserver)
        with socket.socket(family, socket.SOCK_STREAM) as upstream_socket:
            upstream_socket.settimeout(self._upstream_timeout_seconds)
            upstream_socket.connect(_socket_target(nameserver, DNS_PORT))
            upstream_socket.sendall(
                len(request_bytes).to_bytes(2, "big") + request_bytes
            )
            response_len_wire = _read_exact(upstream_socket, 2)
            if response_len_wire is None:
                raise TimeoutError("No upstream TCP response length")
            response_len = int.from_bytes(response_len_wire, "big")
            response = _read_exact(upstream_socket, response_len)
            if response is None:
                raise TimeoutError("No upstream TCP response payload")
            return response

    def _is_truncated(self, response_bytes: bytes) -> bool:
        try:
            response = DNSRecord.parse(response_bytes)
            return bool(response.header.tc)
        except Exception:
            return False

    def _forward_upstream(self, request_bytes: bytes, *, via_tcp: bool) -> bytes | None:
        for nameserver in self._upstream_nameservers:
            try:
                if via_tcp:
                    return self._forward_tcp(nameserver, request_bytes)
                response = self._forward_udp(nameserver, request_bytes)
                if self._is_truncated(response):
                    return self._forward_tcp(nameserver, request_bytes)
                return response
            except Exception:
                continue
        return None

    def resolve(self, request_bytes: bytes, *, via_tcp: bool) -> bytes:
        try:
            request = DNSRecord.parse(request_bytes)
        except Exception:
            return b""

        if not request.questions:
            return self._to_formerr_response(request.header.id)

        qname = _normalize_dns_name(str(request.q.qname))
        match = find_matching_record_set(qname, self._cache)
        if match is not None:
            local_response = build_local_response(
                request,
                record_set=match.records,
                ttl_seconds=DEFAULT_RECORD_TTL_SECONDS,
            )
            if local_response is not None:
                return local_response.pack()

        upstream_response = self._forward_upstream(request_bytes, via_tcp=via_tcp)
        if upstream_response is not None:
            return upstream_response
        return self._to_servfail_response(request)


class ThreadingUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    daemon_threads = True
    allow_reuse_address = True
    forwarder: DnsForwarder


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True
    forwarder: DnsForwarder


class DnsUdpHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        request_bytes: bytes = self.request[0]
        response_socket: socket.socket = self.request[1]
        response = self.server.forwarder.resolve(request_bytes, via_tcp=False)
        if response:
            response_socket.sendto(response, self.client_address)


class DnsTcpHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        while True:
            request_len_wire = self.rfile.read(2)
            if len(request_len_wire) == 0:
                return
            if len(request_len_wire) < 2:
                return

            request_len = int.from_bytes(request_len_wire, "big")
            request_bytes = self.rfile.read(request_len)
            if len(request_bytes) < request_len:
                return

            response = self.server.forwarder.resolve(request_bytes, via_tcp=True)
            if not response:
                return
            self.wfile.write(len(response).to_bytes(2, "big") + response)


def _start_server(server: socketserver.BaseServer) -> threading.Thread:
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return thread


def main() -> None:
    cache_ttl_seconds = _to_float_env(ENV_CACHE_TTL_SECONDS, DEFAULT_CACHE_TTL_SECONDS)
    listen_host = os.getenv(ENV_LISTEN_HOST, DEFAULT_LISTEN_HOST)
    listen_port = _to_int_env(ENV_LISTEN_PORT, DEFAULT_LISTEN_PORT)
    upstream_timeout_seconds = _to_float_env(
        ENV_UPSTREAM_TIMEOUT_SECONDS, DEFAULT_UPSTREAM_TIMEOUT_SECONDS
    )
    discovery_network = os.getenv(ENV_DISCOVERY_NETWORK) or os.getenv("CITM_NETWORK")

    docker_client = docker.from_env()
    resolv_manager = ResolvConfManager()
    upstream_nameservers = resolv_manager.get_upstream_nameservers()

    if not upstream_nameservers:
        print(
            "No upstream nameservers found in /etc/resolv.conf. "
            "Unmatched DNS queries will return SERVFAIL.",
            flush=True,
        )

    resolv_manager.activate_localhost()
    atexit.register(resolv_manager.restore)

    forwarder = DnsForwarder(
        docker_client=docker_client,
        upstream_nameservers=upstream_nameservers,
        cache_ttl_seconds=cache_ttl_seconds,
        upstream_timeout_seconds=upstream_timeout_seconds,
        discovery_network=discovery_network,
    )

    udp_server = ThreadingUDPServer((listen_host, listen_port), DnsUdpHandler)
    udp_server.forwarder = forwarder
    tcp_server = ThreadingTCPServer((listen_host, listen_port), DnsTcpHandler)
    tcp_server.forwarder = forwarder

    servers: list[socketserver.BaseServer] = [udp_server, tcp_server]
    for server in servers:
        _start_server(server)

    print(
        f"CITM DNS forwarder listening on {listen_host}:{listen_port} "
        f"(udp/tcp), cache TTL {cache_ttl_seconds}s",
        flush=True,
    )

    stop_event = threading.Event()

    def _request_shutdown(_sig: int, _frame: Any) -> None:
        stop_event.set()
        for server in servers:
            server.shutdown()

    signal.signal(signal.SIGINT, _request_shutdown)
    signal.signal(signal.SIGTERM, _request_shutdown)

    try:
        while not stop_event.wait(0.5):
            continue
    finally:
        for server in servers:
            server.server_close()
        resolv_manager.restore()
        docker_client.close()


if __name__ == "__main__":
    main()
