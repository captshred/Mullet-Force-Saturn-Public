# Alternating run stride correction

Parent verified from GitHub history and successful run 40760740737: `05f2a58f42c5246bbf46e41ebacdba78d0e3b8f3` on `dash-bat-attack-test`. New branch: `dash-alternating-stride-fix`. No merges or previous branch changes.

## What was wrong

The previous four frames were different pixel images, not exact duplicates. Nevertheless the same forward boot/leg overlap and a forward recovery knee made the cycle read as repeated same-leg contacts. The phase names and distinct hashes did not prove a complete gait. The old eight PNG masters,24 TGAs and manifest are retained in `assets/stride-fix/before` for direct comparison; the old high-resolution guide remains unchanged.

## Actual anatomical identity

The correction uses four individual hip-to-boot layers per fighter rather than moving boots independently. Each layer contains one thigh, knee, shin, ankle and boot. Near/right and far/left are persistent anatomical identities when facing right. Mirroring reflects the finished character for left-facing play; it never fabricates the other stride.

| Frame | Near/right leg | Far/left leg |
|---|---|---|
|1|Forward contact|Folded recovery behind hip|
|2|Trailing push-off|Knee drive forward|
|3|Folded recovery behind hip|Forward contact|
|4|Knee drive forward|Trailing push-off|

Each leg completes contact → push-off → recovery → knee drive → contact. The far leg is exactly two animation phases ahead, always behind the near leg in overlapping pixels and shaded using the existing palette. Frame 3's forward contact is therefore genuinely the other leg, including the thigh/shin chain and its occlusion, rather than a swapped boot. `buck-identity-4x.png` and `chuck-identity-4x.png` tint the actual contributing layers red/near and cyan/far for development review. Those colors are never exported to game TGAs.

The recovery knee bends behind the hip and its boot stays clear of the ground. Contact soles remain on row91; trailing push-off toes clear by 2px, folded recovery by 21px, and driven knees' feet by 10px. No whole-body translations, scaling or root changes are applied. All original pixels in rows 0–47, including the heads, faces, sunglasses, hair, jackets/vests, arms and pelvis, remain byte-identical per frame. Existing arm poses are retained to prioritize the approved upper artwork; no new upper-body arm animation is introduced.

## Timing, gameplay and resources

No gameplay, input, combat, animation-clock or renderer-selection code changes. Native canvas 128×96, root(64,92), four frames, six simulation ticks per frame and existing three-piece construction remain intact. Dash stays 663/256 pixels per tick (1.7× normal walk),12-tick double-tap window. Running bat/ordinary-only KO, momentum 8 ticks, planted-bat priority, normal walk/idle, jump/hurt, enemy AI, score, camera and controls retain their existing implementation. Hash locks cover gameplay/configuration sources; existing asset hashes cover normal heroes and Corporate Punk.

Eight upper TGAs are reused byte-for-byte. Crops for the middle/lower bands are independently optimized at even scanline boundaries: only transparent padding and texture rectangles change, never native output pixels. Identical payloads are interned; no duplicate P1/P2 banks, added poses/palettes, CD streaming, heap work or extra draw submissions.

| VDP1 allocation | Bytes |
|---|---:|
|Inherited approved gameplay excluding run bank|362848|
|Corrected run bank /24 resources|39104|
|Total /159 texture slots|401952|
|Free of458488-byte budget|56536|
|Change from previous run build|−2560|

Palette/CRAM allocation remains eight banks/4096 bytes. Work RAM and gameplay state allocation have no change. The resident walk/run review remains accessible through the existing gallery; the old oversized six-frame expansion remains available only in prior build configurations.

## Review files and limitations

`assets/running` contains corrected native PNGs,1×/4× contact sheets,1×/4× GIFs and unchanged-walk/new-run comparisons. `assets/stride-fix` contains synchronized before/after GIFs (old on the left, corrected on the right), anatomical overlays, intermediate one-leg layers, the final leg guide and untouched previous frames. Reproduce with `python3 tools/fix-running-stride.py`; the prior `build-running.py` describes the original milestone and should not be used to overwrite this correction.

The anatomical phase order and pixel/anchor preservation can be validated mechanically. Naturalness, amount of stepping and the loop still require visual approval at the unchanged timing. Six-tick held contact poses move with the actor between samples; absolute zero world-space sole slip cannot be promised with four fixed poses and a fixed root. No timing/speed/root compensation was added to hide that limitation. Existing upper-body counter-swing is retained and is less pronounced than a newly drawn full-arm cycle. Any requested further arm/timing polish should be reviewed separately.

Native builds, relevant tests, CI and controller-driven local Yabause results accompany the playable artifact. No physical Saturn or WebRetro result is implied by local emulator testing.

## Completed local results

Native build, image/asset/music checks, all existing gameplay tests and focused dash/bat/animation/bank tests pass. The asset test independently recomposes the near/far layers, verifies 48 locked upper rows in all eight frames, opposite contact/recovery geometry, existing-source hashes, exact indexed TGA assembly and mirrored rendering. The padded crop reduction is 2560 bytes with eight identical upper textures reused.

The controller-only local Yabause run covered 900 frames. All 605 recorded gameplay states and idle clocks were byte-identical to the validated `05f2a58` control at the same emulator frames. Dash and running-bat suffix traces were also byte-identical, including timers, direction, pending-input classification and enemy classes. This confirms the tested movement, jump, cancellation, camera, enemy behavior, damage, score and bat timing did not change. Both fighters showed all four corrected run poses facing both directions, with 148,432 visible native pixels compared and zero differences. Full-health ordinary-enemy KO occurred at the same frame 423 and scored 250 once; active dash and carry samples stayed 663/256.

Actual allocator state was 401,952 bytes and 159 slots, leaving 56,536 bytes. Texture hashes remained stable throughout gameplay: no mid-game texture uploads. Real screenshots/GIFs and JSON are in `docs/stride-fix-captures`. Previous captures in `docs/running-bat-captures` intentionally remain historical. No physical Saturn or WebRetro playtest was performed.
