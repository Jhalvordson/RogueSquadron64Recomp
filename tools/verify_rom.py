#!/usr/bin/env python3
"""Check a local Rogue Squadron dump against the hash the game uses at startup.

The expected XXH3-64 is read from src/main/main.cpp (RS64_ROM_HASH). It is not
copied here. librecomp hashes the image after padding to a multiple of 4 and
byteswapping .n64/.v64 to big-endian (see librecomp/src/recomp.cpp select_rom
and check_hash, XXH3_64bits, seed 0).

SHA-1 is not the startup check. rom/expected-sha1.txt is a placeholder until
a dump is hashed locally.

Exit 0 when the file is absent (nothing to check) or the XXH3 matches.
Exit 1 when a file is present and the XXH3 or a configured SHA-1 does not match.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN_CPP = ROOT / "src" / "main" / "main.cpp"
SHA1_FILE = ROOT / "rom" / "expected-sha1.txt"
XXHASH_H = ROOT / "lib" / "N64ModernRuntime" / "thirdparty" / "xxHash" / "xxhash.h"
DEFAULT_ROM = ROOT / "rom" / "rogue_squadron.z64"

# XXH3_64bits from the pinned xxHash (empty and "abc"). Used by --self-test.
XXH3_EMPTY = 0x2D06800538D394C2
XXH3_ABC = 0x78AF5F94892F3950

Z64_MAGIC = bytes((0x80, 0x37, 0x12, 0x40))


def expected_xxh3() -> int:
    text = MAIN_CPP.read_text(encoding="utf-8")
    m = re.search(r"RS64_ROM_HASH\s*=\s*0x([0-9A-Fa-f]+)ULL", text)
    if not m:
        raise SystemExit(f"RS64_ROM_HASH not found in {MAIN_CPP}")
    return int(m.group(1), 16)


def expected_sha1() -> str | None:
    """Return a 40-hex digest, or None when the placeholder is still unset."""
    if not SHA1_FILE.is_file():
        return None
    for line in SHA1_FILE.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.upper() == "PLACEHOLDER":
            return None
        if re.fullmatch(r"[0-9A-Fa-f]{40}", s):
            return s.lower()
        raise SystemExit(f"{SHA1_FILE} has {s!r}; expected PLACEHOLDER or 40 hex digits")
    return None


def normalize_rom(data: bytes) -> bytes:
    """Match select_rom: pad to 4, then byteswap to z64 order if the magic says so."""
    if len(data) % 4:
        data = data + bytes(4 - (len(data) % 4))
    if len(data) < 4:
        raise SystemExit("file is shorter than an N64 header")
    b0, b1, b2, b3 = data[0], data[1], data[2], data[3]
    # NotByteswapped: 80 37 12 40
    if (b0, b1, b2, b3) == (0x80, 0x37, 0x12, 0x40):
        return data
    # Byteswapped4 (.n64): 40 12 37 80, index_xor = 3
    if (b0, b1, b2, b3) == (0x40, 0x12, 0x37, 0x80):
        return _byteswap(data, 3)
    # Byteswapped2 (.v64): 37 80 40 12, index_xor = 1
    if (b0, b1, b2, b3) == (0x37, 0x80, 0x40, 0x12):
        return _byteswap(data, 1)
    raise SystemExit(
        "header is not an N64 ROM magic "
        f"({b0:02X} {b1:02X} {b2:02X} {b3:02X}); refusing to hash it"
    )


def _byteswap(data: bytes, index_xor: int) -> bytes:
    out = bytearray(len(data))
    for pos in range(0, len(data), 4):
        chunk = data[pos : pos + 4]
        for i, byte in enumerate(chunk):
            out[pos + (i ^ index_xor)] = byte
    return bytes(out)


def xxh3_64(data: bytes) -> int:
    try:
        import xxhash  # type: ignore
    except ImportError:
        return _xxh3_via_header(data)
    return xxhash.xxh3_64(data).intdigest()


def _xxh3_via_header(data: bytes) -> int:
    if not XXHASH_H.is_file():
        raise SystemExit(
            "need the xxhash Python module (python3-xxhash) or the "
            "N64ModernRuntime xxHash submodule to compute XXH3-64"
        )
    src = r"""
#define XXH_STATIC_LINKING_ONLY
#define XXH_IMPLEMENTATION
#include "xxhash.h"
#include <stdio.h>
int main(void) {
    unsigned char buf[1 << 16];
    XXH3_state_t* st = XXH3_createState();
    XXH3_64bits_reset(st);
    size_t n;
    while ((n = fread(buf, 1, sizeof buf, stdin)) > 0)
        XXH3_64bits_update(st, buf, n);
    printf("%016llx\n", (unsigned long long)XXH3_64bits_digest(st));
    XXH3_freeState(st);
    return 0;
}
"""
    with tempfile.TemporaryDirectory() as td:
        cpath = Path(td) / "xxh3_stdin.c"
        cpath.write_text(src, encoding="utf-8")
        bin_path = Path(td) / "xxh3_stdin"
        subprocess.run(
            ["cc", "-O2", f"-I{XXHASH_H.parent}", "-o", str(bin_path), str(cpath)],
            check=True,
        )
        proc = subprocess.run(
            [str(bin_path)], input=data, stdout=subprocess.PIPE, check=True
        )
    return int(proc.stdout.decode().strip(), 16)


def self_test() -> int:
    got = expected_xxh3()
    want = 0x6B66A44153594DEA
    if got != want:
        print(f"self-test: RS64_ROM_HASH is 0x{got:016X}, expected 0x{want:016X}")
        return 1
    if xxh3_64(b"") != XXH3_EMPTY or xxh3_64(b"abc") != XXH3_ABC:
        print("self-test: XXH3-64 does not match XXH3_64bits vectors")
        return 1
    # .n64 magic byteswapped in groups of 4 becomes the .z64 magic.
    swapped = normalize_rom(bytes((0x40, 0x12, 0x37, 0x80)))
    if swapped[:4] != Z64_MAGIC:
        print("self-test: .n64 byteswap did not produce z64 magic")
        return 1
    v64 = normalize_rom(bytes((0x37, 0x80, 0x40, 0x12)))
    if v64[:4] != Z64_MAGIC:
        print("self-test: .v64 byteswap did not produce z64 magic")
        return 1
    if expected_sha1() is not None:
        print("self-test: SHA-1 placeholder is set; leaving it for a real dump")
    else:
        print("self-test: SHA-1 placeholder is unset (startup check is XXH3-64)")
    print(f"self-test: XXH3 expected 0x{got:016X} from {MAIN_CPP.name}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("rom", nargs="?", type=Path, default=DEFAULT_ROM)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        return self_test()

    path = args.rom
    if not path.is_file():
        print(f"no dump at {path}")
        print("place your USA v1.0 ROM there and re-run before building")
        print(f"startup XXH3-64 expected 0x{expected_xxh3():016X} (not checked)")
        return 0

    raw = path.read_bytes()
    image = normalize_rom(raw)
    digest = xxh3_64(image)
    want = expected_xxh3()
    sha1 = hashlib.sha1(image).hexdigest()
    print(f"file {path} ({len(raw)} bytes, normalized {len(image)})")
    print(f"XXH3-64  0x{digest:016X}")
    print(f"expected 0x{want:016X}  (RS64_ROM_HASH in src/main/main.cpp)")
    ok = digest == want
    print("XXH3 match" if ok else "XXH3 mismatch")

    sha_want = expected_sha1()
    if sha_want is None:
        print(f"SHA-1 {sha1}  (placeholder in {SHA1_FILE.name} is unset; not compared)")
    else:
        sha_ok = sha1 == sha_want
        print(f"SHA-1 {sha1}")
        print(f"expected {sha_want}")
        print("SHA-1 match" if sha_ok else "SHA-1 mismatch")
        ok = ok and sha_ok
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
