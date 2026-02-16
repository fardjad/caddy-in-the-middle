#!/usr/bin/env python3
import sys
import argparse
import subprocess
import json
import tomllib
from pathlib import Path


def run_uv_add(package, version, group=None):
    # Construct the package requirement with >= constraint for the latest version
    package_req = f"{package}>={version}"
    cmd = ["uv", "add", package_req]
    if group:
        cmd.extend(["--group", group])
    print(f"  Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def normalize_name(name):
    return name.lower().replace("_", "-")


def main():
    parser = argparse.ArgumentParser(
        description="Upgrade python dependencies in pyproject.toml"
    )
    parser.add_argument("directory", help="Directory containing pyproject.toml")
    args = parser.parse_args()

    project_dir = Path(args.directory).resolve()
    pyproject_path = project_dir / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Error: {pyproject_path} not found")
        sys.exit(1)

    print(f"Upgrading dependencies in {project_dir}...")

    # Change working directory to project directory for uv commands
    try:
        import os

        os.chdir(project_dir)
    except FileNotFoundError:
        print(f"Error: Could not change directory to {project_dir}")
        sys.exit(1)

    # Ensure environment is synced
    print("  Syncing environment...")
    subprocess.run(
        ["uv", "sync"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Get outdated packages
    print("  Checking for outdated packages...")
    result = subprocess.run(
        ["uv", "pip", "list", "--outdated", "--format=json"],
        capture_output=True,
        text=True,
        check=True,
    )

    try:
        outdated_packages = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("  No outdated packages found or invalid JSON.")
        outdated_packages = []

    if not outdated_packages:
        print("  All dependencies are up to date.")
        return

    # Create a map of normalized package name to latest version
    outdated_map = {
        normalize_name(pkg["name"]): pkg["latest_version"] for pkg in outdated_packages
    }

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    # Upgrade main dependencies
    if "project" in data and "dependencies" in data["project"]:
        for dep in data["project"]["dependencies"]:
            # Extract package name (ignoring version specifiers and extras)
            package_name = (
                dep.split(">=")[0]
                .split("==")[0]
                .split("<")[0]
                .split("~=")[0]
                .split(";")[0]
                .strip()
            )
            # Handle extras like 'package[extra]' - we need the base name for lookup
            base_name = package_name.split("[")[0]

            normalized_base = normalize_name(base_name)

            if normalized_base in outdated_map:
                latest_version = outdated_map[normalized_base]
                print(f"  Upgrading {package_name} to >={latest_version}...")
                # We use the original package_name (with extras if any) but new version constraint
                # If original was 'flask[async]', we run 'uv add flask[async]>=3.0'
                run_uv_add(package_name, latest_version)

    # Upgrade dependency groups
    if "dependency-groups" in data:
        for group, deps in data["dependency-groups"].items():
            for dep in deps:
                package_name = (
                    dep.split(">=")[0]
                    .split("==")[0]
                    .split("<")[0]
                    .split("~=")[0]
                    .split(";")[0]
                    .strip()
                )
                base_name = package_name.split("[")[0]
                normalized_base = normalize_name(base_name)

                if normalized_base in outdated_map:
                    latest_version = outdated_map[normalized_base]
                    print(
                        f"  Upgrading {package_name} (group: {group}) to >={latest_version}..."
                    )
                    run_uv_add(package_name, latest_version, group=group)

    # Upgrade the lockfile
    print("  Upgrading lockfile...")
    subprocess.run(["uv", "lock", "--upgrade"], check=True)

    print(f"Done upgrading dependencies in {project_dir}")


if __name__ == "__main__":
    main()
