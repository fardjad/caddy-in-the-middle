import pip_system_certs.wrapt_requests
pip_system_certs.wrapt_requests.inject_truststore()

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def get_info():
    return (
        jsonify(
            {"status": "ok"}
        ),
        200,
    )
