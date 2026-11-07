# Level 2 neon city candidate

Branch `art/level2-neon-city`, parent `a914faedaced626297e424a65a29d675b449488b` (latest audio engine delivery). No merge into main.

The sixteen Level 2 palette colors are copied directly from the active Level 1 `assets/city-cleanup/CIPAL.BIN` hardware palette. Indigo and violet replace gray roof materials; cyan outlines and machinery sit above dark navy streets. Selected existing horizontal trim becomes magenta and selected existing facade windows become amber. No geometry, equipment, silhouette, road, damage, scrolling, camera or gameplay changes. Large roof surfaces remain dark. Removing accent indices 9->6 and 15->8 exactly reconstructs every original cell byte; both maps remain identical.

The candidate lives separately in `assets/level2-neon-city/`. Original artwork, source recipes, locks and Level 1 palette are unchanged. `recipe.json` specifies the exact reference entries and detailing rule; `python3 tools/build-level2-neon-city.py --export` reproduces the native assets.

## Audio-preserving build

The public source does not contain the privately compiled latest audio-engine corrections. Compiling it would lose those fixes. The build therefore verifies the original audio-engine delivery ZIP and every contained checksum, then replaces exactly three equal-length ISO9660 payload extents: `/ALEVEL2/WCELL.BIN`, `WROOF.BIN`, `WPAL.BIN`. The entire resulting image is compared to the delivered baseline outside those extents. This preserves the executable, audio, 24x24 explosion artwork, all other assets, directory records and padding byte for byte. No compiler, loader, audio driver, sound bank, sample, gameplay, HUD or build-profile code is modified.

Build: `python3 tools/build-level2-neon-city.py --out build/download`. Open the matching `mullet-force.cue` with its BIN in the same directory. The original audio report and playback measurements in the package describe the unchanged baseline; they are not new candidate playback measurements. `NEON-VALIDATION.json` identifies this image and its preservation check.

## Resources

| Resource | Before | Candidate | Delta |
|---|---:|---:|---:|
| Ground cells | 578 / 36,992 bytes | 578 / 36,992 bytes | 0 |
| Raised cells | 194 / 12,416 bytes | 194 / 12,416 bytes | 0 |
| Two maps | 16,384 bytes | 16,384 bytes | 0 |
| Background payload (excluding CRAM) | 65,792 bytes | 65,792 bytes | 0 |
| Palette entries / CRAM payload | 16 / 32 bytes | 16 / 32 bytes | 0 |
| Palette banks added | 0 | 0 | 0 |
| VDP2 reservation / unreserved | 434,176 / 90,112 bytes | 434,176 / 90,112 bytes | 0 |
| VDP1 textures / definitions | 33,792 bytes / 28 | 33,792 bytes / 28 | 0 |
| SCSP high water / free | 447,588 / 76,700 bytes | 447,588 / 76,700 bytes | 0 |

Level 2 owns CRAM bank1 from entry256 (32-byte payload); font bank0 and separate RGB555 actor/effect textures do not use this palette. Loader allocation and upload remain unchanged. Candidate colors are exact RGB555 words, not approximations from the screenshots.

Host previews decode the actual native maps/cells/palette at left/center/right camera positions and across the vertical wrap. They are asset composites, not emulator captures. Physical Saturn and final user visual/audible approval remain pending.

## Verification performed

The candidate builds reproducibly. Candidate tests reject corrupted executable, sprite, map, palette and image-length mutations. Every non-background byte is identical to the audio-engine delivery.

A native libretro Yabause 0.9.15 HLE smoke comparison ran 1,650 frames per image with identical controller-only Start/X, movement and held-A inputs, without game-memory writes. Captured gallery/Level1 frames are pixel-identical. All seven captured HUD sidebars are pixel-identical, while Level2 background pixels change. Stereo PCM is byte-identical for all 4,851,000 captured bytes. Detailed hashes are in `level2-neon-emulator-results.json`. This is a short playback comparison, not a new full-score or sustained stress certification. Physical Saturn remains untested.

`make test -o test-wingsuit` passes (179 PASS reports). All ten existing focused wingsuit C programs pass, including camera/coop, patterns/turrets, aiming, gameplay stress, flame, audio, weapons and both loader/render configurations. ISO/staging, canonical hero asset, driver-ready and native-tone checks pass.

Full `make test` and `make check` were attempted before changing the workflow: both fail on inherited workflow assumptions in the audio delivery parent. `validate-level2-ready.py` freezes the older workflow hash; `validate-full-gameplay-sfx2.py` prohibits the delivery parent's push trigger. Related historical validators also freeze that workflow. Those existing locks were not weakened or rewritten. The candidate Actions job performs the dedicated image/asset preservation checks and mutation tests; it does not claim the legacy aggregate targets pass. No source compilation is used for this candidate, because the public source lacks the delivered audio-engine fixes.

## GitHub Actions

The existing Manual Saturn playtest build workflow has one candidate packaging job on pushes to `art/level2-neon-city`, or manual profile `level2-neon-city` with the exact candidate source ref. It reproduces the background-only image, runs preservation mutations and verifies all output checksums. One matching playable artifact is retained for one day. Main and the approved baseline are unchanged.
