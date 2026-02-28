import socket
from pathlib import Path

from flask import Blueprint, jsonify, send_file

from . import client

supervisor_blueprint = Blueprint("supervisor", __name__)


@supervisor_blueprint.route("/supervisor", methods=["GET"])
def get_ui():
    return send_file(Path(__file__).with_name("supervisor.html"))


@supervisor_blueprint.route("/supervisor/api/services", methods=["GET"])
def list_services():
    try:
        services = client.list_services()
        return jsonify({"services": services, "hostname": socket.gethostname()}), 200
    except client.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return (
            jsonify({"error": "Failed to read supervisor services", "details": str(e)}),
            502,
        )


@supervisor_blueprint.route(
    "/supervisor/api/services/<name>/<action>", methods=["POST"]
)
def service_action(name: str, action: str):
    try:
        client.service_action(name, action)
        return jsonify({"status": "ok"}), 200
    except client.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return jsonify({"error": "Supervisor action failed", "details": str(e)}), 502


@supervisor_blueprint.route("/supervisor/api/services/restart-all", methods=["POST"])
def restart_all():
    try:
        client.restart_all()
        return jsonify({"status": "ok"}), 200
    except client.SupervisorError as e:
        return jsonify({"error": e.message, "details": e.details}), e.status_code
    except Exception as e:
        return jsonify({"error": "Supervisor action failed", "details": str(e)}), 502
