"""
samall — installs every library Sam (sam3360) has ever published.

Global:
    samall                          show installed versions of everything
    samall --list                   list every package samall includes
    samall --update                 upgrade every included package, and samall
    samall --version                show samall's own version
    samall --outdated               show only packages with a newer release

Per-package (use --<package-name> as a selector):
    samall --secretshield           show details for secretshield
    samall --secretshield --version show secretshield's installed version
    samall --secretshield --update  upgrade only secretshield
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

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
    "devset",
    "surfx",
]

SELF_PACKAGE = "samall"
NOT_INSTALLED = "not installed"


# --------------------------------------------------------------------------
# name handling
# --------------------------------------------------------------------------

def normalize(name: str) -> str:
    """PEP 503 normalization — matches how pip/importlib.metadata name dists."""
    return re.sub(r"[-_.]+", "-", name).lower()


# Lookup so any spelling the user types resolves to the canonical name:
# --secretshield, --SecretShield, --shrug_it, --shrug-it all work.
_CANONICAL = {normalize(n): n for n in LIBRARIES}
_CANONICAL[normalize(SELF_PACKAGE)] = SELF_PACKAGE


def resolve_package(token: str) -> str | None:
    """Return the canonical package name for a user-typed name, or None."""
    return _CANONICAL.get(normalize(token))


# --------------------------------------------------------------------------
# version lookups
# --------------------------------------------------------------------------

def installed_version(name: str) -> str:
    try:
        return importlib_metadata.version(normalize(name))
    except importlib_metadata.PackageNotFoundError:
        return NOT_INSTALLED


def _metadata(name: str) -> dict:
    """Locally installed distribution metadata, as a plain dict."""
    try:
        dist = importlib_metadata.distribution(normalize(name))
    except importlib_metadata.PackageNotFoundError:
        return {}
    return {k: v for k, v in dist.metadata.items()}


def latest_version(name: str, timeout: float = 10.0) -> str | None:
    """Latest version on PyPI, or None if it can't be determined."""
    url = f"https://pypi.org/pypi/{name}/json"
    req = urllib.request.Request(url, headers={"User-Agent": f"samall/{__version__}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.load(resp)
        return data["info"]["version"]
    except (urllib.error.URLError, OSError, ValueError, KeyError):
        return None


def _parse_version(v: str) -> tuple:
    """Crude version tuple for comparison; good enough for x.y.z tags."""
    parts = []
    for chunk in re.split(r"[._-]", v):
        parts.append((0, int(chunk)) if chunk.isdigit() else (1, chunk))
    return tuple(parts)


def is_outdated(current: str, latest: str | None) -> bool:
    if latest is None or current == NOT_INSTALLED:
        return False
    try:
        return _parse_version(current) < _parse_version(latest)
    except Exception:
        return current != latest


# --------------------------------------------------------------------------
# pip
# --------------------------------------------------------------------------

def pip_upgrade(targets: list[str]) -> int:
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *targets]
    return subprocess.run(cmd).returncode


# --------------------------------------------------------------------------
# global commands
# --------------------------------------------------------------------------

def cmd_status() -> int:
    print("samall — every library sam3360 has ever published\n")
    width = max(len(n) for n in LIBRARIES)
    missing = 0
    for name in LIBRARIES:
        ver = installed_version(name)
        if ver == NOT_INSTALLED:
            missing += 1
        print(f"  {name.ljust(width)}  {ver}")

    installed = len(LIBRARIES) - missing
    print(f"\n{installed}/{len(LIBRARIES)} libraries installed.")
    if missing:
        print(f"{missing} missing — run `samall --update` to install them.")
    print("Run `samall --outdated` to check PyPI for newer releases.")
    return 0


def cmd_list() -> int:
    print(f"samall v{__version__} includes {len(LIBRARIES)} packages:\n")
    for name in LIBRARIES:
        print(f"  {name}")
    return 0


def cmd_outdated() -> int:
    print(f"Checking PyPI for newer releases of {len(LIBRARIES) + 1} packages...\n")
    rows = []
    for name in LIBRARIES + [SELF_PACKAGE]:
        current = installed_version(name)
        latest = latest_version(name)
        if current == NOT_INSTALLED:
            rows.append((name, current, latest or "?", "not installed"))
        elif latest is None:
            rows.append((name, current, "?", "could not check"))
        elif is_outdated(current, latest):
            rows.append((name, current, latest, "update available"))

    if not rows:
        print("Everything is up to date.")
        return 0

    width = max(len(r[0]) for r in rows)
    for name, current, latest, note in rows:
        print(f"  {name.ljust(width)}  {current} -> {latest}  ({note})")
    print("\nRun `samall --update` to upgrade everything, "
          "or `samall --<package> --update` for just one.")
    return 0


def cmd_update_all() -> int:
    targets = LIBRARIES + [SELF_PACKAGE]
    print(f"Updating {len(targets)} packages (including samall itself)...\n")
    code = pip_upgrade(targets)
    if code != 0:
        print("\nUpdate failed — see pip output above.", file=sys.stderr)
        return code

    print("\nAll packages are up to date:\n")
    width = max(len(n) for n in targets)
    for name in targets:
        print(f"  {name.ljust(width)}  {installed_version(name)}")
    return 0


# --------------------------------------------------------------------------
# per-package commands
# --------------------------------------------------------------------------

def cmd_package_version(name: str) -> int:
    ver = installed_version(name)
    if ver == NOT_INSTALLED:
        print(f"{name} is not installed. Run `samall --{name} --update` to install it.")
        return 1
    print(f"{name} {ver}")
    return 0


def cmd_package_update(name: str) -> int:
    before = installed_version(name)
    print(f"Updating {name}...\n")
    code = pip_upgrade([name])
    if code != 0:
        print(f"\nCould not update {name} — see pip output above.", file=sys.stderr)
        return code

    after = installed_version(name)
    print()
    if before == NOT_INSTALLED:
        print(f"{name} installed at {after}.")
    elif before == after:
        print(f"{name} is already up to date at {after}.")
    else:
        print(f"{name} updated: {before} -> {after}")
    return 0


def cmd_package_details(name: str) -> int:
    current = installed_version(name)
    meta = _metadata(name)
    latest = latest_version(name)

    print(f"{name}\n")
    print(f"  installed     {current}")
    if latest:
        print(f"  latest        {latest}")
    else:
        print("  latest        could not reach PyPI")

    summary = meta.get("Summary")
    if summary:
        print(f"  summary       {summary}")
    if meta.get("Requires-Python"):
        print(f"  requires      Python {meta['Requires-Python']}")
    print(f"  pypi          https://pypi.org/project/{name}/")

    print()
    if current == NOT_INSTALLED:
        print(f"Not installed. Run `samall --{name} --update` to install it.")
    elif is_outdated(current, latest):
        print(f"Update available. Run `samall --{name} --update`.")
    elif latest:
        print("Up to date.")
    return 0


# --------------------------------------------------------------------------
# argument parsing
# --------------------------------------------------------------------------

def extract_package_selector(argv: list[str]) -> tuple[str | None, list[str], list[str]]:
    """
    Pull any --<package-name> selector out of argv.

    Done by hand rather than with argparse so that every package doesn't need
    its own registered flag (which would bloat --help with 13 entries) and so
    that --SecretShield, --shrug_it and --shrug-it all resolve to the same
    package. Returns (canonical_name, remaining_argv, unknown_selectors).
    """
    selected: str | None = None
    unknown: list[str] = []
    rest: list[str] = []
    known_flags = {"--list", "--update", "--version", "--outdated", "--help", "-h"}

    for token in argv:
        if token.startswith("--") and token not in known_flags:
            match = resolve_package(token[2:])
            if match:
                if selected is None:
                    selected = match
                elif match != selected:
                    unknown.append(f"{token} (only one package at a time)")
                continue
            unknown.append(token)
            continue
        rest.append(token)

    return selected, rest, unknown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="samall",
        description="Installs and manages every library sam3360 has ever published.",
        epilog=(
            "per-package usage:\n"
            "  samall --secretshield            details for one package\n"
            "  samall --secretshield --version  its installed version\n"
            "  samall --secretshield --update   upgrade only that package\n"
            "\nrun `samall --list` to see every available --<package> selector."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--list", action="store_true", help="list every package samall includes"
    )
    parser.add_argument(
        "--update", action="store_true",
        help="upgrade everything, or just the selected package",
    )
    parser.add_argument(
        "--version", action="store_true",
        help="show samall's version, or the selected package's version",
    )
    parser.add_argument(
        "--outdated", action="store_true",
        help="check PyPI and show which packages have a newer release",
    )
    return parser


def main() -> int:
    package, rest, unknown = extract_package_selector(sys.argv[1:])

    if unknown:
        parser = build_parser()
        names = ", ".join(unknown)
        parser.error(
            f"unrecognized option(s): {names}\n"
            f"run `samall --list` to see valid --<package> selectors."
        )

    args = build_parser().parse_args(rest)

    if package:
        # --list has no per-package meaning; treat it as the global command.
        if args.list:
            return cmd_list()
        if args.update:
            return cmd_package_update(package)
        if args.version:
            return cmd_package_version(package)
        return cmd_package_details(package)

    if args.list:
        return cmd_list()
    if args.update:
        return cmd_update_all()
    if args.outdated:
        return cmd_outdated()
    if args.version:
        print(f"samall {__version__}")
        return 0
    return cmd_status()


if __name__ == "__main__":
    sys.exit(main())
