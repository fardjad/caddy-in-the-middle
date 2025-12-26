import logging
from mitmproxy import http

logger = logging.getLogger(__name__)

class RequestLogger:
    def request(self, flow: http.HTTPFlow) -> None:
        logger.info(f"Request: {flow.request.method} {flow.request.pretty_url}")

    def response(self, flow: http.HTTPFlow) -> None:
        logger.info(f"Response: {flow.response.status_code} {flow.request.pretty_url}")

addons = [RequestLogger()]
