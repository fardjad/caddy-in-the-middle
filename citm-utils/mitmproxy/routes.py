import subprocess

from flask import Blueprint, jsonify, send_file

from .har import HarGenerationInProgressError, generate_har

mitmproxy_blueprint = Blueprint("mitmproxy", __name__)


@mitmproxy_blueprint.route("/har", methods=["GET"])
def get_har():
    try:
        har_path = generate_har()
    except HarGenerationInProgressError:
        return jsonify({"error": "HAR generation already in progress"}), 409
    except subprocess.CalledProcessError as e:
        return jsonify({"error": "HAR generation failed", "details": str(e)}), 502

    return send_file(har_path, mimetype="application/json")
