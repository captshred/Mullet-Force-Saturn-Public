# Phase 1: legacy sprite registration reclamation

Branch: `optimization/level1-legacy-sprite-cleanup`.
Parent and approved tag `the-one-ai3-baseline`: `15387a314a51bffbe3e65152e45958ed5f3416c5`.
This report belongs to the commit containing it. No baseline/tag changes or Phase 2 work.

## Change

Only the production `stage-default` profile enables `MF_LEGACY_SPRITE_CLEANUP`.
It skips BT00–BT06.TGA, CT00–CT06.TGA, LEGS.TGA and AL0–AL2.TGA
registrations. All original assets remain in the repository and disc. Historical
profiles default to the original loader. Retired handles become explicit invalid
IDs; all retained handles come from the allocator, so shifted IDs resolve normally.
No drawing or gameplay logic changed.

| Allocation | Approved baseline | Optimized | Reclaimed |
|---|---:|---:|---:|
| Definitions | 255 | 237 | 18 |
| Texture bytes | 452800 | 386848 | 65952 |
| Free texture bytes | 5688 | 71640 | |

All 223 retained payload allocations and 14 zero-payload crop/tail views remain.
The allocation test checks bounds, nonoverlap, exact retained registration order,
dimensions, formats and palette selection; every view resolves inside retained
pixel storage. The allocator's preceding-definition/sentinel behavior is retained.

## Files

Runtime source: `src/main.c` (conditional registrations),
`src/arcade_fx_config.h` (default-off profile guard and exact budget),
`src/animation_preview.c` (memory-accounting subtraction only).
Build/accounting: `tools/build-source-complete.sh`, `tools/build-native.sh`,
`tools/audit-sprite-memory.py`, `Makefile`, `assets/legacy-sprite-cleanup.json`.
New checks: `tools/validate-legacy-sprite-cleanup.py`,
`tools/test-legacy-sprite-cleanup.py`, `tests/sprite_cleanup/{jo/jo.h,trace.c,scenarios.inc}`.
This document records evidence and limits.

The preservation gate compares all other baseline files byte for byte, including
AI 3.0, input/FF+A, stage clear, audio scheduler/samples/music, E108 request-flag
repair, Level 2 loader, wingsuit gameplay and graphics. Main's entire renderer and
update body are identical; animation-preview changes are restricted to accounting.

## Validation performed

- Native `bash tools/build-stage.sh --native`, pinned Jo Engine/compiler SDK
  `556d081146211b6a1cfa6591d70f9487d406758b`: passed; matching local BIN/CUE generated.
- `make check` and `make test`: passed. These run the approved baseline's original
  preservation/regression chain, then the new actual optimized allocation and
  visual-semantic checks. Original tests include both players, combo and FF+A
  buffering, AI 3.0, stage clear/parallax, audio scheduling/flame sustain, wingsuit
  movement/banking/shooting, Level 2 rendering, actual Level 2 loader, WDEATH bank,
  command readiness/consumption and cold/warm restart cases. The existing cold-start
  runner passed 16 fresh host processes; these are mocked runtime tests, not 16
  Saturn boots.
- Actual loader audit: exact table above, no other registrations removed, original
  TGAs still staged. Historical counterfactual: 255 / 452800. Historical FX-off:
  255 / 453344; FX-off/combo-off: 253 / 446304.
- Actual baseline versus optimized versus historical renderers: 7198 frame cases,
  140391 draw commands, identical after replacing numeric sprite IDs with decoded
  texture content/dimensions/format. Exact SHA256 of decoded texture/crop pixels,
  complete sprite palettes, positions, flip, scale, depth and frame ordering match.
  Both actors/facings, idle/walk/run/jump/landing, combo, running bat, kick,
  hurt/death, torch, enemy states, effects, HUD, gallery and animation review are
  exercised under undefined-behavior sanitizer. This is host semantic evidence;
  background drawing and sound I/O are mocked and preserved by the file gate.
- Yabause libretro `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, HLE BIOS,
  interpreter/software renderer, one thread, no cartridge, fresh save directories:
  baseline and optimized each ran 1000 frontend frames using
  `tests/runtime/playable-frontend.c`. Both entered gameplay at frame 822.
  All 35 captured gameplay images (825–995 every five frames) were pixel identical;
  all 178 gameplay state snapshots (822–999) were byte identical. Overall 246/296
  captured images matched. The 50 differing gallery images (555–800 every five
  frames) show the expected memory counter change and an idle animation phase
  difference: optimized registration reaches scene initialization 20 frontend
  frames earlier. State differences are restricted to initialization frames
  563–582. No gameplay timing difference was observed after the shared Start input.
  VDP1 raw hashes legitimately differ because texture allocation changed.
- `git diff --check`: passed.

Emulator reproduction uses the existing frontend, compiled with the core's
`libretro-common/include`, `-Isrc -include build/build-info.h -ldl`, then invoked as:
`frontend CORE CUE FRESH_OUTPUT_DIR 1000 run GAME_ADDRESS IDLE_ADDRESS`.
Addresses must be extracted from each build's SH COFF symbol table; they are not
stable across builds. Tested baseline addresses: `0x6042718`, `0x6042a04`;
optimized: `0x60426b8`, `0x60429a4`. Compare `trace.bin` using
`tools/playable_runtime_validation.py` and PPM files byte for byte, rather than
comparing numeric texture IDs.

## Limits and playtest

No real hardware validation, audible listening test, repeated emulator cold-boot
campaign, or emulator Level 1-to-Level 2 transition was performed. Level 2/audio
preservation is supported by unchanged files and passing loader/scheduler/gameplay
regressions, not a new hardware claim. Owner playtest should cover the transition,
WDEATH, music/SFX and sustained flame on the intended hardware/emulator. The HLE
emulator smoke run is limited evidence, not hardware equivalence certification.

## Build and publication

No usable Actions dispatch tool is available; local `gh` authentication reports
an invalid GH_TOKEN. No Actions artifact is claimed.

In GitHub Actions open **Manual Saturn playtest build** (`.github/workflows/build.yml`):

1. **Run workflow → Use workflow from:** `optimization/level1-legacy-sprite-cleanup`.
2. **profile:** `stage-default`.
3. **source_ref:** the full pushed commit SHA shown in the delivery message
   (or this branch's exact current tip).
4. Run and wait for the native build, `make check`, and `make test` to succeed.
5. Download `mullet-force-stage-default-<resolved-full-SHA>` from the run's
   artifacts. Keep its BIN and CUE together. Artifact retention follows the
   existing workflow (one day).

Local reproduction: `bash tools/setup.sh`, install the README host dependencies,
`bash tools/build-stage.sh --native`, `make check`, `make test`.
Stop after Phase 1; the other 83 legacy definitions remain untouched.
