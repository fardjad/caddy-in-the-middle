from __future__ import annotations

import subprocess

from flask import Flask

import mitmproxy.routes as routes
from mitmproxy.har import HarGenerationInProgressError
from mitmproxy.routes import mitmproxy_blueprint


def _create_client():
    app = Flask(__name__)
    app.register_blueprint(mitmproxy_blueprint)
    return app.test_client()


def test_har_route_returns_file_on_success(monkeypatch, tmp_path):
    har_path = tmp_path / "dump.har"
    har_path.write_text('{"log": {}}', encoding="utf-8")

    monkeypatch.setattr(routes, "generate_har", lambda: str(har_path))
    client = _create_client()

    response = client.get("/har")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.data == b'{"log": {}}'


def test_har_route_returns_conflict_when_generation_in_progress(monkeypatch):
    def _raise_in_progress():
        raise HarGenerationInProgressError()

    monkeypatch.setattr(routes, "generate_har", _raise_in_progress)
    client = _create_client()

    response = client.get("/har")

    assert response.status_code == 409
    assert response.get_json() == {"error": "HAR generation already in progress"}


def test_har_route_returns_bad_gateway_on_subprocess_error(monkeypatch):
    def _raise_subprocess_error():
        raise subprocess.CalledProcessError(1, ["mitmdump"])

    monkeypatch.setattr(routes, "generate_har", _raise_subprocess_error)
    client = _create_client()

    response = client.get("/har")

    assert response.status_code == 502
    payload = response.get_json()
    assert payload["error"] == "HAR generation failed"
    assert "non-zero exit status" in payload["details"]
