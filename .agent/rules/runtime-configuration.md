______________________________________________________________________

## trigger: always_on

# Runtime Configuration Rules

These rules define the required source of truth and integration workflow for
runtime ports and service enablement flags.

## 1. Port Source of Truth

- Runtime port defaults are defined exclusively in
  `hack/update_default_ports.py`.
- New runtime ports must be added to the `PORTS` table in
  `hack/update_default_ports.py`.
- Port defaults must not be hardcoded independently in Dockerfile, docs,
  devcontainer Compose, testcontainers, or runtime scripts when they are part of
  the generated port contract.

## 2. Port Update Workflow

- After adding, removing, or changing a managed port, run
  `just update-default-ports`.
- Generated port blocks in Dockerfile, `.devcontainer/compose.yml`,
  `mitmproxy/start-mitmproxy.sh`, docs, and testcontainer files must be updated
  only through `hack/update_default_ports.py`.
- If a new port must be exposed from the devcontainer service, the generator
  function `render_devcontainer_ports_block()` must be updated so the Compose
  file remains generated rather than manually edited.

## 3. Service Enablement Contract

- Optional supervised services must be gated through `ENABLE_<SERVICE>` style
  environment variables in `supervisor/start-supervisord.sh`.
- The default enabled or disabled behavior for each optional service must be
  explicit in `copy_if_enabled` call sites. Do not rely on implicit defaults
  when a service is intended to be opt-in.
- Runtime configuration documentation must list each supported `ENABLE_*`
  variable and its default behavior.

## 4. Stable Stateful Paths

- Persistent service state must use a stable service-scoped path under
  `/var/lib/<service-name>` unless a different path is required by upstream
  runtime behavior.
- Persistent service state directories should be declared as Docker volumes when
  the data is intended to survive container replacement.
- Transient runtime files must not be promoted to volumes unless they represent
  actual operator-managed or persistent state.
