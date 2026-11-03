# Chuck running denim/waist cleanup

Branch `chuck-run-denim-waist-cleanup`, based on validated `0fbc5fbb6918446368187603b7f3e49d411af93a`. No merges or changes to protected branches.

## Exact source corrections

Both defects are baked into native frame pixels, not extra sprite layers or draw calls. The runtime draws the three existing run pieces plus its shared carried-bat texture. This task changes no C source, renderer, anchor, palette or animation mapping.

- Frame 3 (index 2): remove the remaining two-column blue strip at x51–52, y23–34, just outside the previous x53+ patch. The upper section uses skin pixels from approved frame 1 at the same native coordinates; the lower dangling end becomes transparent. Exactly **24 pixels** change. The previously retained edge was not a necessary part of the vest armhole: adjacent frames show uninterrupted exposed shoulder in this region.
- Frame 4 (index 3): replace the flat blue band at y42–43, x57–81 with the existing frame-1 belt/shirt pixels registered +2px horizontally and −2px vertically to its existing buckle. Exactly **44 pixels** change. This preserves the existing frame-4 buckle top, correct waist silhouette and its approved torso/hip position; no pelvis or sprite root moves.
- Frames 1 and 2 remain pixel-identical. Every pixel at y44 and below is unchanged in all four poses, preserving the approved legs and stride. The rear glove/grip neighborhoods and bat anchors are identical. Hair, face, sunglasses, free arm and native body proportions are untouched.

The matching running-bat preparation crops receive the same native-coordinate patches. This prevents the remnants reappearing during the first attack ticks. Six existing payloads are replaced: RD0/RD1, RN22, COMBAT/DT0/DT1 and COMBAT/CA55. No new texture paths, definitions or uploads are introduced. All original source files and earlier derivative art are preserved; new derivatives live in `assets/chuck-denim-cleanup/`. No character generation was used.

## Build and exact memory

```
bash tools/build-chuck-denim-cleanup.sh --native
# Or omit --native for the pinned Docker build.
```

Isolated disc-copy option `MF_CHUCK_DENIM_CLEANUP=1` requires the approved HQ player-death profile. With the option disabled, the existing `build-player-death.sh` reproduces the previous bank. Every replacement preserves its predecessor's complete TGA header, palette, dimensions, file length and every raw index outside the recorded patch mask. Runtime source and texture IDs are unchanged.

| Allocation | Before | After | Change |
|---|---:|---:|---:|
| VDP1 texture pool used | 446,304 | 446,304 | 0 bytes |
| Free in 458,488-byte pool | 12,184 | 12,184 | 0 bytes |
| Payload textures | 239 | 239 | 0 |
| Existing zero-payload views | 14 | 14 | 0 |
| Definitions / limit 255 | 253 | 253 | 0 |
| Additional palettes | 0 | 0 | 0 |

VDP2 and sound RAM are unchanged. No per-frame CD reads, cache, animation changes or duplicate uploads. Buck run, approved hurt/death, Corporate Punk, combat, SFX and music assets are checksum-locked unchanged.

## Validation

- `make check`, `make test` and the native SH-2 BIN/CUE build pass.
- Exact native reconstruction from the active Saturn pieces matches the edited PNGs. Historical source-bank checks remain active: the ISO validator first verifies all six actual replacement payloads exactly, then normalizes only those verified equal-sized entries to their predecessors for the existing historical checks. No validation is skipped.
- Source locks prove every file under `src/` is unchanged, along with approved run, hurt/death and attack banks. All prior gameplay/audio/character validators still pass.
- Native Yabause HLE/software rendering: controller-only P1/P2 run and running-bat scenario compared with the downloaded previous approved BIN/CUE, without emulated RAM writes or injected damage. All 16 actor/run-frame/facing combinations and **17 carry-to-swing samples** pass. Dash, jab and running-bat traces are identical to control.

Runtime comparison: **705 identical gameplay snapshots**, **362,352 matching native sprite pixels**, and **20,087,986 unchanged pixels outside the permitted character regions**. Runtime counters confirm the exact memory/definition table, unchanged CRAM and stable texture VRAM.

## Review files

`assets/chuck-denim-cleanup/` contains:

- Transparent native PNGs for all four frames.
- Native and 4× nearest-neighbor before/after contact sheets.
- Frame-3 shoulder and frame-4 beltline close-ups, including development-only masks (native and 8×).
- Four-frame 100ms-per-frame offline GIFs in both directions, preserving the existing six-tick-at-60Hz preview cadence.
- Manifest with all 68 changed native coordinates and six payload provenance records.

`docs/chuck-denim-captures/` contains actual controller-driven full-scene Yabause GIFs, Chuck run/attack screenshots in both directions and validation JSON. Offline art previews and actual captures are explicitly named. Pixel checks exclude genuine screen clipping, HUD and opaque nearer-actor occlusion; repeated run phases and attack transitions are exercised without changing game controls or logic.

No WebRetro, physical Saturn, SAROO/optical-drive or real-hardware performance claim is made. This remains a surgical visual-review build; final aesthetic approval is by playtest. Approved hurt and death artwork are not altered or regenerated.
