______________________________________________________________________

## trigger: always_on

# Development Workflow Rules

These rules define the required project tooling interactions for local
development and CI.

## 1. Justfile is the Command Runner

- **Central Command Runner**: The `justfile` located at the root of the project
  is the definitive registry for operational tasks.
- **No Ad-hoc Commands**: Predefined `just` recipes take priority over executing
  manual shell commands.

## 2. Core Just Targets

Code changes and commits require the use of the following targets:

- **Formatting**: `just format` - Automatically formats the codebase
  (Dockerfiles, Justfiles, Markdown, Shell scripts, Python code). This must be
  run before verifying changes.
- **Linting / Syntax**: `just check` - Runs the linting and syntax validations.
  The `just check` target MUST pass before concluding a task.
- **Testing**: `just test` - Runs the test suite (which includes checks).
