#!/usr/bin/env python3
"""Set esphome.project.version in recommended_base.yaml.

Used by the release workflow to keep the declared project version in sync with
the calendar-versioned git tag (YEAR.MONTH.PATCH).
"""

import pathlib
import re
import sys


def bump(path: pathlib.Path, version: str) -> None:
    text = path.read_text()
    pattern = re.compile(r'(?m)(^\s*version:\s*")[^"]*(")')
    new_text, count = pattern.subn(rf"\g<1>{version}\g<2>", text, count=1)
    if count != 1:
        raise SystemExit(f"could not find a project version in {path}")
    path.write_text(new_text)


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: bump_version.py <version>")
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    bump(repo_root / "recommended_base.yaml", sys.argv[1])
    print(f"set project.version = {sys.argv[1]}")


if __name__ == "__main__":
    main()
