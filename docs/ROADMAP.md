# Roadmap: Rogue Squadron 64, native port plus matching decomp

This is the plan for the Jhalvordson fork. It sits under the [fork charter](../AGENTS.md#fork-charter). Where they disagree, the charter wins. Nothing here is a playtest claim.

Last revised: 22 Nov 2026.

## Goal

1. A great native PC port of *Star Wars: Rogue Squadron* (N64, USA v1.0): smooth 60fps, widescreen, good controls, known bugs fixed.
2. Modern graphics on top of that port: high resolution, widescreen without stretching, and HD texture packs through RT64.
3. A matching decompilation done properly: C that rebuilds the original code byte for byte. It is the long-term foundation for better symbols, cleaner patches, and deeper mods.

The model to follow is [Zelda 64: Recompiled](https://github.com/Zelda64Recomp/Zelda64Recomp). It uses the same N64Recomp and RT64 stack as this repo and ships high frame rates, widescreen and ultrawide, mods, and RT64 texture packs.

## Principles

- **The ROM never enters git.** No ROM, `RecompiledFuncs/`, extracted textures, audio, models, or disassembly output, and no ROM-derived data in docs. Each player supplies their own dump.
- **The build is the referee.** A decomp function counts only when the compiled bytes match the original. A port change counts only after Jeff plays it on his own dump.
- **One concern per PR.** Small draft PRs, each labelled `builds-not-verified-in-game` until Jeff has played it.
- **The repo is the memory.** Plans, quirks, attempt logs, and progress live in files, so any agent or person can pick up where the last one stopped.
- **Port first, polish second.** The decomp feeds the port. It never blocks a port fix that can ship today.

## The two tracks

### Track A: recomp port (this repo)

N64Recomp turns the game's MIPS code into C, N64ModernRuntime runs it, and the forked RT64 draws Factor 5's custom display lists. Upstream reports the game playable start to credits on Windows, with a known-issues list in the [README Status](../README.md#status-playable) (frame interpolation glitches, hitching, cutscene widths, a credits rendering bug, a rare boot freeze). Fork Phase 1 is that list plus CI, packaging, widescreen, 60fps and frame pacing, and controls.

### Track B: matching decomp (companion repo)

The companion decomp is [MikeSemicolonD/rogue_squadron64](https://github.com/MikeSemicolonD/rogue_squadron64), forked from [Tmcg2/rogue_squadron64](https://github.com/Tmcg2/rogue_squadron64). As read on 22 Nov 2026:

- It uses splat to split the ROM, with code split into `main`, `zlib`, and three overlays (mission, menu, cinematic). libultra code is matched against [decompals/ultralib](https://github.com/decompals/ultralib).
- The compilers are Nintendo-SDK-era GCC builds, not IDO. The Makefile uses SN GCC 2.8.1 by default and SN GCC 2.7.2 for some files and zlib, run through `wibo`, with asm-processor. m2c gives starter C.
- Its README calls it "very, very rough". The split has known code/data mistakes, and it cannot yet rebuild a matching ROM. No checksum gate or progress report exists yet.
- Tmcg2's repo is active ("More matches" commits through 21 Nov 2026). MikeSemicolonD's fork last merged from it on 27 Sep 2026.
- No official matched % is published. A rough count at Tmcg2 HEAD shows about 830 functions written in C and about 1,600 still as `INCLUDE_ASM` stubs. That's about a third by function count, but it's an estimate, not a verified match figure.

### How the tracks feed each other

Today the recomp reads only the decomp's **symbols and splits**. `tools/make_elf.py` in the decomp builds an ELF straight from the ROM plus the symbol files, and `regen_funcs` runs N64Recomp on that. Better names and boundaries already make the port easier to debug.

As the decomp matures:

- **Decomp to port:** correct function boundaries and jump tables, real names and types for patches, and port patches written as readable C against known structs. Later, N64Recomp can read a real compiled ELF.
- **Port to decomp:** the port's runtime traces, crash logs, and named hooks show which functions matter most, and tell the decomp which ones to grind first.

## Roles

| Who | Does |
| --- | --- |
| **Jeff** | Decides scope, playtests on his own dump, merges. Decides if and when anything goes to MikeSemicolonD's repos or Tmcg2. |
| **Frontier architect** (a frontier coding agent) | Plans, picks targets, writes briefs, reviews diffs and names, and keeps this roadmap current. It works from code and specs, never from ROM bytes in a PR. |
| **Local-model lane** (home hardware) | Does the brute-force per-function matching and proposes names, following the charter's [local lane](../AGENTS.md#local-qwen-lane): the endpoint and model come from environment variables, and it writes proposals only. It never merges and never commits ROM bytes or extracted assets. Tools: m2c, decomp-permuter, objdiff or asm-differ, and Ghidra for reading. |
| **CI / objdiff** | The referee. A function counts only when it byte-matches. A port PR passes CI, but it is still not verified in game. |

Permuter output is a hint, not a merge. A matching agent rewrites what it finds as readable C, and the build re-checks it.

## Milestones

Each phase has exit criteria. Tick them in Status tracking below.

### P0: reproducible build and first real playtest

- A documented local build on Jeff's machine from a clean clone: submodules, the decomp ELF, `regen_funcs`, the three RSP recomp outputs, `patches/`.
- `tools/verify_rom.py` passes on Jeff's dump.
- **Exit:** Jeff boots to the menu, flies one mission, and writes down what he saw. That is the fork's first "verified in game", and only then does any PR drop the label.

### P1: port Phase 1 (charter scope)

- CI and release packaging (the non-ROM CI already exists).
- 60fps and frame pacing: fix the object-ID problem that makes interpolation glitch (terrain first), and reduce the hitches.
- Widescreen: correct aspect ratio for gameplay and cutscenes, and a sane HUD.
- Controls: finish keyboard bind/rebind (the README points at Zelda64Recompiled's UI), plus gamepad defaults.
- Known bugs from README Status and AGENTS Open work: display-list desyncs, the credits text, the boot freeze, and remaining KSEG0 guards.
- **Exit:** Jeff plays a full mission at 60fps in widescreen with no stutter or visual regression he cares about. Each item gets its own PR and its own playtest.

### P2: decomp infrastructure

- Agree with Jeff where decomp work lives (see open questions), and keep it in sync with Tmcg2's upstream.
- A matching build: fix the known split mistakes, then add a checksum gate per segment and for the whole ROM, so CI fails on any mismatch.
- A pinned toolchain, ideally in a container: binutils, the SN GCC builds, splat, asm-processor, m2c, decomp-permuter, objdiff.
- A progress report per segment (bytes and functions), generated by a script, not hand-counted.
- A local-lane harness: pick a function, generate starter C, compile, diff, iterate, then save the draft and an attempt-log line. Results go back as proposals for the architect to review.
- A shared notes file of compiler quirks for these GCC builds. The DK64 decomp's IDO notes don't carry over.
- **Exit:** a clean clone plus a dump gives a byte-identical ROM, CI enforces it, and the harness has matched its first function end to end.

### P3: grind the segments

Order: libultra and zlib first (known source, quick wins that check the toolchain), then main game code, then the mission overlay (gameplay and flight), then menu, then cinematic. Inside each segment, functions the port touches or crashes in go first.

- The architect picks batches, the local lane grinds them, and the referee scores them.
- A naming pass after each batch, so names flow back into the symbol files the port uses.
- **Exit per segment:** 100% of code bytes matched and the segment's checksum is green.

### P4: modern graphics

- High internal resolution (and anti-aliasing, where RT64 offers it) through RT64, with the Factor 5 display-list path rendering cleanly.
- True widescreen with an extended view, not a stretch, where the game's culling allows it.
- HD texture pack support (RT64 already builds its `texture_hasher` and `texture_packer` tools here, per docs/AUDIT.md), plus a short guide for pack makers.
- **Exit:** Jeff plays at high resolution with a sample texture pack loaded and no regressions.

### P5: mods and deeper changes

- A mod template and loader pattern like Zelda 64: Recompiled's, built on decomp names and types.
- Larger changes (new controls, quality-of-life options, rendering upgrades) written as C against the matched decomp.
- **Exit:** a first mod installs and runs, and Jeff signs off on it.

## Guardrails

- No ROM and nothing derived from it in any commit, PR, issue, or doc. That includes addresses or data pulled from private analysis that isn't already public in this repo or the companion decomp.
- One concern per PR, opened as a draft. Jeff merges. No closing keywords.
- Every PR is labelled `builds-not-verified-in-game` until Jeff has played it.
- Never open PRs or issues on stock N64Recomp, N64ModernRuntime, or rt64 (see [CONTRIBUTING.md](../CONTRIBUTING.md)). Submodules stay pinned to MikeSemicolonD's forks.
- Upstream changes to MikeSemicolonD's repos or Tmcg2's decomp go out only when Jeff decides.
- The local lane proposes. It never merges, and the endpoint is never baked into the repo.
- Battle for Naboo stays parked ([tracking issue 13](https://github.com/Jhalvordson/RogueSquadron64Recomp/issues/13)).

## Open questions and risks

- **Where the decomp work lives.** The options are a Jhalvordson fork of Tmcg2's repo, contributing upstream to Tmcg2, or MikeSemicolonD's fork. Tmcg2's repo is the active one. Jeff decides.
- **Compiler mix.** Two SN GCC builds are in use, and the per-file assignment may still be wrong. Agent tooling and quirk notes are mostly built around IDO, so expect a slower start than DK64.
- **Split quality.** The decomp's own README says sections are mis-typed. Matching can't scale until splits are fixed.
- **Compressed and custom data.** zlib-compressed assets and Factor 5's custom microcode and MusyX audio need byte-exact handling for a full ROM match. The per-segment code hashes come first.
- **Local model quality.** Home models may stall on the hard last few percent. The plan expects to hand those to the frontier architect, and logs attempts so time isn't wasted twice.
- **Interpolation needs stable object IDs.** That may need decomp knowledge of how terrain and objects are built, so P1 and P3 may meet there.
- **Licensing and etiquette.** The decomp repos have their own owners. Coordinate before large rewrites.

## Status tracking

Update this list in the same PR as the work it describes.

- [x] Fork charter, source audit, ROM guard, non-ROM CI merged
- [ ] P0: documented local build reproduced on Jeff's machine
- [ ] P0: first in-game playtest by Jeff, written up
- [ ] P1: release packaging
- [ ] P1: 60fps / frame pacing (interpolation without terrain stutter)
- [ ] P1: widescreen (gameplay, cutscenes, HUD)
- [ ] P1: keyboard rebind and gamepad defaults
- [ ] P1: known-bug list cleared or triaged
- [ ] P2: decomp home decided by Jeff
- [ ] P2: split fixes and matching-ROM checksum gate in CI
- [ ] P2: pinned toolchain and progress script
- [ ] P2: local-lane harness matches its first function
- [ ] P3: libultra and zlib 100%
- [ ] P3: main 100%
- [ ] P3: mission overlay 100%
- [ ] P3: menu and cinematic overlays 100%
- [ ] P4: hi-res and true widescreen
- [ ] P4: HD texture pack support and guide
- [ ] P5: first mod running

## References

- [n64decomp/banjo-kazooie](https://github.com/n64decomp/banjo-kazooie): a Rare N64 game, 100% matching per its README. Useful for build and progress layout.
- [Unstripped/decomp_dk64](https://github.com/Unstripped/decomp_dk64): 100% of code bytes matched, written by LLM coding agents with one human reviewing. Its METHODOLOGY.md describes a containerised toolchain, per-segment hashes, a single integrator behind a merge gate, a quirks knowledge base, an attempt ledger, and m2c, decomp-permuter, and objdiff-style compare tools. It used IDO, not GCC, so take the process, not the compiler notes.
- [Zelda64Recomp/Zelda64Recomp](https://github.com/Zelda64Recomp/Zelda64Recomp): the target experience for the port, on the same N64Recomp and RT64 stack.
- [rerogue](https://github.com/dpethes/rerogue): PC-version format notes the N64 build shares.
