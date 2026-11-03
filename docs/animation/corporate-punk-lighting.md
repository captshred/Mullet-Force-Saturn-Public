# Corporate Punk: final soft rim-lighting review

Branch `corporate-punk-lighting-test`, parent `bf4e41df9c68511944176fa54f376e772a289b8f`, the latest validated playable scale-refinement head verified against GitHub. The approved92px anatomy, poses, texture layout and timing are locked. This milestone edits indexed colors only; no image model, pose generation, resampling or new animation artwork is used.

## Exact color operation and isolation

Twelve audited magenta/pink environmental suit shades are changed to rounded half of each existing5-bit channel: `new=(old+1)//2`. This retains colored rim light, with approximately50% channel intensity (nearest half-step in RGB555), rather than deleting it. It is not a calibrated perceptual/gamma adjustment. Cyan/blue edge colors, green mohawk, skin/face, bright red tie and every other untargeted native pixel remain byte-identical in visible RGBA values.

`assets/corporate-punk-lighting/rim-lighting-roles.json` documents each source index, destination index, original/new BGR555 channels, use count and protection reason for future offline palette variants. Raw source indices74,100,120,121,146,162,163,175,176,186,187,192 represent the audited suit-rim ramp. The full native head region y<22 and conservative shirt/tie rectangle49<=x<61,22<=y<52 are protected. All six current idle/walk frames are audited; shared shades162 and176 also occur in protected pixels, so those original palette words stay intact. Only their suit occurrences are remapped into previously unused slots235/236 with softer shades. The other ten entries can change safely in place. This is a palette edit plus two necessary index substitutions, not a pose edit.

All legacy EN*.TGA use raw0–14, which remain exactly unchanged. The original84px and full-strength92px source banks remain intact and are alternative build configurations. The new palette extends the same enemy bank4; bank5's warm/flash colors are derived from it by the unchanged loader. No unrelated palette bank is edited, and fire/music/background/player assets remain intact. No attack/damage frame currently uses the new high-detail art; those still use the original legacy fallbacks, unchanged.

Two spare palette entries are consumed within an already allocated512-byte bank, leaving17 eligible raw slots237–253. Full bank allocation does not grow. Some softened hues converge in RGB555; their original separate indices remain available for future shade roles. The new master uses181 visible hardware colors because protected and environmental uses of shared shades are separated. No lighting engine, dynamic palette updates, runtime variants or level-specific assets are implemented.

## Geometry, animation and memory

Every canvas remains96×96, root(48,92), opaque master64×92. Pixel coordinates, alpha masks, resource IDs, padded rectangles, four-piece layout and ten-resource deduplication are identical to the validated parent. All changed pixels are within the audited rim mask. Visible pixel changes per pose are39,39,38 idle and40,39,17 walk. All other visible colors are exact originals. The3-frame idle holds remain24/12/18 simulation ticks; walk remains7/7/7 at60Hz. No source C/header/gameplay/AI/renderer/player timing change is required.

VDP1 animation bank stays **11744 bytes /10 texture slots** shared across all instances. Actual approved gameplay configuration remains **362848 allocated /95640 free /135 slots** within458488 texture bytes. Optional full player-comparison expansion remains438848 allocated /19640 free /186 slots. VDP1 allocation delta **0 bytes/0 slots**; CRAM allocation delta **0 bytes/0 banks** (existing eight512-byte banks,4096 total). Two existing enemies still submit four pieces each; no new allocations, uploads, sprite submissions or CD reads occur during gameplay. Color changes cannot establish hardware performance; physical Saturn frame pacing remains untested.

## Review and build

`comparison-native.png` shows full-strength, softer rim, actual approved Buck88px and softer Punk92px at matching sole row91, without independently scaling characters. `comparison-4x.png` is nearest-neighbor enlargement. `contact-{native,4x}.png`, `master-92-rgba.png`, `master-92-8x.png` and `idle/walk-4x.gif` provide the updated previews. Source poses are retained in `assets/corporate-punk-refined/`. The comparison intentionally retains magenta on protected face/tie pixels.

Build with `MF_CORPORATE_LIGHTING=1 MF_CORPORATE_REFINED=1 MF_CORPORATE_PUNK=1 MF_WALK_KNEE_LIFT=1 MF_ORIGINAL_THREE_WALK=1 MF_ORIGINAL_WALK_SLOW=1 MF_PLAYABLE_ANIMATION=1 MF_ANIMATION_PREVIEW=1 MF_SPRITE_GALLERY=1 MF_VDP2_STREET=1 MF_PARALLAX_DEMO=1 make native`. `MF_CORPORATE_LIGHTING=0` restores the full-strength approved92px bank. Flags default0 and selection is recorded in BUILD-INFO/source hashes. Normal builds stage committed assets; offline regeneration is `python3 tools/build-corporate-punk-lighting.py`.

Validation: `python3 tools/corporate_lighting_validation.py` independently proves half-channel colors, preserved protected/untargeted pixels and legacy palette, exact masks/geometry/holds, native/mirrored TGA reconstruction, identical resource sizes/IDs/count and GIF pixels. `make check` validates the selected disc payload; `make test` retains existing gameplay checks. Local emulator and CI results are reported with the build. No WebRetro or physical hardware compatibility claim is made without a corresponding test.

## Completed local verification

Pinned native build, `make check`, `make test` and the dedicated color/geometry validator pass. No committed C/header file changes, no edits to the approved full-strength bank, and no player, legacy enemy, music, background or timing asset changes are present.

The controller-driven local Yabause HLE/software test ran2800 frames per build against the approved scale-refinement control. All2470 compared gameplay simulation frames were byte-identical. It compared552099 native enemy pixels with zero mismatches, observing idle0 and all three walking poses in both facings and all eight original enemy states. Multiple simultaneous Corporate Punks are shown in actual captures. Idle1/2 remain covered by exact native/mirrored/GIF asset checks and existing timing tests; the ordinary controller sequence does not expose them unobstructed long enough for full runtime pixel comparison.

A whole-screen comparison checked **48372547 pixels outside the allowed rim masks with zero differences**; all11192 observed color changes were confined to the audited rim masks. No unrelated gameplay/HUD/player/background pixel differences were observed. Read-only runtime inspection confirmed **362848 VDP1 bytes/135 slots**, stable textures throughout gameplay, all222 allocated new normal/warm palette entries correct in existing banks4/5, and unchanged legacy palette entries. The source palette and those derived flashes change only for the intended rim roles.

The JSON report records the local core SHA256 and method. Before/after gameplay comparisons use matching controller frames, with no independent scaling or synthetic sprite placement. No physical Saturn or WebRetro testing was performed here. Visual final approval and hardware/browser playtesting remain outstanding; existing simpler legacy combat fallbacks are unchanged.
