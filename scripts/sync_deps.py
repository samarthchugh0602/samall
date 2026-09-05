#!/usr/bin/env python3
"""
Sync libraries.txt -> pyproject.toml [project.dependencies] and
src/samall/cli.py LIBRARIES.

This is the reliable, no-network way to add a newly published library:

    1. Add the package name to libraries.txt
    2. python scripts/sync_deps.py
    3. bump the version in pyproject.toml
    4. python -m build && twine upload dist/*

(See scripts/check_pypi_profile.py for a best-effort helper that suggests
new entries by checking your PyPI profile — it can't run unattended because
PyPI's profile pages sit behind a browser/JS bot-check, so it's a "look what
I found, go add it yourself" tool, not an auto-writer.)
"""

from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBRARIES_TXT = ROOT / "libraries.txt"
PYPROJECT = ROOT / "pyproject.toml"
CLI_FILE = ROOT / "src" / "samall" / "cli.py"


def read_libraries() -> list[str]:
    names = []
    for line in LIBRARIES_TXT.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        names.append(line)
    if not names:
        print("libraries.txt is empty — refusing to wipe dependencies.", file=sys.stderr)
        sys.exit(1)
    return names


def write_pyproject_deps(names: list[str]) -> None:
    text = PYPROJECT.read_text()
    block = "dependencies = [\n" + "".join(f'    "{n}",\n' for n in names) + "]"
    new_text, count = re.subn(r"dependencies = \[.*?\]", block, text, count=1, flags=re.DOTALL)
    if count == 0:
        print("Could not find a dependencies = [...] block in pyproject.toml", file=sys.stderr)
        sys.exit(1)
    PYPROJECT.write_text(new_text)


def write_cli_libraries(names: list[str]) -> None:
    text = CLI_FILE.read_text()
    block = "LIBRARIES = [\n" + "".join(f'    "{n}",\n' for n in names) + "]"
    new_text, count = re.subn(r"LIBRARIES = \[.*?\]", block, text, count=1, flags=re.DOTALL)
    if count == 0:
        print("Could not find a LIBRARIES = [...] block in cli.py", file=sys.stderr)
        sys.exit(1)
    CLI_FILE.write_text(new_text)


def main() -> int:
    names = read_libraries()
    write_pyproject_deps(names)
    write_cli_libraries(names)
    print(f"Synced {len(names)} libraries into pyproject.toml and cli.py:")
    for n in names:
        print(f"  - {n}")
    print("\nNow bump the version in pyproject.toml, then build + upload to publish.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
