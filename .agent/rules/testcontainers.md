______________________________________________________________________

## trigger: always_on

# Testcontainers Implementation Rules

The CITM project includes native integration libraries for various languages
(Python, Java, Go, .NET, etc.) located in the `testcontainers/` directory.

## 1. The Specification is the Single Source of Truth

- **Strict Adherence**: Modifying, creating, or interacting with a testcontainer
  implementation requires locating, reading, and strictly adhering to the
  `testcontainers/specification.md` document.
- **No Duplicate Rules**: To prevent drift, specific configuration rules (e.g.,
  ports, wait strategies, builder methods) are deliberately excluded from this
  rule file. The `specification.md` is the sole authoritative document.

## 2. Updating the Specification

- **Specification First**: If a new capability is added to the CITM container
  that requires changes to how the testcontainer clients interact with it, the
  `testcontainers/specification.md` document **MUST** be updated first.
- **Client Synchronization**: All language implementations must subsequently be
  updated to remain compliant with the modified specification.
