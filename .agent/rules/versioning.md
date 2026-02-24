______________________________________________________________________

## trigger: always_on

# Versioning Rules

These rules define how versions are managed and synchronized across the
`Caddy in the Middle` (CITM) project and its associated testcontainer libraries.

## 1. The Source of Truth

- **`VERSION.txt` File**: The `VERSION.txt` file located at the root of the
  repository is the definitive and single source of truth for the project's
  current version.
- **Tag and Package Matching**: The version defined in `VERSION.txt` dictates
  both the Docker container tag and the published package version for all
  testcontainer library implementations.

## 2. Language-Specific Syncing

The testcontainers libraries must use the version from `VERSION.txt` as their
package version. The mechanism for this differs by language:

- **.NET Implementation**: The testcontainer library automatically reads the
  version from `VERSION.txt` during the build process. No manual package version
  bumping is needed prior to publishing.
- **Python Implementation**: The Python testcontainer requires a manual
  synchronization step before a release. The
  `testcontainers/python/scripts/update_version.py` script **MUST** be run to
  sync the `pyproject.toml` and `version.py` files with the root `VERSION.txt`.
