#!/usr/bin/env python3
"""
Release utility script for make-api-request-py

Usage:
    python scripts/release.py patch    # 1.0.0 -> 1.0.1
    python scripts/release.py minor    # 1.0.0 -> 1.1.0
    python scripts/release.py major    # 1.0.0 -> 2.0.0
    python scripts/release.py 1.2.3    # Set specific version
"""

import re
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, check: bool = True) -> subprocess.CompletedProcess:
    """Run a shell command and return the result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        sys.exit(1)
    return result


def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        print("Error: pyproject.toml not found")
        sys.exit(1)

    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)

    return match.group(1)


def bump_version(current: str, bump_type: str) -> str:
    """Bump version based on type (patch, minor, major)."""
    parts = [int(x) for x in re.split(r"[.-]", current)[:3]]

    if bump_type == "patch":
        parts[2] += 1
    elif bump_type == "minor":
        parts[1] += 1
        parts[2] = 0
    elif bump_type == "major":
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    else:
        # Assume it's a specific version
        if not re.match(r"^\d+\.\d+\.\d+(?:-rc\.\d+)?$", bump_type):
            print(f"Error: Invalid version format: {bump_type}")
            sys.exit(1)
        return bump_type

    return ".".join(map(str, parts))


def update_version_in_pyproject(new_version: str):
    """Update version in pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    content = pyproject_path.read_text()

    # Replace only the main package version line in [tool.poetry] section
    new_content = re.sub(
        r'(\[tool\.poetry\].*?version\s*=\s*)"[^"]+"',
        rf'\1"{new_version}"',
        content,
        flags=re.DOTALL,
    )

    pyproject_path.write_text(new_content)
    print(f"Updated pyproject.toml version to {new_version}")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    bump_type = sys.argv[1]

    # Check if we're in a git repository
    result = run_command("git status --porcelain", check=False)
    if result.returncode != 0:
        print("Error: Not in a git repository")
        sys.exit(1)

    # Check for uncommitted changes
    if result.stdout.strip():
        print("Error: You have uncommitted changes. Please commit or stash them first.")
        print("Uncommitted files:")
        print(result.stdout)
        sys.exit(1)

    # Get current version
    current_version = get_current_version()
    print(f"Current version: {current_version}")

    # Calculate new version
    new_version = bump_version(current_version, bump_type)
    print(f"New version: {new_version}")

    # Confirm with user
    confirm = input(f"Release version {new_version}? (y/N): ")
    if confirm.lower() != "y":
        print("Release cancelled")
        sys.exit(0)

    # Update version in pyproject.toml
    update_version_in_pyproject(new_version)

    # Run tests to make sure everything works
    print("Running tests...")
    run_command("poetry run pytest --tb=short -q")

    # Commit version bump
    run_command("git add pyproject.toml")
    run_command(f'git commit -m "Bump version to {new_version}"')

    # Create and push tag
    tag_name = f"v{new_version}"
    run_command(f'git tag -a {tag_name} -m "Release {new_version}"')
    run_command("git push origin main")
    run_command(f"git push origin {tag_name}")

    print(f"✅ Successfully created release {new_version}")
    print("🚀 GitHub Actions will now build and publish to PyPI")
    print(
        f"📦 Check the release at: https://github.com/sideko-inc/make-api-request-py/releases/tag/{tag_name}"
    )


if __name__ == "__main__":
    main()
