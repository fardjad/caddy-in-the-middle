from flask import Flask, send_file, jsonify
import subprocess
import os

app = Flask(__name__)

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
