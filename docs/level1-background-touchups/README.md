# Level 1 background touchups — visual-review candidate

Parent: approved Ricky tattoo build `fa4a56b6df13df6eaeaf0f38676e2de448321217`.
Development branch: `art/level1-background-touchups`.
No merge or THE ONE tag update. Visual approval remains pending.

## Review previews

- [Full 640×240 background before/after](full-before-after.png).
- [ION ARCADE sign before/after, 6× nearest-neighbor](ion-arcade-before-after.png).
- [VINYL post before/after, including intact lower post](vinyl-post-before-after.png).
- [Matching gray-strip correction beside MULLET FORCE](mullet-post-before-after.png).
- [Three repair regions marked on the full background](repair-regions.png).
- Native production Yabause: [left/MULLET view](native-left-view.png),
  [ION ARCADE/VINYL view](native-ion-vinyl-view.png), [verification report](native-report.json).
- Unobstructed source images: [before](before.png), [after](after.png).

The ION ARCADE lettering, neon frame/corners and existing animated color indices
are retained. Only the dark right-hand interior patch receives a continuation
of the sign's existing blue-to-purple shading, using the original palette.

The annotated VINYL strip and one matching strip beside MULLET FORCE are removed
above source row 104; the lower posts from row 104 down are untouched. Restored
masonry uses adjacent brick/mortar row colors and lighting, with subtle grain
from existing brickwork on the same source row. Lamp fixtures, brackets, door
frames and intentional structural columns remain intact. No other confirmed
instances were found in the full 640×240 inspection; skyline antennas and other
architectural verticals were retained.

## Exact scope and pipeline

The authoritative indexed source remains `assets/city-cleanup/CIPIX.BIN`.
`TOUCHUPMASK.BIN` records only these three repair regions. Original indexed
source, cells, maps, palette and cleanup mask are preserved under
[`art/level1-background-touchups`](../../art/level1-background-touchups/).
The original ION letters and all pixels outside the new mask remain byte-exact.
Only 1,037 of 153,600 indexed source pixels change.

No entire-background generation or global palette quantization is used. A local
sign restoration study informed the color continuation; final edits use existing
palette indices under explicit masks. `tools/prepare-level1-background-touchups.py`
reproduces those indexed edits and invokes the existing
`tools/build-city-cleanup.py` cell/map/chunk packer. The packer now asserts the
exact original allocation instead of merely checking that the bank has room.
The generated maps and chunks are also byte-identical to the parent.

| Resource | Before | Candidate | Change |
|---|---:|---:|---:|
| Source dimensions | 640×240 | 640×240 | 0 |
| Actual unique 8×8 tiles | 1,664 | 1,664 | 0 |
| VDP2 facade cell bytes | 106,496 | 106,496 | 0 |
| Facade map bytes | 16,384 | 16,384 | 0 |
| Chunk-table bytes | 4,800 | 4,800 | 0 |
| Skyline cells/map bytes | 32,768 / 16,384 | 32,768 / 16,384 | 0 |
| Palette payload | 510 bytes | 510 bytes | 0 |
| Additional VDP1/VDP2/CRAM allocation | — | — | 0 |

Palette bytes and entries, all prior neon pixel indices and animation code,
skyline parallax assets/code, props, gameplay, characters including the approved
Ricky tattoo, AI, music/SFX and Level 2 are unchanged. No runtime source file or
generated memory-budget header changes.

## Validation

- Byte-reproducible indexed edit/packing and strict repair-mask preservation.
- Every source pixel decoded from the actual packed cell/map payload; all chunk
  entries checked; exact original tile count, map/chunk bytes and palette.
- Native `stage-default`, `make check`, `make test`.
- Current-disc validation checks every staged file (including characters/audio
  and nested Ricky resources), source checksums, executable source fingerprint,
  background maps/cells and unchanged parallax payloads.
- Historical source/asset locks and automated suites run unmodified on the exact
  approved parent archive. Current gameplay/characters/audio/Level 2 files must
  match that parent byte-for-byte. The changed current disc is checked by the
  new background validator, rather than claiming it matches historical pixels.
- Production Yabause HLE, normal Start/Right/Pause controller input, no emulator
  RAM writes. Captures at camera 0 and 320 verify exact loaded VDP2 cells, maps,
  skyline and static palette; five different neon-palette phases observed;
  asset error 0 throughout. Subjective visual/hardware approval remains pending.

Commands: `python3 tools/prepare-level1-background-touchups.py`,
`python3 tools/preview-level1-background-touchups.py`,
`bash tools/build-stage.sh --native`, `make check`, `make test`.
The Yabause harness is `tools/test-level1-background-runtime.py` (requires the
existing pinned core and libretro include directory).

## Exact Manual Saturn playtest build settings

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).
Use workflow from: **art/level1-background-touchups**.
Profile: **stage-default**.
`source_ref`: the full candidate commit SHA in the delivery report.
Download `mullet-force-stage-default-<full SHA>` and keep the matching BIN/CUE
pair together. Artifact retention is one day. No automatic dispatch or merge.
