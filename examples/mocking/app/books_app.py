from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BOOKS = [
    {"id": 1, "title": "The Pragmatic Programmer"},
    {"id": 2, "title": "Clean Code"},
]


class BooksHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/books":
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')
            return

        body = json.dumps(BOOKS).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", 8000), BooksHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
