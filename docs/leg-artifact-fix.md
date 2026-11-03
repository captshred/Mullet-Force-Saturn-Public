# Localized running-leg artifact repair

Branch: `dash-leg-artifact-fix`, created from verified `aae373fb6fe1b7d0ca63210a071a8bb85ad500c8`. The named branch did not previously exist locally or remotely; that commit was on `dash-alternating-stride-fix`. Previous branches are preserved. No merges.

## Confirmed cause and native repair

The old upper-art preservation step pasted rows 0–47 from the original run prototypes over the corrected two-leg composition. In frames 2 and 4 those rows included part of the old high knee and forward thigh. These old pixels produced extra knee/thigh fragments above the actual new knee, especially in frame 4. This was an artwork compositing defect, not a texture-allocation problem.

The fix adds four explicit native repair mattes. Inside those small hip/upper-leg areas, the converter now retains the existing two-leg underlay instead of restoring the stale old knee. It reuses the approved leg pixels and palette rather than redrawing the character or generating a new cycle. A targeted edited cleanup reference is retained for visual comparison; actual shipped patches are constructed from the existing native leg layers.

| Fighter | Frame2 changed pixels | Frame4 changed pixels |
|---|---:|---:|
|Buck|113|130|
|Chuck|103|140|

Total: 486 pixels across four frames. All changes are within x54–89/y43–47 of the 128×96 canvas. Frames 1 and 3 remain entirely pixel-identical to aae373f. Every pixel above row43, every pixel below row47, and every pixel outside the explicit mattes remains identical. This preserves head/face/hair/upper costume, actual knee/shin/boot placement, forward lean, scale and ground anchor. The corrected near/far leg layers and alternating sequence are unchanged. Two contact frames remain on the original ground line; recovery/push-off phases retain their approved clearance.

The generator's broad horizontal lock now has explicit stale-leg exclusions, preventing regeneration from pasting the artifacts back. Regression checks require the known ghost kneecap locations to be transparent and reconstruct each final frame from the same two leg chains plus the protected body artwork. Native and enlarged sheets have been visually inspected for two coherent leg chains and two boots per pose.

## Preserved gameplay and build

No changes to game/input/combat/animation-clock code, speed 1.7×, 12-tick double-tap window, running bat, ordinary-enemy KO, momentum, walking/idle, Corporate Punk, music or backgrounds. Running timing stays six ticks per frame and root (64,92). The existing three-piece indexed renderer and palette are unchanged.

Run bank: 39104 bytes/24 resources. Total VDP1 allocation: 401952 bytes/159 slots. Remaining: 56536 bytes of the 458488-byte texture budget. Change from aae373f: zero. This is normal updated-asset validation, not another memory audit or optimization pass.

The playable artifact contains matching BIN/CUE in `build/`. `assets/leg-artifact-fix` contains all-eight-frame native/4× contact sheets, before/after sheets for the affected frames (old left, corrected right; frame2 above frame 4), full-cycle before/after GIFs, repair mattes and untouched pre-fix PNGs. `assets/running` contains the corrected individual PNGs and native/4× Buck/Chuck run GIFs. Old stride and combat reports/captures remain historical.

Native builds, asset validation, gameplay tests, CI and actual local emulator checks are required for this milestone. Emulator checks do not establish physical-Saturn or WebRetro compatibility. Visual approval remains with the user; no timing changes or new animation features are included.

## Completed local validation

Native BIN/CUE build, image/asset/music checks and all gameplay tests pass. Targeted artwork regressions verify all 486 edits remain inside the four repair mattes, original frames 1/3 remain identical, all actual leg-layer hashes/phases remain unchanged, and the known stale-kneecap pixels are clear. Native TGA reconstruction, mirroring, shared palette and ground-root checks pass.

The 900-frame local Yabause controller run showed all four poses for both fighters in both directions. All 605 recorded gameplay states, idle clocks, dash states and running-bat states remained byte-identical to aae373f. Running-bat KO occurred on the same frame 423 with the same 250-point score. It compared 147340 visible native sprite pixels with zero mismatches, and separately verified 54 visible ghost-kneecap pixels from the old build no longer appear in the game. Actual allocation remained 401952 bytes/159 slots, 56536 free, with stable textures during gameplay.

Screenshots/GIFs and JSON are in `docs/leg-artifact-captures`. Scene before/after comparisons use actual emulator captures: old on the left, corrected on the right. Physical Saturn and WebRetro playtests remain outstanding.
