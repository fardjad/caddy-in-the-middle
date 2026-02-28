______________________________________________________________________

## trigger: always_on

# CITM Utils Testing Rules

These rules define how `citm-utils` code should be structured and tested to keep
tests readable, behavior-focused, and easy to maintain.

## 1. Test Placement and Style

- **Co-located Tests Required**: Tests for `citm-utils` MUST live next to the
  modules they validate (for example `citm-utils/supervisor/test_client.py`). Do
  not create a central `citm-utils/tests/` directory.
- **Pytest-First Style**: New `citm-utils` tests MUST use pytest function and
  fixture style. Prefer direct assertions over class-heavy patterns.
- **Behavior-Oriented Names**: Test names should describe user-visible or
  contract-visible behavior, not internal implementation details.

## 2. Testability-First Design Constraints

- **Small Seams over Redesigns**: When code is hard to test, prefer minimal
  dependency injection seams (for example optional callable parameters) instead
  of major architecture changes.
- **Runtime Defaults Preserved**: Injected test seams MUST default to current
  production behavior so runtime wiring stays unchanged.
- **Public Contract Stability**: Keep existing HTTP routes, status codes, and
  public function names stable unless a requested feature explicitly changes
  them.

## 3. Behavior Coverage Priorities

- **`app.py`**: Cover `/` and `/health` behavior, including healthy and
  unhealthy response paths.
- **`mitmproxy`**: Cover HAR generation success, lock conflict behavior, and
  subprocess failure mapping.
- **`service_discovery`**: Cover discovery filtering/normalization and DNS
  resolver behavior (local match, upstream fallback, SERVFAIL/FORMERR cases).
- **`supervisor`**: Cover client state/action behavior and route-level error
  mapping.

## 4. Scope Defaults for Hard-to-Test Paths

- **Defer Runtime Wiring by Default**: Heavy lifecycle or socket wiring tests
  (for example `dns_forwarder.main`) should be deferred unless explicitly
  requested.
- **Prioritize Core Logic**: Prefer isolated behavior tests of resolver/client
  logic before adding integration-style runtime tests.
