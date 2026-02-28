from __future__ import annotations

import xmlrpc.client
from types import SimpleNamespace

import pytest

import supervisor.client as client


class FakeSupervisorAPI:
    def __init__(self, processes: list[dict]):
        self._base_processes = [dict(process) for process in processes]
        self._processes_by_name = {
            process["name"]: dict(process)
            for process in processes
            if process.get("name")
        }
        self.calls: list[tuple] = []
        self.start_side_effects: dict[str, list[Exception | None]] = {}

    def getAllProcessInfo(self):
        self.calls.append(("getAllProcessInfo",))
        result = []
        for process in self._base_processes:
            name = process.get("name")
            if name and name in self._processes_by_name:
                merged = dict(process)
                merged.update(self._processes_by_name[name])
                result.append(merged)
                continue
            result.append(dict(process))
        return result

    def getProcessInfo(self, name: str):
        self.calls.append(("getProcessInfo", name))
        return dict(self._processes_by_name[name])

    def startProcess(self, name: str, wait: bool):
        self.calls.append(("startProcess", name, wait))
        if effects := self.start_side_effects.get(name):
            effect = effects.pop(0)
            if effect is not None:
                raise effect
        self._processes_by_name.setdefault(name, {"name": name})[
            "statename"
        ] = "RUNNING"

    def stopProcess(self, name: str, wait: bool):
        self.calls.append(("stopProcess", name, wait))
        self._processes_by_name[name]["statename"] = "STOPPED"


def _server_with_processes(
    processes: list[dict],
) -> tuple[SimpleNamespace, FakeSupervisorAPI]:
    api = FakeSupervisorAPI(processes)
    return SimpleNamespace(supervisor=api), api


def test_list_services_filters_excluded_processes():
    server, _api = _server_with_processes(
        [
            {
                "name": "citm-utils-web",
                "statename": "RUNNING",
                "description": "internal",
            },
            {"name": "caddy", "statename": "RUNNING", "description": "  serving  "},
        ]
    )

    services = client.list_services(rpc_factory=lambda: server)

    assert services == [
        {
            "name": "caddy",
            "state": "RUNNING",
            "description": "serving",
        }
    ]


def test_list_services_wraps_rpc_failures():
    def failing_rpc():
        raise RuntimeError("rpc unavailable")

    with pytest.raises(client.SupervisorError) as exc_info:
        client.list_services(rpc_factory=failing_rpc)

    assert exc_info.value.status_code == 502
    assert "rpc unavailable" in exc_info.value.details


def test_service_action_rejects_unsupported_action():
    with pytest.raises(client.SupervisorError) as exc_info:
        client.service_action("caddy", "pause")
    assert exc_info.value.status_code == 400


def test_service_action_rejects_excluded_process():
    with pytest.raises(client.SupervisorError) as exc_info:
        client.service_action("citm-utils-web", "restart")
    assert exc_info.value.status_code == 400


def test_restart_running_service_stops_then_starts():
    server, api = _server_with_processes(
        [{"name": "caddy", "statename": "RUNNING", "description": ""}]
    )

    client.service_action("caddy", "restart", rpc_factory=lambda: server)

    assert ("stopProcess", "caddy", True) in api.calls
    assert ("startProcess", "caddy", False) in api.calls


def test_restart_stopped_service_starts_without_stop():
    server, api = _server_with_processes(
        [{"name": "caddy", "statename": "STOPPED", "description": ""}]
    )

    client.service_action("caddy", "restart", rpc_factory=lambda: server)

    assert ("startProcess", "caddy", False) in api.calls
    assert ("stopProcess", "caddy", True) not in api.calls


def test_stop_action_noops_for_non_running_service():
    server, api = _server_with_processes(
        [{"name": "caddy", "statename": "EXITED", "description": ""}]
    )

    client.service_action("caddy", "stop", rpc_factory=lambda: server)

    assert ("stopProcess", "caddy", True) not in api.calls


def test_start_retries_when_supervisor_reports_still_stopping():
    server, api = _server_with_processes(
        [{"name": "caddy", "statename": "STOPPED", "description": ""}]
    )
    api.start_side_effects["caddy"] = [
        xmlrpc.client.Fault(1, "STILL_STOPPING"),
        None,
    ]
    sleep_calls: list[float] = []

    client.service_action(
        "caddy",
        "start",
        rpc_factory=lambda: server,
        sleep=lambda seconds: sleep_calls.append(seconds),
    )

    assert sleep_calls == [0.3]
    assert ("startProcess", "caddy", False) in api.calls


def test_start_treats_already_started_fault_as_success():
    server, api = _server_with_processes(
        [{"name": "caddy", "statename": "RUNNING", "description": ""}]
    )
    api.start_side_effects["caddy"] = [xmlrpc.client.Fault(1, "ALREADY_STARTED")]

    client.service_action("caddy", "start", rpc_factory=lambda: server)

    assert ("startProcess", "caddy", False) in api.calls


def test_service_action_wraps_rpc_errors():
    def failing_rpc():
        raise RuntimeError("socket gone")

    with pytest.raises(client.SupervisorError) as exc_info:
        client.service_action("caddy", "start", rpc_factory=failing_rpc)

    assert exc_info.value.status_code == 502
    assert "socket gone" in exc_info.value.details


def test_restart_all_stops_running_then_starts_managed_processes():
    server, api = _server_with_processes(
        [
            {"name": "caddy", "statename": "RUNNING", "description": ""},
            {"name": "mitmproxy", "statename": "STOPPED", "description": ""},
            {"name": "citm-utils-web", "statename": "RUNNING", "description": ""},
        ]
    )

    client.restart_all(rpc_factory=lambda: server)

    stop_calls = [call for call in api.calls if call[0] == "stopProcess"]
    start_calls = [call for call in api.calls if call[0] == "startProcess"]
    assert stop_calls == [("stopProcess", "caddy", True)]
    assert ("startProcess", "caddy", False) in start_calls
    assert ("startProcess", "mitmproxy", False) in start_calls
    assert all(call[1] != "citm-utils-web" for call in start_calls)

    stop_indices = [
        index for index, call in enumerate(api.calls) if call[0] == "stopProcess"
    ]
    start_indices = [
        index for index, call in enumerate(api.calls) if call[0] == "startProcess"
    ]
    assert max(stop_indices) < min(start_indices)
