#!/usr/bin/env bash

set -euo pipefail

export PATH="/proxy-lens/server/.venv/bin:${PATH}"

/proxy-lens/bin/set-ui-api-base-url.sh /api

# Initialize the SQLite schema once before the worker pool starts.
uv run python - <<'PY'
import os
from pathlib import Path

from proxylens_server.bootstrap import create_container
from proxylens_server.config import ServerConfig

container = create_container(
    ServerConfig(data_dir=Path(os.environ["PROXYLENS_SERVER_DATA_DIR"]).resolve())
)
container.close()
PY

exec uv run gunicorn 'proxylens_server.app:create_app()' \
	--bind "0.0.0.0:${PROXYLENS_SERVER_PORT}" \
	--worker-class uvicorn.workers.UvicornWorker \
	--workers 4
