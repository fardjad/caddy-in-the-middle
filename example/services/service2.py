import pip_system_certs.wrapt_requests
pip_system_certs.wrapt_requests.inject_truststore()

from flask import Flask, jsonify
import requests

app = Flask(__name__)


@app.route("/", methods=["GET"])
def get_info():
    service3_info = requests.get("https://service3.internal").json()

    return (
        jsonify(
            {"service2_info": {"name": "service2"}, "service3_info": service3_info}
        ),
        200,
    )
