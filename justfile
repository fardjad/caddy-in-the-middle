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

check: check-justfiles check-dockerfiles check-composefiles check-caddyfiles check-python check-shellscripts

format: format-justfiles format-dockerfiles format-composefiles format-caddyfiles format-python format-shellscripts

test: check

publish-testcontainers-python:
    #!/usr/bin/env bash

    set -euo pipefail

    cd testcontainers/python
    uv build
    uv publish

publish-testcontainers-dotnet:
    #!/usr/bin/env bash

    set -euo pipefail

    cd testcontainers/dotnet
    dotnet pack Testcontainers.CaddyInTheMiddle/Testcontainers.CaddyInTheMiddle.csproj -c Release
    dotnet nuget push Testcontainers.CaddyInTheMiddle/bin/Release/*.nupkg --source https://api.nuget.org/v3/index.json --skip-duplicate

publish-testcontainers: publish-testcontainers-python publish-testcontainers-dotnet
