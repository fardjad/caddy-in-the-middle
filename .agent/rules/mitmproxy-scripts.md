______________________________________________________________________

## trigger: always_on

# Mitmproxy Scripts Rules

These rules define how standalone mitmproxy addon scripts are structured and
tested in this repository.

## 1. Project Boundary

- The `mitmproxy/` directory is a standalone Python project.
- Do not place mitmproxy addon tests inside `citm-utils/`.
- Do not couple mitmproxy addon changes to `citm-utils` refactors unless
  explicitly requested.

## 2. Test Location

- Keep addon tests in the module they validate.
- Do not use a separate top-level `mitmproxy/tests/` directory for addon tests.
- Configure pytest discovery in `mitmproxy/pyproject.toml` to target module
  paths (for example, `rewrite_host`).

## 3. Rewrite-Host Integration Test Standard

- Use real upstream `mitmproxy` flow/request types for integration tests.
- Build test flows with `mitmproxy.connection.Client`,
  `mitmproxy.connection.Server`, `mitmproxy.http.HTTPFlow`, and
  `mitmproxy.http.Request.make`.
- Cover protocol behavior for `HTTP/1.1`, `HTTP/2.0`, and `HTTP/3`.
- Assert protocol-aware host semantics (`Host` for HTTP/1.1 and authority for
  HTTP/2+).
- Assert malformed `X-MITM-To` handling blocks the flow (`flow.kill()`), marks
  with `:warning:`, sets a warning comment, and emits an error log.

## 4. Runtime Entry Point Compatibility

- Keep `/rewrite-host.py` as the script entrypoint loaded by mitmproxy.
- Prefer module implementation plus a thin entrypoint shim.
- If shim imports project modules, ensure Dockerfile copies required module
  directories into the runtime image.

## 5. Command Workflow

- `mitmproxy/justfile` must expose a `test` recipe that runs `uv run pytest`.
- Root `just test` must run mitmproxy tests from the `mitmproxy/` working
  directory.
