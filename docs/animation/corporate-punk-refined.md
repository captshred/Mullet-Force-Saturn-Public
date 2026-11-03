# Corporate Punk 2.0: scale and native-detail review

Branch `corporate-punk-scale-refinement`, parent `f45cad4b4d4fdf56e9030997c7536df714866ef6` (latest integration head verified against GitHub and its successful CI run). Older artwork and integration branches remain untouched.

## Choice and native comparison

The user-supplied new gameplay concept guides the design only; its labels and diagram are not technical measurements. Actual approved hero PNGs are used unchanged in the lineup, not concept-image hero crops. Buck is79×88 opaque pixels, Chuck82×88, old Corporate Punk47×84. New candidates are65×88 and64×92, each within a96×96 canvas rooted at(48,92), soles at row91. The92px candidate is selected: tall, lean proportions, more readable face/mohawk and long slim legs, shoulders/arms still narrower than the muscular heroes. It is four native pixels taller than the heroes. The88px candidate is included for visual comparison. No runtime scale change is used.

`assets/corporate-punk-refined/lineup-native.png` contains actual Buck, Chuck, old84, new88, selected92 on a single sole line; `lineup-4x.png` is nearest-neighbor enlargement. `master-92-rgba.png` and indexed `idle-0.png` are the same native master. `contact-{native,4x}.png`, `idle-4x.gif`, `walk-4x.gif` show all six frames. The older84px source, animation bank, and previews are retained in their original asset directories and packaged as references.

## Craft and limits

This is a new tool-assisted reconstruction from the supplied concept, not a stretch or nearest-neighbor enlargement of84px art. Retained source guides include separate88/92 proportion studies, finer body-cluster reconstruction, a24×28 native head-grid cleanup, and pose edits referencing the previous walk. Coverage/cluster-median import preserves hard contours; a separately reconstructed native head adds the eye, brow, mouth and sharp crest. Nearest-neighbor is used only for review enlargement, not for importing the finished sprite. Source studies and intermediate native references are labeled as such; committed indexed frame PNGs are authoritative. No claim of manual hand-painting or pixel-exact extraction from the inline concept is made.

The previous master used42 opaque RGB555 shades; the selected master uses180, versus193/226 in the actual heroes. Quantization occurs after snapping samples to Saturn5-bit channels so the palette budget is spent on distinct hardware shades. No dithering or partial alpha is exported. Contours are predominantly one native pixel; small2px shade clusters remain in dark cloth and the crest. Face, lapel boundaries, fists and pointed shoes are more readable, but tiny facial/cloth details still simplify at92px. The dark suit naturally has flatter regions than the heroes' textured denim and bright jacket; equal color counts or an identical pixel artist cannot be guaranteed. `comparison_metrics` reports exact bounds, RGB555 counts and a horizontal same-color adjacency statistic. That statistic is descriptive, not a visual-quality score or proof of matched pixel density. Visual approval in gameplay remains essential.

## Animation and gameplay continuity

Three idles retain24/12/18-tick holds; three walk poses retain7/7/7 ticks at60Hz. The21-tick gait remains front-foot lift, weight transfer, opposite step. Frame4 (walk middle) shares the full master. Head and torso are fixed across walking poses above row52. Idle edits stay in two small shoulder/fist regions; head and all pixels below row52 remain fixed. Pose guides are registered at the pelvis, not centered on a moving foot. The existing game walk counter drives each enemy independently. No movement, AI, hitbox, combat, spawning, audio, player animation/timing or background changes are made.

The shared renderer now accepts a compile-time piece count. Old configuration retains three pieces; refined uses four. Root, hardware mirroring, depth and unit scale remain unchanged. Legacy attack/hurt/recovery/death frames retain the previous integration's one-pixel sole registration correction and original native dimensions. Their standing poses are approximately90px tall, so the height change is now about2px rather than6px; their simpler design and pose-dependent silhouette still pop at fallback transitions. Redrawing those moves is outside this correction, and they are not rescaled to disguise the difference.

## Palette and VDP1

Existing enemy bank4 and derived warm-flash bank5 are reused. Every legacy raw0–14 palette entry is byte-identical.220 new unused raw slots are assigned (15–234);19 eligible slots remain. The full file palette is256 BGR24 entries/768 bytes, hardware bank512 bytes. A raw index i maps to CRAM word i+1 through the pinned Jo loader. Burn colors are derived after loading the refined palette, not from the older42-color version. Total CRAM bank allocation remains4096 bytes; no new bank.

Layout search compares global deduplicated bank cost, not just one pose. Tested three-band layouts cost21088 and14304 bytes; four-band alternatives cost13344,11744 and13536; the tested five-band layout costs13248. Selected cuts are rows0/22/52/76/92. Ten unique indexed textures total **11744 bytes** with32-byte allocator alignment; four commands draw each enemy. This is **2272 fewer texture bytes** than the previous14016-byte bank, with one extra resident texture slot. Identical enemy instances reuse all ten handles; there are no per-instance uploads, per-frame allocations or gameplay CD reads. Existing two enemies use eight submissions rather than the previous six. This is a command-count estimate, not a Saturn CPU/FPS measurement.

| Configuration | Texture bytes allocated | Free /458488 | Texture slots |
|---|---:|---:|---:|
| Locked players + old84px integrated enemy |365120|93368|134|
| Locked players + refined92px enemy |362848|95640|135|
| Refined enemy + expanded old comparison bank |438848|19640|186|

Nothing is removed from the original gameplay bank or the optional player comparison bank. Old and new Corporate Punk idle/walk banks are alternative builds, not simultaneously resident; all original combat fallbacks remain loaded.

## Build and validation

Set `MF_CORPORATE_REFINED=1 MF_CORPORATE_PUNK=1 MF_WALK_KNEE_LIFT=1 MF_ORIGINAL_THREE_WALK=1 MF_ORIGINAL_WALK_SLOW=1 MF_PLAYABLE_ANIMATION=1 MF_ANIMATION_PREVIEW=1 MF_SPRITE_GALLERY=1 MF_VDP2_STREET=1 MF_PARALLAX_DEMO=1` for the review build. Set only refined=0 to recover the old84px integration. Other inherited configurations remain unchanged. Both flags default0 so their selection is explicit in CI/build metadata.

Offline regeneration: `python3 tools/build-corporate-punk-refined.py` (Pillow/NumPy). Ordinary game builds stage committed assets and do not regenerate art. Independent validation: `python3 tools/corporate_refined_validation.py`. It checks palette preservation/uniqueness, exact TGA native and mirrored assembly, transparency, all frame bounds, frozen head/torso/idle feet, three distinct walking poses, GIF pixels, hero lineup pixels, layout/memory totals and source hashes. Existing tests exercise both bank configurations. Native build, disc/asset validation and gameplay regression results are reported with the delivered build. Emulator/hardware claims require actual testing; physical Saturn and WebRetro visual review remain outstanding.

## Completed local tests

Pinned native SH-2 build, `make check`, `make test`, old84px export validation and refined export validation passed. Diff checks confirm `src/game.c`, `src/game.h`, `src/main.c`, player assets/timing, legacy assets, old enemy banks and backgrounds are unchanged. Both old and refined shared-loader/state/facing/failure/fallback tests pass.

A controller-driven local Yabause test ran2800 frames for this build and the validated integration control, with2470 identical gameplay simulation frames. It compared552099 unoccluded enemy pixels with zero differences, covering idle0 and all three walk poses in both facings; it observed all eight existing enemy states. The ordinary controller sequence did not expose unobstructed idle1/2 long enough for pixel comparison: their native/mirrored/GIF pixels and54-tick clock holds are validated offline/unit-tested, and visual idle approval remains outstanding. Multiple simultaneous enemies, target switching, damage/death/respawn and two-player actions occur in the test, without game-memory writes. Actual captures are included, not concept composites.

A separate native-art check matched897754 player pixels against the locked hero frames, including both facings and all three approved walking poses. Read-only state inspection confirms362848 allocated bytes/135 slots and no texture writes during gameplay. CRAM inspection verifies all220 new normal/warm shades in the same bank4/5 allocation and legacy entries unchanged. A1600-frame gallery test confirms438848 allocated bytes/186 slots after expansion,28800 preview pixels unchanged, gameplay return and stable textures afterward. Core SHA256/method and exact counts are in `corporate-punk-refined-captures` JSON reports. These are local software-renderer, interpreter, HLE-BIOS Yabause tests, not WebRetro or physical Saturn tests. Physical fill-rate/frame pacing and the final artistic match still require playtesting.
