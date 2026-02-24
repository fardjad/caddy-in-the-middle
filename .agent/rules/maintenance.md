______________________________________________________________________

## trigger: always_on

# Maintenance Rules

These rules dictate how project dependencies should be upgraded and maintained
across the repository.

## 1. Python Dependencies

- **Automated Upgrade Script**: Upgrading dependencies or performing maintenance
  tasks on Python projects (including `citm-utils` and Python testcontainers)
  REQUIRES the use of the predefined `just` recipe: `just upgrade-python-deps`.
- **Target Detection**: This recipe automatically detects `pyproject.toml` files
  and upgrades the dependencies described within them.
- **No Manual Bumps**: Do not manually bump versions for Python capabilities
  unless absolutely necessary or instructed otherwise.

## 2. .NET Dependencies

- **No Automated Support**: The .NET testcontainer library dependencies lack an
  automated script.
- **CLI Tooling**: Upgrading .NET dependencies requires the use of the standard
  .NET CLI tooling directly within the solution/project paths (e.g.,
  `dotnet list package` and `dotnet add package <PackageName>`).
- **Path Resolution**: The appropriate `.csproj` or `.sln` files must be located
  and used when modifying these dependencies.
