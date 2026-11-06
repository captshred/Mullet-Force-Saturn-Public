# Level 2 night palette and CRAM registration

Branch: `art/level2-night-palette-pass`. Parent: current improved top-down city `ad83025f3558fd11d934367bb74416e70814339c`. The new SHA is supplied in the delivery response. No Actions dispatch or workflow change.

## Why roads and shadows were pink

This pass found a **Level 2 full-palette upload error**, beyond the requested art balance. The pinned Jo Engine allocator starts `jo_palette.data` at **CRAM entry257** (`CRAM_PALETTE_SIZE + 1`), skipping transparent color0. Native Level 2 8bpp pattern names use palette bank1, which begins at **entry256**. `WPAL.BIN` contains all 16 entries including color0, but Level 2 copied it at the SDK's color1 pointer. Consequently native index12, used for roads and shadows, read file entry11: the old bright-pink color.

The prior host previews indexed `WPAL[index]` directly and the old loader mock incorrectly supplied `cram+256`; those checks missed the actual SDK offset. A new host comparison using the real entry257 upload reproduces the reported pink roads and building-edge masses. This is a source-level/CRAM-lookup reproduction, not a captured emulator frame.

The Level 2 loader now explicitly clears and uploads from **bank1/entry256** and validates that the passed SDK pointer is entry257. Its seven-bank clear covers exactly entries256..2047. The parent clear started at257 and extended through2048; correcting the base removes that one-entry overrun too. Font bank0 and post-CRAM guard words remain untouched. The SDK and Level 1 palette handling are unchanged; their convention is appropriate for palette buffers that omit color0, unlike the full Level 2 palette.

## Night materials

The stage retains its six aerial sites, building silhouettes, roof equipment, damage, street layout and complete-building parallax. This is a material/color refinement, not a geometry redesign.

Sixteen RGB555-friendly colors now provide these roles (RGB values before native packing):

| Index | Role | RGB |
|---|---|---|
|0|Transparent source color|0,0,0|
|1|Deep alleys/gaps|8,16,24|
|2|Shaded wall/structure|24,24,32|
|3|Cool steel roof|40,48,56|
|4|Concrete roof/panels|56,64,72|
|5|Machinery/parapet midtone|80,96,104|
|6|Restrained edge highlight|112,128,136|
|7|Faded amber road markings|152,136,96|
|8|Dim cyan windows/skylights|24,64,72|
|9|Reserved subdued cyan accent|48,96,112|
|10|Cast shadow|8,8,16|
|11|Collapsed-roof cavity|8,8,8|
|12|Dark asphalt|16,16,24|
|13|Tar/asphalt rooftop|24,32,40|
|14|Neutral paving/sidewalks|40,40,48|
|15|Reserved rust-red warning accent|136,72,56|

Values are quantized deliberately to native 5-bit channel steps. The effective palette contains no hot pink or magenta. Existing amber markings and cyan details remain sparse. No new light positions are added; character colors, hostile pink bullets and all other gameplay effects remain their original RGB555 assets.

Material indices now distinguish cast shadows from roads, collapsed voids from asphalt, and paving from tar roofs. Existing concrete wear, corrugation, machinery shading and edge lighting use the refined palette. Their pixel positions are unchanged. After mapping the three separated classes back (10/11->12, 14->13), the complete decoded native image of **each layer hashes identically to the parent**. Authoring metadata also matches exactly. This verifies the same geometry and surface-detail positions despite native tile deduplication/ID changes.

## Layer, gameplay and audio preservation

The full production `render()` function, sprite-state setup and entire frame/gameplay/audio driver are byte-identical to the parent. NBG1/NBG2 priorities, windows, movement rates and transparency remain identical. NBG1 retains normal camera motion; complete elevated buildings retain **9/8 horizontal speed**, maximum **+/-6px** relative displacement and the same vertical phase as the ground. No structures can drift or detach through a change of scrolling behavior in this pass.

Camera/gameplay source files remain unchanged: world320, viewport224/X48..271, camera initial48 and clamp0..96, exactly48px travel each way, existing dead zone and max3px/tick. Level 1, transitions/Stage Clear, X skip, controls, aiming, collision, HP/damage, HUD, sprite art and all audio are unchanged. The original confirmed Level 2 polyphonic sound sources/banks/metadata remain byte-identical to `78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e`. No music change.

Exact additive preservation is recorded in `docs/level2-night-lock.json`; earlier locks remain unchanged. `tools/level2_night_scope.py` authorizes only the exact new asset/source/test digests. It also freezes the V2 documents, geometry hashes, authoring layout and complete render/frame/sprite-state/audio-load sections.

## Resource impact

| Resource | Top-down V2 parent | Night pass |
|---|---:|---:|
|Palette entries / CRAM payload|16 /32 bytes|16 /32 bytes|
|Ground tiles / bytes|576 /36,864|578 /36,992|
|Raised tiles / bytes|194 /12,416|194 /12,416|
|Map bytes|16,384|16,384|
|VDP2 background payload|65,664|**65,792**|
|VDP2 reservation|434,176|434,176|
|Unreserved VDP2 headroom|90,112|90,112|
|Unused transferred arena bytes|106,368|106,240|
|VDP1 textures /definitions /max commands|28,032 /18 /73|28,032 /18 /73|
|SCSP high-water /free|307,260 /217,028|307,260 /217,028|
|Gameplay state|1,492|1,492|

Separating previously shared shadow/asphalt characters requires **two additional 64-byte ground cells**, only **128 bytes**. No additional palette bank, VRAM reservation, VDP1/SCSP allocation, mutable gameplay state or per-frame work. A0/B0 placement and all layer formats remain unchanged. The loader correction uses the same 32-byte file and exact existing seven stage banks.

`WPAL.BIN`, `WCELL.BIN`, `WMAP.BIN`, `WROOF.BIN`, manifest and generated ground byte count advance. `WRMAP.BIN` stays identical. Runtime file count remains26 and total payload is252,292 bytes. A focused `.gitattributes` entry marks `WCELL.BIN` as binary: newly used palette-index10/13 bytes are literal LF/CR values, not source whitespace or line endings.

## Verification and visual review

- Full `make test` passed **245 PASS reports**. The final focused suite passed **65 PASS reports**, including UBSan, camera/coop/gameplay, audio mixing/readiness, rendering, loading, ISO and staging checks.
- The real SDK contract is now represented in C: `palette.data=cram+257`, physical bank1 at256. Tests compare the complete loaded palette bytes at256 and verify entry255/font, entries2048/2049 guard words, all cleared stage-bank ranges and invalid-pointer E100 rejection.
- A mutation test deliberately restored the parent's palette upload/clear at257; the new loader test rejected it. The Python CRAM model independently reproduces old pink index12 and verifies every used native palette lookup after alignment.
- Native decoded material-class normalization proves identical geometry on both planes; six sites, full masks, wrapping, complete raised objects, every fixed-point camera sample and parallax checks remain active.
- Actual RGB/luminance tests require cast shadows < alleys < asphalt < paving < steel < concrete < trim; all16 palette values are unique and none is hot pink/magenta. Upper index0 transparency and opaque lower coverage remain intact.
- Palette/material regeneration is byte-identical. The palette change does not introduce new art shapes or unrelated assets.
- Native build and `make check` validate matching BIN/CUE, exact runtime payloads and preserved Level 1. `git diff --check` treats the native cells as binary and passes.

Host composites were visually inspected, including a source/SDK-accurate old-versus-new comparison, the new scene with original sprites, and camera/scroll review images. Roads now resolve to dark asphalt, shadows to darker charcoal/blue-black, paving to neutral slate and roofs to distinct steel/concrete/tar values. Existing weapons remain readable.

These exports are **host composites, not emulator screenshots**. The palette lookup defect is reproduced from pinned source and native data; audible behavior, actual hardware display/timing and final nighttime color balance still need manual WebRetro confirmation.

Review exports (ignored `build/night-palette-review/`): `host-cram-before-after.png`, `host-readability.png`, `host-contact-sheet.png`, individual `host-view-*` images and `host-pan.gif`. The before image intentionally models the parent's shifted CRAM lookup; it does not reuse the earlier misleading direct-palette preview.

## Build and manual settings

With README prerequisites installed:

```sh
bash tools/setup.sh
bash tools/build-level2-wingsuit.sh --native
make test
make check
```

The normal build consumes committed native assets. Deliberate palette/material edits use `python3 tools/build-topdown-city-v2.py`; source colors and material roles are authored there. In this environment host ISO tools under ignored `.deps/host-tools/usr/bin` are added to PATH for build/check commands.

Keep matching `build/mullet-force.bin` and `build/mullet-force.cue` together and open the CUE (MODE1/2048).

Manual GitHub Actions: **Use workflow from `main`; Profile `stage-default`; Source ref = the exact new delivery SHA**. No workflow is dispatched automatically.

WebRetro: enter Level 2 via X and check roads/shadows, all six sites over a full vertical cycle, left/center/right camera positions, coherent parallax, upper transparency, HUD/font colors and sprite/projectile contrast. Check Shots + held Flame + overlapping Explosions, coop, pause/restart and normal Stage Clear entry. The geometry and movement are preserved; this palette pass awaits visual confirmation on the actual build.
