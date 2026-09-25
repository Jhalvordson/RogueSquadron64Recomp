# Local ROM

This directory is for your own dump. The game image is not part of the
repository. `*.z64`, `*.n64`, and `*.v64` are gitignored, and so is everything
in this directory except this file and `expected-sha1.txt`.

Put the USA v1.0 ROM at `rom/rogue_squadron.z64`. Startup also looks in the
process working directory for `rogue squadron.z64`, `RogueSquadron.z64`, and
`rs64.z64` (`src/main/main.cpp`). Then, before building:

```sh
python3 tools/verify_rom.py rom/rogue_squadron.z64
```

The script reads `RS64_ROM_HASH` from `src/main/main.cpp` and computes
XXH3-64 the same way `librecomp` does at startup: pad to a multiple of 4,
byteswap an `.n64` or `.v64` header to big-endian, then `XXH3_64bits` over
the whole buffer (seed 0). The value checked in is `0x6B66A44153594DEA`.

SHA-1 is not that startup check. `expected-sha1.txt` stays `PLACEHOLDER`
until you replace it with the lowercase SHA-1 of the normalized image from
your own dump. Until then the script prints the SHA-1 and does not compare it.

If the file is missing, the script exits 0 and tells you it did not check
anything, so a ROM-less configure is not blocked. A present file that does
not match exits 1.

`tools/check_no_rom_blobs.py` is the commit/CI check. It fails on
`.z64`/`.n64`/`.v64`, on an N64 header magic, or on any tracked file of
8 MiB or more. Optional hook:

```sh
git config core.hooksPath .githooks
```
