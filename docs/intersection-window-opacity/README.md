# Receding-street window opacity correction

Starting branch: `art/level1-intersection-detail-pass`.
Approved starting commit: `e270d2dd8461475185be6eac503ce0c0f874974b`.

The native `EXTPIX.BIN` source contained index-zero pixels inside the narrow
window openings above row 56. Index zero is transparent on NBG1, so the existing
quarter-speed NBG2 skyline was visible through them. This is a source-index
problem; no palette, layer priority, transparency mode or runtime code changed.

The repair replaces **233 index-zero pixels** within explicitly bounded openings
with existing opaque index **224** (`0x8400`, RGB555 **0,0,1**). There is no exact
RGB555 black entry in the approved palette: this is its darkest existing
near-black ink, rather than adding a color or changing a palette entry. All
nonzero source pixels remain byte-identical, preserving the lit panes, jambs,
mullions, shadows and architectural highlights. One inspected opening already
contained no transparent pixels and needed no changes.

The complete hotel, record store, residential artwork, road, skyline source,
older 1280-pixel panorama, palette/animated entries, character assets, all native
runtime source, audio and Level 2 remain byte-identical to the approved commit.
Only EXTPIX and its lossless packed derivatives/generated decoding table change.
No merge or THE ONE tag modification.

## Review

- [Native before/after screenshots](native-before-after.png), captured from the
  production disc in Yabause. Both show **camera 1469**, rendered world origin
  **1468**. The static facade pixels were matched exactly to account for video
  callback timing versus end-of-frame telemetry; actors and HUD values differ.
- [Before screenshot](before.png) / [After screenshot](after.png).
- [Background-only same-camera comparison](background-only-before-after.png).
  This supplemental source/map rendering omits HUD and actors and decodes the
  unchanged skyline map at the same quarter-speed scroll. It is not an emulator
  screenshot or a paint-over of the user's screenshot.
- [Unobscured left windows](source-left-before-after.png) /
  [unobscured right windows](source-right-before-after.png).
- [Native left crop](left-windows-before-after.png) /
  [native right crop](right-windows-before-after.png), including the normal HUD.
- [Exact changed-pixel mask](changed-pixel-mask.png), red marking edits;
  [source proof](../../art/intersection-window-opacity/proof.json) and
  [opening bounds](../../art/intersection-window-opacity/openings.json).

The camera was selected to match the supplied intersection view. No screenshot
was edited to simulate the fix. The replacement pixels are opaque against every
skyline position; the mask cannot change pixels outside the selected interiors.
Visual/hardware acceptance remains with the user.

## Memory

[Measured source/manifest comparison](memory-comparison.json):

| Resource | Approved | Corrected | Change |
|---|---:|---:|---:|
| Source tiles | 5,369 | 5,370 | +1 |
| Packed source | 225,892 B | 226,008 B | +116 B |
| Background heap owner | 294,204 B | 294,320 B | +116 B |
| Decoder/cache suffix | 68,308 B | 68,308 B | 0 |
| Static source/tables estimate | 34,414 B | 34,412 B | -2 B |
| VDP2 resident cells | 106,496 B | 106,496 B | 0 |
| Total reserved VDP2 | 434,176 B | 434,176 B | 0 |
| VDP1 textures | 371,072 B / 177 definitions | unchanged | 0 |
| Palette allocation / SCSP | unchanged | unchanged | 0 |

The fixed Jo heap remains 393,216 B. The owner plus the 16,384 B load-time map
buffer fits with 82,512 B spare. The full fixed allocator stays below SGL sort
work at `0x060c0000`; linked end stays `0x060b23f4`, below actual SDK vertex work
`0x060e5784`. The protected Buck/Chuck 49,152 B texture reserve is untouched.

## Reproduce / validate

```
python3 tools/apply-intersection-window-opacity.py
python3 tools/prepare-intersection-window-opacity.py
PATH="$PWD/.deps/iso-tools/usr/bin:$PATH" bash tools/build-stage.sh --native
make check
make test
```

The current validator compares every pre-existing tracked file with exact
`e270d2d`, allowing only the indexed background payloads, generated header and
Makefile validation routing to change. Historical proofs run on their exact
archived assets. Tests check deterministic repair/packing; every-camera decoder,
ring wrap and reloads; palette/skyline/VRAM guards; current combat/render tests
under UBSan; owner allocation/read/size failures and eight reloads/retirement.

[Native traversal](native-traversal.json) reaches camera 1600, returns to the
1280 checkpoint, exercises three-enemy combat and records zero asset/background
errors. [Independent cold starts](cold-starts.json) match 600 Level 1 state
snapshots / 30 images and 556 Level 2 ticks / 546 images, with no mismatches;
compressed owner and decode cache retire before Level 2. These use normal
controller inputs, read-only observations, and the approved developer stage skip,
not RAM writes, healing, teleportation, hardware tests or a natural KO clear.

Native review reproduction:

```
python3 tools/test-full-detail-runtime.py --core .deps/recovery-yabause/yabause/src/libretro/yabause_libretro.so --include .deps/recovery-yabause/yabause/src/libretro/libretro-common/include --out work/window-opacity-new/runtime
python3 tools/preview-intersection-window-opacity.py --before work/full-detail/runtime --after work/window-opacity-new/runtime
```

The `--before` directory is a traversal captured from the approved production
disc, retained locally; the committed screenshots and matching-camera report
preserve its review evidence. Output directories for emulator runners must be
new/empty.

## GitHub Actions manual build

Workflow: **Manual Saturn playtest build**.
Use workflow from: **art/level1-intersection-detail-pass**.
`profile`: **stage-default**.
`source_ref`: **the full final correction commit SHA reported with delivery**.
Artifact: `mullet-force-stage-default-<full SHA>` (one-day retention).
