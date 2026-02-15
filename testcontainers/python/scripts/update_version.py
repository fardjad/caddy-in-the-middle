import sys
from pathlib import Path

try:
    import tomlkit
except ImportError:
    print(
        "Error: tomlkit is required. Run with `uv run --with tomlkit python scripts/update_version.py`"
    )
    sys.exit(1)


def update_version():
    script_dir = Path(__file__).parent
    python_root = script_dir.parent

    version_py_file = python_root / "caddy_in_the_middle" / "version.py"
    pyproject_file = python_root / "pyproject.toml"

    # Source of truth for the version
    version_file = python_root.parent.parent / "VERSION.txt"

    print(f"Reading version from {version_file}")
    if not version_file.exists():
        print(f"Error: Could not find VERSION.txt at {version_file}")
        return

    version = version_file.read_text().strip()
    print(f"Detected version: {version}")

    print(f"Updating {pyproject_file}")
    with open(pyproject_file, "r") as f:
        doc = tomlkit.parse(f.read())

    if "project" in doc and "version" in doc["project"]:
        doc["project"]["version"] = version
        with open(pyproject_file, "w") as f:
            f.write(tomlkit.dumps(doc))
    else:
        print("Error: Could not find [project] version in pyproject.toml")

    print(f"Updating {version_py_file}")
    version_py_file.write_text(f'__version__ = "{version}"\n')

    print("Version synchronization complete.")


if __name__ == "__main__":
    update_version()
