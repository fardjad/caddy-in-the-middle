______________________________________________________________________

## trigger: always_on

# CITM Utils Testing Rules

These rules define required constraints for testing `citm-utils`.

## 1. Test Placement and Style

- Tests for `citm-utils` must be co-located with the modules they validate.
- A central `citm-utils/tests/` directory must not be introduced.
- New tests must use pytest function and fixture style.
- Test names must describe user-visible or contract-visible behavior.

## 2. Testability-First Design Constraints

- When code is hard to test, introduce small seams before considering structural
  redesigns.
- Test seams must default to current production behavior.
- Existing public routes, status codes, and public function names must remain
  stable unless a requested change requires a contract change.

## 3. Behavior Coverage Priorities

- For HTTP-facing behavior, tests must cover both success and error responses
  with explicit status-code assertions.
- For subprocess, lock, or external-system boundaries, tests must cover conflict
  and failure paths and assert caller-visible error mapping.
- For discovery or resolution logic, tests must cover normalization, filtering,
  and fallback behavior.
- For client and wrapper components, tests must cover stateful actions and
  downstream error mapping.

## 4. Scope Defaults for Hard-to-Test Paths

- Heavy lifecycle and socket-wiring tests should be deferred unless explicitly
  requested.
- Isolated behavior tests for core logic should be implemented before
  integration-style runtime wiring tests.
