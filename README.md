# samall  

Installs every library [sam3360](https://pypi.org/user/sam3360/) has ever
published. That's it — `samall` itself does nothing except depend on all of
them, so `pip install samall` pulls the whole catalog in one shot.

```
pip install samall
samall              # show installed versions
samall --list       # list every package samall includes
samall --update     # upgrade every included package, and samall itself
```

```
samall — every library sam3360 has ever published

  replico          0.2.3
  vibeUI            0.1.0
  sam3360           0.3.0
  whyfail           3.0.0
  secretshield      0.4.2
  shrug-it          0.1.0
  memobox           0.2.0
  pyproject-lens    0.1.0
  neonprint         0.1.0
  cortexa           0.1.0
  formula-math      0.1.0

11 libraries installed. samall itself does nothing else.
```

## Currently included

- [replico](https://pypi.org/project/replico/)
- [vibeUI](https://pypi.org/project/vibeUI/)
- [sam3360](https://pypi.org/project/sam3360/)
- [whyfail](https://pypi.org/project/whyfail/)
- [secretshield](https://pypi.org/project/secretshield/)
- [shrug-it](https://pypi.org/project/shrug-it/)
- [memobox](https://pypi.org/project/memobox/)
- [pyproject-lens](https://pypi.org/project/pyproject-lens/)
- [neonprint](https://pypi.org/project/neonprint/)
- [cortexa](https://pypi.org/project/cortexa/)
- [formula-math](https://pypi.org/project/formula-math/)

## Publishing a new library later

PyPI dependencies are frozen at upload time — there's no way for
`pip install samall` to reach out and dynamically decide what to install at
someone else's install time. So "auto-detect" here means: **adding a new
library to samall's next release is one line + one command**, not zero
effort, but as close as the packaging system allows.

```
# 1. add the package name to libraries.txt
echo "my-new-lib" >> libraries.txt

# 2. sync it into pyproject.toml and cli.py
python scripts/sync_deps.py

# 3. bump the version in pyproject.toml, then publish
python -m build
twine upload dist/*
```

`libraries.txt` is the single source of truth; `scripts/sync_deps.py` writes
it into both `pyproject.toml`'s `dependencies` and `cli.py`'s `LIBRARIES`
list, with no network calls, so it can't fail or get blocked.

There's also `scripts/check_pypi_profile.py`, a **best-effort, read-only**
helper that checks `https://pypi.org/user/sam3360/` and tells you if
anything there isn't in `libraries.txt` yet. It can't run unattended (e.g.
in a nightly CI job) reliably: PyPI serves profile pages behind Fastly's
bot-challenge for non-browser requests, so a plain script sometimes gets a
challenge page back instead of your project list. It detects that case and
tells you plainly rather than guessing. Use it as a manual "did I forget
one?" check before a release, not as unattended automation.

## Development

```
pip install -e .
python scripts/sync_deps.py
python scripts/check_pypi_profile.py
```
