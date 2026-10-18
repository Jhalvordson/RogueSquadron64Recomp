# Audit snapshot

Source inspection of `main` at `8b67d28c67a126b7ebf61e45b1acbfe7aca5d7ab` (merge of MikeSemicolonD PR 9). This is not an in-game run. No ROM was present. Nothing here is a playtest.

Upstream of this fork is https://github.com/MikeSemicolonD/RogueSquadron64Recomp. The companion decomp the recompiler reads is https://github.com/MikeSemicolonD/rogue_squadron64 (started by Tmcg2).

## Build system

Root file: `CMakeLists.txt`. CMake 3.20+, C17, C++20. `CMAKE_RUNTIME_OUTPUT_DIRECTORY` is the binary dir, so single-config generators put executables in `build/` and Visual Studio puts them in `build/<Config>/`.

The root project always adds:

| Target | What it is |
| --- | --- |
| `rt64` | Static library. The root sets `RT64_STATIC` and `RT64_SDL_WINDOW_VULKAN` before `add_subdirectory(lib/rt64)`. |
| `ultramodern`, `librecomp` | Static libraries from `lib/N64ModernRuntime`. |
| `RecompiledFuncs` | Static library. `file(GLOB CONFIGURE_DEPENDS)` of `RecompiledFuncs/*.{c,cpp}`. That directory is gitignored. |
| `regen_funcs` | Custom target, not part of the default `all` build. Runs `${N64RECOMP_EXE}` on `rogue_squadron.toml`. Depends on `N64RecompCLI` when that target exists. |
| `gen_state_table` | Custom target when Python 3 is found. Writes `src/main/state_table.inl` from `state_model.toml`. The `.inl` is gitignored. |
| `RogueSquadron64Recomp` | The game executable. |
| `video_config_test`, `nav_target_test` | `EXCLUDE_FROM_ALL`. `cmake --build build --target video_config_test` (and `nav_target_test`). |
| `PatchesLib` | OBJECT library, only if `mips64-elf-gcc`, `N64Recomp.exe`, and `make` all exist at configure time. Otherwise CMake prints a skip and the game links without the `patches/` overrides. |

`librecomp`'s CMake pulls `lib/N64ModernRuntime/N64Recomp` with `EXCLUDE_FROM_ALL`. Targets defined there:

| Target | Output |
| --- | --- |
| `N64Recomp` | Static library (recompiler core). |
| `N64RecompElf` | ELF reader. |
| `N64RecompCLI` | Executable, `OUTPUT_NAME N64Recomp`. This is the tool `regen_funcs` runs. |
| `RSPRecomp` | RSP recompiler executable. |
| `RecompModTool`, `OfflineModRecomp`, `RecompModMerger`, `LiveRecomp`, `LiveRecompTest` | Mod tooling. `librecomp` links `N64Recomp` and `LiveRecomp`. |

RT64 also builds `file_to_c`, `re-spirv`, `nfd`, `libzstd_static`, `plume`, `texture_hasher`, and `texture_packer`.

### regen_funcs and the decomp ELF

`rogue_squadron.toml`:

```
elf_path = "../rogue_squadron64/build/roguesquadron.elf"
rom_file_path = "../rogue_squadron64/rogue_squadron.z64"
output_func_path = "RecompiledFuncs"
```

`regen_funcs` is N64Recomp over that toml. The ELF is produced in the sibling decomp checkout (`splat split` then `python tools/make_elf.py`, per the README). The ROM path in the toml is an input to the recompiler for data, separate from the runtime ROM next to the executable.

The default `N64RECOMP_EXE` cache value is `${CMAKE_BINARY_DIR}/Debug/N64Recomp.exe`. That matches a Visual Studio multi-config build. A Linux Ninja build of `N64RecompCLI` writes `${CMAKE_BINARY_DIR}/N64Recomp` with no `.exe` suffix. `regen_funcs` on Linux does not point at that binary unless `-DN64RECOMP_EXE=` is passed. `MIPS_GCC` / `MIPS_LD` are hardcoded to `E:/mips-toolchain/bin/mips64-elf-gcc.exe` and `mips64-elf-ld.exe`.

### What a clean tree cannot link

`RogueSquadron64Recomp` lists three RSPRecomp outputs that are not in git:

- `build/factor5_ucode/factor5_ucode_recompiled.c` (`factor5_rsp.toml`, `rom_file_path = "rogue_squadron.z64"`, text at ROM `0x025610`)
- `build/factor5_ucode/factor5_boot_recompiled.c` (`factor5_boot_rsp.toml`, `rom_file_path = "factor5_boot_text.bin"`)
- `build/factor5_ucode/musyx_audio_recompiled.c` (`musyx_rsp.toml`, `rom_file_path = "rogue_squadron.z64"`, text at ROM `0x9ABE0`)

`build*/` is gitignored, so those `.c` files are not in the clone. `factor5_boot_text.bin` is named in `.gitignore` as intentionally not ignored, and it is not tracked. `src/main/register_overlays.cpp` includes `../../../N64Recomp/RecompiledFuncs/recomp_overlays.inl`. From `src/main/` that path is `<parent-of-repo>/N64Recomp/RecompiledFuncs/recomp_overlays.inl`, not `<repo>/RecompiledFuncs/`. CMake's include path for the game adds `<repo>/RecompiledFuncs`, which does not rewrite a `../` include.

## Submodules and pinned SHAs

`.gitmodules` records two submodules. `git ls-tree HEAD` pins:

| Path | SHA | URL |
| --- | --- | --- |
| `lib/N64ModernRuntime` | `d96b1e912283f1baaceb6415d3a5e56f19801703` | https://github.com/MikeSemicolonD/N64ModernRuntime.git |
| `lib/rt64` | `40687126b782a70f5251cc1428dbf30125fdfc4c` | https://github.com/MikeSemicolonD/rt64.git |

Nested gitlinks are pinned by those commits (not floated by this repo). N64ModernRuntime:

| Path | SHA |
| --- | --- |
| `N64Recomp/lib/ELFIO` | `ad8b641f9682b6091ba8b9f7c8152255c1a2c803` |
| `N64Recomp/lib/fmt` | `407c905e45ad75fc29bf0f9bb7c5c2fd3475976f` |
| `N64Recomp/lib/rabbitizer` | `e0d8003047938e2ec3697eaf8d61a84d11d17b43` |
| `N64Recomp/lib/sljit` | `f6326087b3404efb07c6d3deed97b3c3b8098c0c` |
| `N64Recomp/lib/tomlplusplus` | `1f7884e59165e517462f922e7b6de131bd9844f3` |
| `thirdparty/miniz` | `8573fd7cd6f49b262a0ccc447f3c6acfc415e556` |
| `thirdparty/o1heap` | `a124b850791db2a33f7354d2b0aa7da821cef6f5` |
| `thirdparty/xxHash` | `ac3a25da3d957d9ef3e4114d9f8332d34ce83a46` |

`thirdparty/concurrentqueue`, `thirdparty/json`, and `thirdparty/sse2neon` are files in the N64ModernRuntime tree, not submodules.

rt64:

| Path | SHA |
| --- | --- |
| `src/contrib/ddspp` | `21ca0c4319dfd5a161c5f2a0c406e8f60194ea6c` |
| `src/contrib/dxc` | `cc15e715ee378a4f675b335bd1071ff105873fc8` |
| `src/contrib/hlslpp` | `6f5274c66132e8f951c400103d897582b8f21491` |
| `src/contrib/im3d` | `d03941725fd0bd08c78c46e3e5b0265526e9d060` |
| `src/contrib/imgui` | `277ae93c41314ba5f4c7444f37c4319cdf07e8cf` |
| `src/contrib/implot` | `f156599faefe316f7dd20fe6c783bf87c8bb6fd9` |
| `src/contrib/mupen64plus-core` | `860fac3fbae94194a392c1d9857e185eda6d083e` |
| `src/contrib/mupen64plus-win32-deps` | `de8111fdcb89144abc16c85650ce4e21e028bfb5` |
| `src/contrib/nativefiledialog-extended` | `17b6e8ce219c0677f94b63636abb9296b28841ca` |
| `src/contrib/plume` | `7f3f34f7d69781291b4bbe82b044540cda865b78` |
| `src/contrib/re-spirv` | `5d6b756ee62760f71b65d37e41a0b5a3dab90507` |
| `src/contrib/spirv-cross` | `6173e24b31f09a0c3217103a130e74c4ddec14a6` |
| `src/contrib/stb` | `ae721c50eaf761660b4f90cc590453cdb0c2acd0` |
| `src/contrib/xxHash` | `1864a50c9b5cf8500d8e9e61ed92aa0dd3772750` |
| `src/contrib/zstd` | `0ff651dd876823b99fa5c5f53292be28381aee9b` |

plume's own gitlinks: `D3D12MemoryAllocator` `9ef66bc14edd10dee0de3a545b98578363552f66`, `Vulkan-Headers` `2fa203425eb4af9dfc6b03f97ef72b0b5bcb8350`, `VulkanMemoryAllocator` `29b35ea4232688c0f42cdff0c10848290760a417`, `volk` `be3dbd49bf77052665e96b6c7484af855e7e5f67`. re-spirv pins `external/SPIRV-Headers` `f013f08e4455bcc1f0eed8e3dd5e2009682656d9`.

A checkout that builds RT64 needs `git submodule update --init --recursive`. The dxc pin includes `bin/x64/dxc-linux`, which needs `libdxcompiler.so` from `lib/x64` (`RPATH` is `$ORIGIN/../lib`, which does not contain that library; CMake prefixes the shader command with `LD_LIBRARY_PATH=.../lib/x64`).

## How the ROM is consumed

There is no ROM in the git tree. `git ls-files` has no `*.z64`, `*.n64`, or `*.v64`. `.gitignore` ignores `*.z64`, `*.n64`, and `*.elf`. It does not ignore `*.v64`.

Two different consumers:

1. **Recompiler.** `rom_file_path` in `rogue_squadron.toml`, `factor5_rsp.toml`, and `musyx_rsp.toml`, as above.
2. **Runtime.** `src/main/main.cpp` registers one game:

```c
static constexpr uint64_t RS64_ROM_HASH = 0x6B66A44153594DEAULL;
// internal_name "ROGUE SQUADRON", game_id rs64.n64.us.1.0, SaveType::Eep4k
```

`librecomp/src/recomp.cpp` `check_hash` is `XXH3_64bits(rom_data.data(), rom_data.size())` from `thirdparty/xxHash` (`xxh3.h`), seed 0, over the whole buffer. `select_rom` pads the file to a multiple of 4, detects the N64 magic, and byteswaps `.n64` (groups of 4) or `.v64` (groups of 2) to big-endian before that hash. The expected value is therefore the XXH3-64 of the normalized USA v1.0 image, not of an arbitrary dump byte-for-byte. A mismatch against the internal name `ROGUE SQUADRON` returns `IncorrectVersion` or `IncorrectRom`.

Startup (`main`) sets the config directory to `std::filesystem::current_path()` and looks for `rogue_squadron.z64`, `rogue squadron.z64`, `RogueSquadron.z64`, and `rs64.z64` in that directory. The stored copy's name is `game_id + ".z64"` (`rs64.n64.us.1.0.z64`). The stderr text says to put the file next to the executable; the search is the process working directory.

The README states the same hash and a 16 MB USA v1.0 image. This audit did not recompute it against a dump.

## CI

There is no `.github/` directory on this commit. No workflow, no pre-commit hook, no CI config of any other kind in the tree.

## Known bugs, TODOs, and doc drift

README section `Status (PLAYABLE)` lists these as open, from the upstream author's Windows playthrough. They were not re-checked here:

- Credits text clipping and background artifacts after the ending cutscene (not the CREDITS passcode).
- Rare freeze while fading to black on the Attribution screen.
- A ring near the skybox horizon overlapping transparent materials (depth sorting suspected).
- CPU hitching around 20 fps in spots.
- Cutscenes with varying widths.
- Battle of Calamari post-cutscene shows a terrain edge the fog should cover.
- Frame interpolation can be enabled and glitches because of object IDs; terrain that regenerates stutters.
- Low-resolution mode makes cutscenes look wide.
- Slight cutoff at the top of text rects, also present in the original game.

`AGENTS.md` "Open work" does not match the tree on a few points:

- It links `README.md#open-work`. The README has no Open work heading. The status list is `## Status (PLAYABLE)`.
- Open work item 4 says the keyboard rebind UI is still to port. `src/main/main.cpp` already has an F6 Controls window and `roguesq_input.json` (see below).
- Open work item 3 says plain KSEG0 entry-bail / skip-store hooks remain in the toml. `rogue_squadron.toml` around the host-hooks banner says those inline KSEG0 guards are gone.
- The README controls table lists look-around as F8. `src/main/input_bindings.cpp` `default_bindings` binds `Target::CUp` to `SDL_SCANCODE_Q`, and the comment on that line calls it look around. No default binding uses F8.
- That same table assigns cockpit, close, and switch view to F1, F3, and F4, and `default_bindings` binds those actions to those keys. The next README paragraphs say Debug builds also use F1 for the RT64 inspector, F3 for ViewRDRAM, and F4 for texture replacement.
- `CMakeLists.txt` defaults `MIPS_TOOLCHAIN_DIR` to `E:/mips-toolchain` and points `MIPS_GCC` / `MIPS_LD` at the `.exe` names under `bin/`. The README build section says Debug is the tested configuration.

`src/main/rt64_render_context.cpp` sets `refreshRate = RefreshRate::Original` (interpolation off) and `refreshRateTarget = 60`, then the `ROGUESQ_RT_INTERP` block's comment says the baseline is on at 60 Hz. `docs/debug-trace-env-vars.md` says the env var defaults off. The README says turning interpolation on glitches. The same env-var doc says the Factor 5 path was "nearly flicker-free". Those two documents disagree. This audit did not run either setting.

`tools/musyx_harness.cpp` still has a TODO for building a voice command list. `tools/MORTDecoder.cpp` has scattered address TODOs. `docs/game-architecture.md` says about 2000 functions are still `func_XXXXXXXX`.

A no-ROM compile of the host sources on Ubuntu 24.04 / GCC 13 (not a game launch) showed two Linux breaks on this commit:

- `plume_render_interface_types.h` includes X11 unless `PLUME_SDL_VULKAN_ENABLED` is set. The root CMake option `RT64_SDL_WINDOW_VULKAN` adds that define only inside `lib/rt64`, so `rt64_render_context.cpp` sees an X11 `RenderWindow` while `ultramodern` types `WindowHandle` as `SDL_Window*` on Linux.
- Once those headers are visible, the X11 `Bool` macro collides with `CliFlag::Bool` in `main.cpp`. The file already avoids `SDL_syswm.h` for the same macros.
- `tests/video_config_test.cpp` `test_apply_basic` applies `"graphicsAPI": "d3d12"` and expects `GraphicsAPI::D3D12`. `UserConfiguration::validate` calls `isGraphicsAPISupported`, which is false for D3D12 when `_WIN32` is not set, and then stores `Automatic`. That assertion fails on Linux. The other checks in the file passed in the same no-ROM build (`nav_target_test` printed OK).

## Widescreen, 60fps interpolation, controls

### Widescreen

Not a game-side projection patch. It is an RT64 `UserConfiguration::aspectRatio` knob.

| Hook | Where |
| --- | --- |
| `roguesq_video.json` key `widescreen` | `src/main/video_config.cpp` `apply_friendly`: `true` sets `AspectRatio::Expand`, `false` sets `Original`. `to_friendly` writes the key back. |
| `ROGUESQ_WIDESCREEN=1` | `src/main/rt64_render_context.cpp` `create_render_context`: sets `AspectRatio::Expand`. Applied after the JSON load, so the env var wins. |
| `ROGUESQ_ASPECT=<w/h>` | Same function. Sets `AspectRatio::Manual` and `aspectTarget`. Takes precedence over `ROGUESQ_WIDESCREEN` when both are set. |
| Unit test | `tests/video_config_test.cpp` checks the `widescreen` key round-trip. |
| Doc | `docs/debug-trace-env-vars.md` says F5 HUD/2D may need alignment at non-4:3. |

`rogue_squadron.toml` `[[patches.hook]]` entries are not where aspect ratio is applied.

### 60fps / frame interpolation

The game logic tick is not rewritten. Interpolation is RT64's refresh-rate mode.

| Hook | Where |
| --- | --- |
| Baseline | `rt64_render_context.cpp`: `refreshRate = Original`, `refreshRateTarget = 60` before the JSON load. `Original` is off. |
| `roguesq_video.json` `frameInterpolation` | `video_config.cpp`: `true` sets `RefreshRate::Manual`, `false` sets `Original`. `targetFramerate` maps to `refreshRateTarget`. |
| `ROGUESQ_RT_INTERP` | Same render-context block. `0` forces `Original`. Any other set value uses `Manual` and that Hz, floored to 60 when the parsed number is below 20. |
| VI pacing | README and `AGENTS.md`: the default loop is the game's VI/SP/DP protocol. `--no-vi-driven-loop` / `ROGUESQ_VI_DRIVEN_LOOP=0` is the older host-paced loop. |

### Controls (F6, `roguesq_input.json`)

| Hook | Where |
| --- | --- |
| F6 | `src/main/main.cpp` `poll_input`: `SDL_SCANCODE_F6` toggles `g_show_controls`. Esc closes the window when it is open. |
| Window | `draw_controls_ui` in the same file. ImGui. Save / Restore defaults / per-action Rebind. Mouse sensitivity, smoothing, curve, invert. The comment above the function says it is active in developer mode (the inspector frame). |
| File | `src/main/input_bindings.cpp` `default_config_path()` is `SDL_GetBasePath()` plus `roguesq_input.json` (next to the executable, not the working directory). |
| Load | `main()` calls `rs64::input::load_bindings`. `ROGUESQ_INPUT_RESET=1` overwrites the file with `default_bindings()`. |
| Resolve | `rs64::input::resolve` in `input_bindings.cpp`, called from `get_n64_input`. |
| Header | `src/main/input_bindings.h`. Targets are N64 buttons plus four stick directions. Sources are key, pad button, pad axis, mouse button, mouse axis. |

README Controls and `docs/debug-trace-env-vars.md` describe the same F6 window. In Debug, the README says press F1 before F6 because the RT64 inspector owns the ImGui frame.
