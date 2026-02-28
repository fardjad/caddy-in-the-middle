______________________________________________________________________

## trigger: always_on

# Mitmproxy Scripts Rules

These rules define required constraints for standalone mitmproxy addon scripts.

## 1. Project Boundary

- The `mitmproxy/` directory is a standalone Python project.
- Mitmproxy addon tests must not be placed inside `citm-utils/`.
- Mitmproxy addon changes must not be coupled to `citm-utils` refactors unless
  explicitly requested.

## 2. Test Location

- Addon tests must be co-located with the module they validate.
- A top-level `mitmproxy/tests/` directory must not be introduced for addon
  tests.
- Pytest discovery in `mitmproxy/pyproject.toml` must target addon module paths.

## 3. Addon Integration Test Standards

- Integration tests must use upstream `mitmproxy` flow and request types.
- Test flows must be built with `mitmproxy.connection.Client`,
  `mitmproxy.connection.Server`, `mitmproxy.http.HTTPFlow`, and
  `mitmproxy.http.Request.make`.
- Assertions must focus on observable behavior, including response shape, flow
  mutations, and pass-through behavior.
- Integration tests must include protocol-specific scenarios when behavior
  depends on protocol semantics. Use `HTTP/1.1`, `HTTP/2.0`, and `HTTP/3`.
- When addons transform host, authority, or response headers, tests must assert
  protocol-correct behavior for HTTP/1.x and HTTP/2+.
- When addons consume control headers or dynamic input, tests must include
  malformed-input scenarios and assert safe operator-visible outcomes.
- For file or template-driven addons, fixtures must be co-located with the addon
  module and tests must cover matching, pass-through, rendering, reloading, and
  upstream fetch behavior when those features exist.
- When addons emit headers, tests must assert protocol-safe behavior for HTTP/2+
  constraints.

## 4. Runtime Entry Point Compatibility

- Keep existing script entrypoints loaded by mitmproxy stable.
- Prefer module implementations with thin entrypoint shims.
- If a shim imports project modules, Dockerfile must copy those module
  directories into the runtime image.

## 5. Command Workflow

- `mitmproxy/justfile` must provide a `test` recipe that runs `uv run pytest`.
- Root `just test` must execute mitmproxy tests from the `mitmproxy/` working
  directory.
