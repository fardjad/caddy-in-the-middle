import pip_system_certs.wrapt_requests
pip_system_certs.wrapt_requests.inject_truststore()

from flask import Flask, jsonify
import requests

app = Flask(__name__)


@app.route("/", methods=["GET"])
def get_info():
    service2_info = requests.get("https://service2.internal").json()

    return (
        jsonify(
            {"service1_info": {"name": "service1"}, "service2_info": service2_info}
        ),
        200,
    )
