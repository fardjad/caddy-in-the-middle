FROM python:3

RUN <<EOF
apt-get update -y
apt-get install ca-certificates
EOF

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN mkdir /app
WORKDIR /app
COPY .python-version uv.lock pyproject.toml app.py ./

RUN uv sync

COPY --chown=root:root --chmod=755 <<EOF /entrypoint.sh
#!/usr/bin/env bash

set -euo pipefail

install -m 644 -o root -g root "/certs/rootCA.pem" /usr/local/share/ca-certificates/citm-root-ca.crt
update-ca-certificates

exec uv run gunicorn -w 4 -b 0.0.0.0:5031 app:app
EOF

ENTRYPOINT [ "/entrypoint.sh" ]
