______________________________________________________________________

## trigger: always_on

# Examples Workflow Rules

These rules define the operational contract for runnable scenarios under
`examples/`.

## 1. Tutorial Mapping and Compose Contract

- **Tutorial Mapping**: Each tutorial in `docs/src/tutorials/` must map to one
  directory in `examples/<tutorial-slug>/`.
- **Project Naming Contract**: Compose projects in `examples/` must use unique
  names prefixed with `citm-examples-`.
- **Network Naming Contract**: All example stacks must use the Docker network
  name `my-citm-network` and treat it as an external network.
- **Build Source Exception**: As an explicit examples-only exception, CITM
  services in `examples/` must be built from the repository root `Dockerfile`
  (Compose `build` with root context), not pulled from `fardjad/citm:latest`.
- **Tutorial Runtime Image Contract**: Tutorials in `docs/src/tutorials/` must
  use `image: fardjad/citm:latest` for end-user runtime examples.
- **Self-Contained Examples**: Each tutorial example directory must include all
  files required to run that scenario locally (Compose files, Caddy
  configuration, cert output directory placeholders, and helper automation).

## 2. Justfile Contract Per Example

- **Required Location**: Every tutorial example directory
  (`examples/<tutorial-slug>/`) must contain a local `justfile`.
- **Required Import**: Example `justfile`s must import the shared helper module
  at `examples/.just/justfile`.
- **Required Recipes**: Each example `justfile` must provide at least:
  - `up`
  - `down`
- **Certificate Generation Scope**: Certificate generation recipes (for example
  `_generate-certs`) must remain private shared helpers, not public example
  recipes.
- **Generation Workflow**: Example certificate generation must follow the
  CFSSL-based workflow documented in `docs/src/how-to/create-dev-root-ca.md` (CA
  CSR JSON + `cfssl genkey -initca` + `cfssljson`).
- **CA Extension Requirements**: Generated Root CA certificates for examples
  must include CA-specific X.509 extensions, including `basicConstraints` with
  `CA:TRUE` and `keyUsage` with certificate-signing capability.
- **Shared Helper Invocation**: Example `justfile`s should invoke shared private
  module recipes directly in dependencies (for example, `_ensure-certs` and
  `_ensure-network`, and `_clear-project-containers`) instead of defining local
  wrapper recipes.
- **Fixed Network Scope**: `_ensure-network` should be a shared no-argument
  helper with a fixed ensure scope for `my-citm-network`.
- **Fixed Cleanup Scope**: `_clear-project-containers` should be a shared
  no-argument helper with a fixed cleanup scope for `citm-examples-*` projects.
- **Cleanup Side Effect**: `_clear-project-containers` must remove the
  `my-citm-network` Docker network after container cleanup so the next example
  run can recreate it with consistent metadata.
- **Project Cleanup Requirement**: Before running `up`, example workflows must
  remove all existing containers whose Compose project name starts with
  `citm-examples-`.
- **Network Ensure Requirement**: Before running `up`, example workflows must
  ensure the external network `my-citm-network` exists.
- **Up Command Requirements**: Startup commands must use
  `docker compose up -d --wait --pull always --build --force-recreate`.
- **Per-Directory Startup Requirement**: For multi-stack examples, run
  `docker compose up` from each stack directory separately. Do not merge stack
  files into a single multi-`-f` `up` command, because it can change relative
  path resolution.
- **Smoke Check Behavior**: If an example provides a `smoke` recipe, it must
  fail when status codes do not match expected values. Use shared status check
  helpers (for example, `_check-status`) with explicit expected HTTP codes.
- **Practical Helpers**: Add any additional recipes needed for operational
  convenience and repeatable testing (for example: `restart`, `ps`, `logs`,
  `smoke`).

## 3. Shared Module Contract

- **Module Location**: Shared private helper recipes for examples must be
  implemented in `examples/.just/justfile`.
- **Private Recipe Naming**: Shared helper recipes must remain private recipes
  (prefixed with `_`) and must not be exposed as public operational entrypoints.

## 4. No Root Aggregator Justfile

- **Prohibited File**: `examples/justfile` must not be introduced.
- **Execution Model**: Operations must be executed from each example directory's
  local `justfile`, not through an umbrella wrapper.
