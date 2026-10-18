#!/usr/bin/env python3
"""Fail if a ROM image or a large binary blob is tracked (or staged).

ROM images: extension .z64/.n64/.v64, or an N64 header magic in any of the
three byte orders (z64 80 37 12 40, n64 40 12 37 80, v64 37 80 40 12).

Large blobs: any tracked file of 8 MiB or more. The largest file on main at
the time this check was added is a 1.7 MB PNG, so screenshots are under the
line. Submodule gitlinks are not opened.

Exit 0 when nothing matches. Exit 1 and list the paths otherwise.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROM_EXT = {".z64", ".n64", ".v64"}
MAGICS = (
    bytes((0x80, 0x37, 0x12, 0x40)),
    bytes((0x40, 0x12, 0x37, 0x80)),
    bytes((0x37, 0x80, 0x40, 0x12)),
)
LARGE = 8 * 1024 * 1024


def git_paths(staged: bool) -> list[str]:
    if staged:
        cmd = ["git", "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"]
    else:
        cmd = ["git", "ls-files", "-z"]
    out = subprocess.run(cmd, cwd=ROOT, check=True, stdout=subprocess.PIPE).stdout
    return [p.decode() for p in out.split(b"\0") if p]


def reasons(path: Path) -> list[str]:
    found: list[str] = []
    if path.suffix.lower() in ROM_EXT:
        found.append(f"ROM extension {path.suffix}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        return [f"unreadable ({exc})"]
    if size >= LARGE:
        found.append(f"size {size} >= {LARGE}")
    if size >= 4:
        with path.open("rb") as fh:
            head = fh.read(4)
        if head in MAGICS:
            found.append(f"N64 header magic {head.hex()}")
    return found


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--staged",
        action="store_true",
        help="check the index (pre-commit) instead of every tracked file",
    )
    args = p.parse_args()
    bad = 0
    for rel in git_paths(args.staged):
        path = ROOT / rel
        if not path.is_file():
            continue
        why = reasons(path)
        if why:
            bad += 1
            print(f"{rel}: {', '.join(why)}")
    if bad:
        print(f"{bad} file(s) look like a ROM or a large binary blob")
        return 1
    scope = "staged" if args.staged else "tracked"
    print(f"no ROM images or >=8MiB blobs in {scope} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
