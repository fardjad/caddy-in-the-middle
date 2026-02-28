set dotenv-load := true

# show this message
help:
    @just --list

_check-tools *args:
    #!/usr/bin/env bash

    for tool in {{ args }}; do
        if ! command -v "${tool}" &> /dev/null; then
            echo "Error: ${tool} is not in your PATH. Make sure it's installed and is in your PATH and try again". >&2
            exit 1
        fi
    done

_dockerfmt *args: (_check-tools "dockerfmt")
    #!/usr/bin/env bash

    set -euo pipefail

    for f in $(find . -maxdepth 5 -type f -name 'Dockerfile'); do
        dockerfmt "${f}" {{ args }}
    done

format-justfiles *args:
    #!/usr/bin/env bash

    set -euo pipefail

    for f in $(find . -maxdepth 5 -type f -name 'justfile'); do
        just --justfile "$f" --unstable --fmt {{ args }}
    done

check-justfiles:
    @just format-justfiles --check

check-dockerfiles:
    @just _dockerfmt --check

format-dockerfiles:
    @just _dockerfmt --write

check-composefiles *args: (_check-tools "node" "dclint")
    #!/usr/bin/env bash

    set -euo pipefail

    for f in $(find . -maxdepth 5 -type f -name 'compose.yml'); do
        dclint "${f}" {{ args }} | (grep -Ev '^$' || true)
    done

format-composefiles:
    @just check-composefiles --fix

check-caddyfiles *args: (_check-tools "caddy")
    #!/usr/bin/env bash

    set -euo pipefail

    for f in $(find . -maxdepth 5 -type f -iname '*Caddyfile'); do
        caddy fmt {{ args }} "${f}" > /dev/null
    done

format-caddyfiles:
    @just check-caddyfiles --overwrite

format-python *args: (_check-tools "black")
    #!/usr/bin/env bash

    set -euo pipefail
    black -q {{ args }} .

check-python:
    @just format-python --check

check-shellscripts: (_check-tools "shfmt")
    #!/usr/bin/env bash

    set -euo pipefail
    shfmt -s -d .

format-shellscripts: (_check-tools "shfmt")
    #!/usr/bin/env bash

    set -euo pipefail
    shfmt -s -w .

format-markdown *args: (_check-tools "uv")
    #!/usr/bin/env bash

    set -euo pipefail
    uv tool run mdformat --wrap 80 {{ args }} $(find . -maxdepth 5 -type f -name '*.md' -not -path "*/.venv/*" -not -path "*/.git/*" -not -path "*/site/*" -not -path "*/docs/site/*")

check-markdown:
    @just format-markdown --check

check: check-justfiles check-dockerfiles check-composefiles check-caddyfiles check-python check-shellscripts check-markdown

format: format-justfiles format-dockerfiles format-composefiles format-caddyfiles format-python format-shellscripts format-markdown

test:
    #!/usr/bin/env bash
    set -euo pipefail

    echo "Running citm-utils tests"
    (
        cd citm-utils
        uv run pytest
    )

    echo "Running mitmproxy script tests"
    (
        cd mitmproxy
        just test
    )

    example_dirs=$(find examples -mindepth 1 -maxdepth 1 -type d ! -name '.just' | sort)

    if [[ -z "$example_dirs" ]]; then
        echo "No example directories found under examples/" >&2
        exit 1
    fi

    while IFS= read -r example_dir; do
        if [[ ! -f "${example_dir}/justfile" ]]; then
            echo "Missing justfile in ${example_dir}" >&2
            exit 1
        fi

        echo "Running example workflow in ${example_dir}"
        (
            cd "${example_dir}"
            just up
            just smoke
            just down
        )
    done <<< "$example_dirs"

install-git-hooks: (_check-tools "uv")
    #!/usr/bin/env bash

    set -euo pipefail
    uv tool run pre-commit install

publish-testcontainers-python:
    #!/usr/bin/env bash

    set -euo pipefail

    cd testcontainers/python
    just publish

publish-testcontainers-dotnet:
    #!/usr/bin/env bash

    set -euo pipefail

    cd testcontainers/dotnet
    just publish

upgrade-python-deps *args:
    #!/usr/bin/env bash
    set -euo pipefail

    for f in $(find . -maxdepth 5 -type f -name 'pyproject.toml'); do
        dir=$(dirname "$f")
        echo "Processing $dir..."
        python3 hack/upgrade_deps.py "$dir" {{ args }}
    done

publish-testcontainers: publish-testcontainers-python publish-testcontainers-dotnet

docs-serve: (_check-tools "uv")
    #!/usr/bin/env bash
    set -euo pipefail
    cd docs
    uv run zensical serve

docs-build: (_check-tools "uv")
    #!/usr/bin/env bash
    set -euo pipefail
    cd docs
    uv run zensical build

build:
    #!/usr/bin/env bash
    set -euo pipefail
    docker build -t "fardjad/citm:$(cat VERSION.txt)" .
