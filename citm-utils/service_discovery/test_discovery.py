from __future__ import annotations

from dataclasses import dataclass

from service_discovery.discovery import get_citm_dns_entries, get_citm_dns_record_sets


@dataclass
class FakeContainer:
    id: str
    labels: dict[str, str]
    attrs: dict


class FakeContainerCollection:
    def __init__(self, containers: list[FakeContainer]):
        self._containers = containers
        self.last_list_call: dict | None = None

    def list(self, all: bool, filters: dict):
        self.last_list_call = {"all": all, "filters": filters}
        return list(self._containers)


class FakeDockerClient:
    def __init__(self, containers: list[FakeContainer]):
        self.containers = FakeContainerCollection(containers)


def _network(ipv4: str = "", ipv6: str = "") -> dict[str, str]:
    return {"IPAddress": ipv4, "GlobalIPv6Address": ipv6}


def test_get_citm_dns_record_sets_filters_by_selected_network_and_normalizes_names():
    containers = [
        FakeContainer(
            id="2",
            labels={"citm_network": "net1", "citm_dns_names": "API.local, www.local."},
            attrs={
                "NetworkSettings": {
                    "Networks": {"net1": _network("10.0.0.2", "fd00::2")}
                }
            },
        ),
        FakeContainer(
            id="1",
            labels={"citm_network": "net1", "citm_dns_names": "api.local,db.local"},
            attrs={"NetworkSettings": {"Networks": {"net1": _network("10.0.0.3")}}},
        ),
        FakeContainer(
            id="3",
            labels={"citm_network": "net2", "citm_dns_names": "api.local"},
            attrs={"NetworkSettings": {"Networks": {"net2": _network("10.0.0.4")}}},
        ),
        FakeContainer(
            id="4",
            labels={"citm_dns_names": "ignored.local"},
            attrs={"NetworkSettings": {"Networks": {"net1": _network("10.0.0.5")}}},
        ),
    ]
    docker_client = FakeDockerClient(containers)

    records = get_citm_dns_record_sets(docker_client, network_name="net1")

    assert records["api.local"].ipv4 == ("10.0.0.2", "10.0.0.3")
    assert records["api.local"].ipv6 == ("fd00::2",)
    assert records["db.local"].ipv4 == ("10.0.0.3",)
    assert records["www.local"].ipv4 == ("10.0.0.2",)
    assert "ignored.local" not in records
    assert docker_client.containers.last_list_call == {
        "all": False,
        "filters": {
            "label": [
                "citm_dns_names",
                "citm_network=net1",
            ]
        },
    }


def test_get_citm_dns_record_sets_uses_env_selected_network(monkeypatch):
    containers = [
        FakeContainer(
            id="1",
            labels={"citm_network": "env-net", "citm_dns_names": "svc.local"},
            attrs={
                "NetworkSettings": {
                    "Networks": {"env-net": _network("10.0.0.2", "fd00::2")}
                }
            },
        ),
        FakeContainer(
            id="2",
            labels={"citm_network": "other-net", "citm_dns_names": "svc.local"},
            attrs={
                "NetworkSettings": {"Networks": {"other-net": _network("10.0.0.3")}}
            },
        ),
    ]
    docker_client = FakeDockerClient(containers)
    monkeypatch.setenv("CITM_DNS_NETWORK", "env-net")
    monkeypatch.setenv("CITM_NETWORK", "fallback-net")

    records = get_citm_dns_record_sets(docker_client)

    assert records["svc.local"].ipv4 == ("10.0.0.2",)
    assert docker_client.containers.last_list_call == {
        "all": False,
        "filters": {
            "label": [
                "citm_dns_names",
                "citm_network=env-net",
            ]
        },
    }


def test_get_citm_dns_entries_returns_json_friendly_lists():
    containers = [
        FakeContainer(
            id="1",
            labels={"citm_network": "net1", "citm_dns_names": "svc.local"},
            attrs={
                "NetworkSettings": {
                    "Networks": {"net1": _network("10.0.0.2", "fd00::2")}
                }
            },
        ),
    ]
    docker_client = FakeDockerClient(containers)

    entries = get_citm_dns_entries(docker_client, network_name="net1")

    assert entries == {"svc.local": {"ipv4": ["10.0.0.2"], "ipv6": ["fd00::2"]}}
