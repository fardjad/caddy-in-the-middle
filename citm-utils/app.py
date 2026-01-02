from flask import Flask, send_file, request, jsonify
import subprocess
import os
import socket

app = Flask(__name__)


@app.route("/", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"])
def get_info():
    request_data = {
        "method": request.method,
        "url": request.url,
        "host": request.host,
        "remote_addr": request.remote_addr,
        "headers": dict(request.headers),
        "args": request.args.to_dict(flat=False),
        "cookies": request.cookies,
    }
    return (
        jsonify({"hostname": socket.gethostname(), "request_data": request_data}),
        200,
    )


@app.route("/har", methods=["GET"])
def get_har():
    if not os.path.exists("/mitm-dump/dump.flow"):
        return jsonify({"error": "Flow file not found"}), 404

    subprocess.call(
        [
            "mitmdump",
            "-nr",
            "/mitm-dump/dump.flow",
            "--set",
            "hardump=/mitm-dump/dump.har",
        ],
    )

    return send_file("/mitm-dump/dump.har", mimetype="application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
