"""
Increment the VERSION file by 1 and print the new version.
Usage: python scripts/bump_version.py
"""
from pathlib import Path

VERSION_FILE = Path(__file__).parent.parent / "VERSION"


def bump() -> int:
    current = int(VERSION_FILE.read_text().strip()) if VERSION_FILE.exists() else 0
    new_version = current + 1
    VERSION_FILE.write_text(f"{new_version}\n")
    print(f"Version bumped to V{new_version}")
    return new_version


if __name__ == "__main__":
    bump()
