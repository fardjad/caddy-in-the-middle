from __future__ import annotations

from flask import Flask

import supervisor.routes as routes
from supervisor import client
from supervisor.routes import supervisor_blueprint


def _create_client():
    app = Flask(__name__)
    app.register_blueprint(supervisor_blueprint)
    return app.test_client()


def test_list_services_returns_services_and_hostname(monkeypatch):
    monkeypatch.setattr(
        routes.client,
        "list_services",
        lambda: [{"name": "caddy", "state": "RUNNING", "description": ""}],
    )
    monkeypatch.setattr(routes.socket, "gethostname", lambda: "citm-host")
    test_client = _create_client()

    response = test_client.get("/supervisor/api/services")

    assert response.status_code == 200
    assert response.get_json() == {
        "services": [{"name": "caddy", "state": "RUNNING", "description": ""}],
        "hostname": "citm-host",
    }


def test_list_services_maps_supervisor_error(monkeypatch):
    def _raise():
        raise client.SupervisorError(
            "custom failure", status_code=418, details="teapot"
        )

    monkeypatch.setattr(routes.client, "list_services", _raise)
    test_client = _create_client()

    response = test_client.get("/supervisor/api/services")

    assert response.status_code == 418
    assert response.get_json() == {"error": "custom failure", "details": "teapot"}


def test_list_services_maps_unknown_error_to_bad_gateway(monkeypatch):
    monkeypatch.setattr(
        routes.client,
        "list_services",
        lambda: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    test_client = _create_client()

    response = test_client.get("/supervisor/api/services")

    assert response.status_code == 502
    payload = response.get_json()
    assert payload["error"] == "Failed to read supervisor services"
    assert "boom" in payload["details"]


def test_service_action_success(monkeypatch):
    called = {}

    def _record(name: str, action: str):
        called["name"] = name
        called["action"] = action

    monkeypatch.setattr(routes.client, "service_action", _record)
    test_client = _create_client()

    response = test_client.post("/supervisor/api/services/caddy/restart")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert called == {"name": "caddy", "action": "restart"}


def test_service_action_maps_supervisor_error(monkeypatch):
    def _raise(_name: str, _action: str):
        raise client.SupervisorError(
            "invalid request", status_code=400, details="bad action"
        )

    monkeypatch.setattr(routes.client, "service_action", _raise)
    test_client = _create_client()

    response = test_client.post("/supervisor/api/services/caddy/restart")

    assert response.status_code == 400
    assert response.get_json() == {"error": "invalid request", "details": "bad action"}


def test_restart_all_success(monkeypatch):
    called = {"count": 0}

    def _record():
        called["count"] += 1

    monkeypatch.setattr(routes.client, "restart_all", _record)
    test_client = _create_client()

    response = test_client.post("/supervisor/api/services/restart-all")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert called["count"] == 1


def test_restart_all_maps_unknown_error_to_bad_gateway(monkeypatch):
    monkeypatch.setattr(
        routes.client,
        "restart_all",
        lambda: (_ for _ in ()).throw(RuntimeError("cannot restart")),
    )
    test_client = _create_client()

    response = test_client.post("/supervisor/api/services/restart-all")

    assert response.status_code == 502
    payload = response.get_json()
    assert payload["error"] == "Supervisor action failed"
    assert "cannot restart" in payload["details"]
