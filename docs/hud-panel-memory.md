# Phase 4: generated HUD panel memory

Branch: `optimization/level1-hud-panel-memory`.
Exact parent/fallback: `279e33d2f60645b12cf479ba3b096954565a0173` on
`optimization/level1-duplicate-texture-cleanup`. Phase 3 is a working candidate,
not a newly approved THE ONE baseline; hardware testing of both players remains
outstanding. No THE ONE tags created, moved or deleted, no merge and no next phase.
`the-one-ai3-baseline` remains `15387a314a51bffbe3e65152e45958ed5f3416c5`.
The delivery message identifies the full commit containing this report.

## Resource and investigation

`src/main.c:load_assets` generates the RGB555 `panel` sprite immediately after the
80x8 health-fill `bar`. Panel ID remains 28; its original allocation began at
VDP1 offset 124928 (`CMDSRCA=0x3d00`). Original width 256, height 40, allocation
20480 bytes. It has no palette; every pixel is opaque/nonzero RGB555. The first
and last rows are `JO_COLOR_RGB(124,66,112)` (0xb90f), all other rows
`JO_COLOR_RGB(12,18,34)` (0x9041). Every row is horizontally constant; no vertical
border or horizontal detail exists. Original width supplies the overlay's
full width directly and the denominator for health-bar scaling.

All references were inspected:

- `health_bar` stretches the same panel to 80x8 for Buck/enemies and 88x8 for
  Chuck, then composites the unchanged health-fill texture over it. Partial/zero
  health affects only that fill, not the panel geometry.
- `draw_game` uses the full panel behind pre-start, pause, stage-clear and Level 2
  entry text. Its layer is 180; health-background layer is 185 and fill layer 180.
- `mf_gallery_load(panel)` uses the handle only to calculate the preceding RGB555
  allocation end; it does not draw or sample the panel. Subsequent gallery and
  preview content is independent.

There are no crop/tail views into the panel. Both actual inventories check this;
all 14 existing views remain within their original retained owners. The panel
has no runtime pixel/metadata writes or resource-sharing consumers beyond these
references. All retained resource IDs remain unchanged.

## Implementation and rendering proof

The panel is now **8x40 RGB555 / 640 bytes**, the minimum legal texture width.
The pinned Jo allocator encodes width in units of eight in the VDP1 SIZE field;
8x40 is SIZE 0x0128, versus original 0x2028. Allocations align to 32 bytes; both
sizes are already aligned. The existing temporary CPU buffer allocation remains
unchanged, including its 80x8 health-fill storage: no heap-saving claim or unrelated
heap-layout change is included.

`MF_HUD_PANEL_MEMORY` defaults off, requires the complete Phase 3 profile, and is
enabled only by the production stage-default wrapper. Historical profiles keep
the old dimensions/drawing. Counts and per-stage absolute budgets are updated;
source assets, other generated textures and definitions remain intact.

Health backgrounds retain the **same vertical source size and scaling**. Horizontal
scale is 10 for width 80 and 11 for width 88 rather than 80/256 and 88/256. These
products are exactly equal in 16.16 fixed point, without rounding changes.
Real native SGL/VDP1 command captures confirm identical destination coordinates,
flags, color mode, source address and ordering, changing only texture SIZE. Since
every source row has one color, all horizontal samples return that same color;
vertical sampling and skew/edge behavior are unchanged. No extra draws or tiling.

The full overlay uses **one explicit four-point quad**. This is necessary to match
the actual Phase 3 raster, not just a nominal 256x40 bounding box:

- Phase 3 emits a center-center scaled sprite command `CMDCTRL=0x0a01`, A=(0,64),
  B=(255,39), PMOD=0x00a8, source=0x3d00, SIZE=0x2028. With local origin (160,120),
  its inclusive destination is **x33..288, y165..204**. The center anchor subtracts
  truncated halves of size-1: 255/2=127 and 39/2=19.
- Phase 4 emits an axis-aligned distorted sprite (`CMDCTRL` low nibble 3), with
  relative corners **(-127,45), (128,45), (128,84), (-127,84)**, same depth, PMOD,
  color setting and source address, SIZE=0x0128. These are exactly the same four
  inclusive destination corners. There is no rotation workaround, floating scale,
  interpolation of colors, changed clipping region, or additional draw command.

Both paths therefore cover the same rectangle, with the same 40 source rows.
Only horizontal source sampling changes across constant-color rows. All HUD
rectangles remain inside the existing screen/user clipping bounds; world camera
and parallax do not affect these screen-space coordinates. Pixel data is nonzero
and opaque, and end-code/color-mode settings are unchanged. Full native emulator
screens and active command chains were compared as additional evidence. This is
not a claim of real-hardware validation.

### Rejected prototypes / investigated differences

A simple 32x horizontal scale through `jo_sprite_draw3D` was rejected: Jo selects
`slDispSpriteHV` for nonuniform scale and uses angle 1 to work around its angle-zero
bug. It changed overlay edge/border pixels (1319 differences in the inspected
stage-clear frame; six captured overlay frames differed). Health backgrounds
matched. A first quad using nominal x32..287/y164..203 also failed (1098 differing
pixels in the inspected frame). Raw VDP1 command capture established the actual
center-anchor bounds above. The corrected quad matches those original bounds;
no expected image was edited or pixel difference ignored to pass the comparison.

## Exact memory result

| Build | Definitions | Texture bytes | Free bytes |
|---|---:|---:|---:|
| Phase 3 | 152 | 276864 | 181624 |
| Phase 4 | **152** | **257024** | **201464** |
| Recovered | **0** | **19840** | |

138 payloads and all 14 views remain. No other texture shrank or disappeared.
Cumulative recovery from the original AI 3.0 allocation: 103 definitions and
195776 bytes. There is no enemy-bank architecture or gameplay change.

## Validation

- Native `bash tools/build-stage.sh --native`: passed with unchanged SDK pin
  `556d081146211b6a1cfa6591d70f9487d406758b`; matching production BIN/CUE generated.
- `make check` and `make test`: passed, including original immutable baseline
  chains, Phase 1/2/3 checks, disc/export validation and current actual loader /
  renderer tests. Inherited tests cover attacks/FF+A, both players, AI 3.0,
  two-enemy limit, natural 40-KO progression, parallax/neon, audio/flame sustain,
  WDEATH/readiness/E108 repair, wingsuit controls and fresh/warm mock reloads.
- Actual allocation audit: exact table above, same IDs/order, unchanged dimensions /
  formats / registration palettes for every other resource, bounds/nonoverlap,
  physical end and all view ownership verified. `--phase3` restores 152/276864;
  older counterfactual profiles retain their exact historical allocations.
- Expanded host semantic test: **7666 cases / 150855 draws**, including **16864
  panel draws**, actual Phase 3 versus Phase 4 and disabled profile. All non-panel
  texture hashes, transforms, positions, depth/order, complete palette banks, text
  and clears match. Panel comparison preserves exact native fixed-point geometry
  and every RGB555 row color, accounting for the actual center-anchor rule above.
  Cases include both actors/facings/all animations/attacks and **360 additional HUD
  scenes**, all five modes, one/two players, six full/damaged/dead health values,
  score 0/12345/999999, kills 0/39/40, debug off/on. Separate cases cover every
  player health fill 0..100 at widths 80/88 and every enemy health 0..6. UBSan used.
  Diagnostic VDP1 counters must change to the exact true budget; only those expected
  numeric strings are normalized. Both host profiles use the same build metadata;
  production build/provenance identifiers naturally reflect the new commit.
  No gameplay HUD text/pixel difference is allowed.
- Production Yabause comparison directly against exact Phase 3: **600 full Level 1 /
  stage-clear snapshots and 30 complete screens** match at equal wall frames;
  **555 Level 2 states / 545 complete screens** match at equal gameplay ticks.
  Raw wall-frame comparisons also have **zero state or image mismatches**.
  Both builds enter Level 2 gameplay at frontend frame **1844**, install the same
  28-definition Level 2 bank (last ID 27), and report zero errors including no E108.
- Transition uses the existing development X shortcut at frame 1500, followed by
  real settling/clear, VBlank drain, sprite teardown, Level 2 initialization,
  WDEATH and sound readiness. No emulator RAM writes or safety-check bypasses.
  This is not a natural 40-KO completion run.
- Additional isolated **native HUD raster fixtures**: **180 complete screens,
  zero mismatches**, covering one/two players × five modes × health
  0/1/25/50/99/100 × three score/kill combinations. These temporary binaries use
  the actual loader, `draw_game`, SGL, VDP1, fonts, backgrounds and compositing,
  replacing only update with deterministic test scenes. They are not the playable
  BIN/CUE. Active command-list validation (follow ASSIGN, stop at END, exclude
  stale table slots) checks **144 overlay pairs / 600 health-background pairs**;
  all expected geometry/settings match, with no added draws. A test-reader COFF
  duplicate-symbol issue was corrected by ignoring undefined/absolute records.
- `git diff --check` and Python/shell syntax checks: passed.

All emulator runs used Yabause libretro
`8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, software/interpreter, one thread, no
cartridge, HLE BIOS, fresh saves. Production comparison uses the unchanged
`tools/test-legacy-sprite-runtime.py`: pass Phase 3 files via its legacy
`--phase1-cue`/`--phase1-program` arguments and the current production files via
`--phase2-cue`/`--phase2-program`. Isolated HUD raster reproduction:

```sh
python3 tools/test-hud-panel-runtime.py \
  --core /path/to/yabause_libretro.so \
  --include /path/to/libretro-common/include \
  --out /tmp/fresh-hud-fixtures
```

It builds temporary TEST-ONLY fixture sources and preserves raw frames, native
command tables and `comparison.json`; production sources/build are untouched.
The frontend reads save states only, without RAM writes. `--resume` reuses matching
fixture sources after checking their renderer/config/loader against the expected
baseline/current files, and writes fresh verified captures.

## Changed files and preservation

Runtime: `src/main.c` (panel generation width, health scale denominator, one quad),
`src/arcade_fx_config.h` (guarded flag/width/budget), `src/animation_preview.c`
(accounting subtraction only). Build/audit: `tools/build-source-complete.sh`,
`tools/build-native.sh`, `tools/audit-sprite-memory.py`, `Makefile` and new
`assets/hud-panel-memory.json`. New checks: `tools/validate-hud-panel-memory.py`,
`tools/test-hud-panel-memory.py`, optional `tools/test-hud-panel-runtime.py`, and
`tests/hud_panel/{jo/jo.h,trace.c,scenarios.inc,emulator-fixtures.inc}`. This report.

The scope gate reverses only the three exact reviewed main integrations and checks
all remaining main bytes against Phase 3. Animation source matches after removing
only the HUD-budget subtractions. All other existing files are frozen byte for
byte, including game/input/player/AI/audio/Level 2 code and assets. No audio,
attacks/buffering, animation timing, HUD layout/text, joining, stage progression,
enemy counts or background changes. The quad change adds no draw commands;
no Saturn hardware performance benchmark is claimed.

## Remaining caveats

No real Saturn tests, audible listening comparison or natural 40-KO emulator
completion was performed. The hardware argument rests on identical destination
bounds/settings, unchanged vertical sampling and horizontally constant colors,
with native command captures and complete-screen emulator tests as evidence.
Emulator equivalence is not hardware certification. Owner playtest should still
check both players, damaged HUD and all overlays on the intended Saturn setup.
Phase 3 remains intact as the fallback; no new THE ONE approval is implied.

## Build publication

No workflow dispatch tool is available; local `gh` authentication reports an
invalid GH_TOKEN. No downloadable Actions artifact is claimed. Open **Manual
Saturn playtest build** (`.github/workflows/build.yml`), then Run workflow:

- Workflow branch: `optimization/level1-hud-panel-memory`.
- `profile`: `stage-default`.
- `source_ref`: the full pushed commit SHA in the delivery message.

Wait for native build, `make check` and `make test`. Download
`mullet-force-stage-default-<resolved-full-SHA>`, keep BIN/CUE together; existing
retention is one day. Local production build: `bash tools/setup.sh`, README host
prerequisites, `bash tools/build-stage.sh --native`, `make check`, `make test`.
Stop after Phase 4.
