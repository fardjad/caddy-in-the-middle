import os
from collections import defaultdict
from dataclasses import dataclass

from docker import DockerClient


@dataclass(frozen=True)
class DnsRecordSet:
    ipv4: tuple[str, ...]
    ipv6: tuple[str, ...]


def _normalize_dns_name(name: str) -> str:
    return name.strip().lower().rstrip(".")


def _get_discovery_network(explicit_network: str | None = None) -> str | None:
    if explicit_network:
        return explicit_network
    return os.getenv("CITM_DNS_NETWORK") or os.getenv("CITM_NETWORK")


def _list_discoverable_containers(
    docker_client: DockerClient, *, network_name: str | None
):
    filters = (
        {
            "label": [
                "citm_dns_names",
                f"citm_network={network_name}",
            ]
        }
        if network_name
        else {"label": ["citm_network", "citm_dns_names"]}
    )
    containers = docker_client.containers.list(all=False, filters=filters)
    return sorted(containers, key=lambda container: container.id)


def _to_dns_names(raw_names: str) -> list[str]:
    return [
        normalized
        for name in raw_names.split(",")
        if (normalized := _normalize_dns_name(name))
    ]


def get_citm_dns_record_sets(
    docker_client: DockerClient, *, network_name: str | None = None
) -> dict[str, DnsRecordSet]:
    selected_network = _get_discovery_network(network_name)
    containers = _list_discoverable_containers(
        docker_client, network_name=selected_network
    )

    records: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: {"ipv4": set(), "ipv6": set()}
    )

    for container in containers:
        container_network = container.labels.get("citm_network")
        if not container_network:
            continue
        if selected_network and container_network != selected_network:
            continue

        network = container.attrs["NetworkSettings"]["Networks"].get(container_network)
        if not network:
            continue

        ipv4 = (network.get("IPAddress") or "").strip()
        ipv6 = (network.get("GlobalIPv6Address") or "").strip()

        if not ipv4 and not ipv6:
            continue

        dns_names = _to_dns_names(container.labels.get("citm_dns_names", ""))
        for dns_name in dns_names:
            if ipv4:
                records[dns_name]["ipv4"].add(ipv4)
            if ipv6:
                records[dns_name]["ipv6"].add(ipv6)

    return {
        dns_name: DnsRecordSet(
            ipv4=tuple(sorted(families["ipv4"])),
            ipv6=tuple(sorted(families["ipv6"])),
        )
        for dns_name, families in sorted(records.items())
    }


def get_citm_dns_entries(
    docker_client: DockerClient, *, network_name: str | None = None
) -> dict[str, dict[str, list[str]]]:
    records = get_citm_dns_record_sets(docker_client, network_name=network_name)
    return {
        dns_name: {
            "ipv4": list(record_set.ipv4),
            "ipv6": list(record_set.ipv6),
        }
        for dns_name, record_set in records.items()
    }
