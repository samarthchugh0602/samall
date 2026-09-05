"""
samall — installs every library Sam (sam3360) has ever published.

This package does nothing on its own. Its only job is to depend on all
of Sam's other PyPI packages so that `pip install samall` pulls all of
them down in one shot.

    samall             show installed versions of everything
    samall --list      list every package samall includes
    samall --update    upgrade every included package, and samall itself
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - Python <3.8 fallback
    import importlib_metadata  # type: ignore

from . import __version__

# Kept in sync with libraries.txt and [project.dependencies] in
# pyproject.toml. To add a new library: edit libraries.txt, then run
# `python scripts/sync_deps.py`.
LIBRARIES = [
    "replico",
    "vibeUI",
    "sam3360",
    "whyfail",
    "secretshield",
    "shrug-it",
    "memobox",
    "pyproject-lens",
    "neonprint",
    "cortexa",
    "formula-math",
]

SELF_PACKAGE = "samall"


def _normalize(name: str) -> str:
    # PEP 503 normalization — matches how pip/importlib.metadata name dists.
    return re.sub(r"[-_.]+", "-", name).lower()


def _version(dist_name: str) -> str:
    try:
        return importlib_metadata.version(_normalize(dist_name))
    except importlib_metadata.PackageNotFoundError:
        return "not installed"


def cmd_status() -> int:
    print("samall — every library sam3360 has ever published\n")
    width = max(len(name) for name in LIBRARIES)
    for name in LIBRARIES:
        print(f"  {name.ljust(width)}  {_version(name)}")
    print(f"\n{len(LIBRARIES)} libraries installed. samall itself does nothing else.")
    print("Run `samall --update` to check for and install newer versions.")
    return 0


def cmd_list() -> int:
    print(f"samall v{__version__} includes {len(LIBRARIES)} packages:\n")
    for name in LIBRARIES:
        print(f"  {name}")
    return 0


def cmd_update() -> int:
    # Upgrade every included library, plus samall itself, in one pip call —
    # a single resolver pass avoids the packages fighting each other over
    # shared sub-dependencies.
    targets = LIBRARIES + [SELF_PACKAGE]
    print(f"Checking for updates to {len(targets)} packages (including samall itself)...\n")

    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *targets]
    result = subprocess.run(cmd)

    if result.returncode != 0:
        print("\nUpdate failed — see pip output above.", file=sys.stderr)
        return result.returncode

    print("\nAll packages are up to date:\n")
    width = max(len(name) for name in targets)
    for name in targets:
        print(f"  {name.ljust(width)}  {_version(name)}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="samall",
        description="Installs and manages every library sam3360 has ever published.",
    )
    parser.add_argument(
        "--version", action="version", version=f"samall {__version__}"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--list", action="store_true", help="list every package samall includes"
    )
    group.add_argument(
        "--update",
        action="store_true",
        help="upgrade every included package (and samall itself) via pip",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    if args.list:
        return cmd_list()
    if args.update:
        return cmd_update()
    return cmd_status()


if __name__ == "__main__":
    sys.exit(main())
