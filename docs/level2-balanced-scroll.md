# Level 2 balanced horizontal scrolling

Parent: `a827c2ec82fddaade0bd8e1c627f75ec9905705c` (working wide-camera pass).
Branch: `fix/level2-balanced-scroll`. The exact delivery SHA is supplied in the delivery response. This report supersedes the dimensions in the historical wide-camera report; its preservation lock remains unchanged.

The logical world is now **320px**. The gameplay viewport remains **224x240**, at display **X48..271**, with the original HUD. The camera starts at **X48**, clamps to **X0..96**, and therefore has exactly **48px left and 48px right** available from its initial position.

Solo Buck now starts at world **X160**, which renders at display X160 with the centered camera. Coop retains Buck/Chuck **X130/X190**, symmetric about world X160. A shared home-position helper gives solo respawns the middle slot and coop respawns the original symmetric slots inside the current view; it never recenters the camera. Late joining remains camera-relative. Player center boundaries are now **X16..304**, preserving the 16px half-sprite margin. Stage-width-dependent drone lanes and projectile cleanup automatically contract to the smaller world; their velocities, cadence, collision rules, damage and pools remain unchanged.

The dead zone remains viewport-relative **X50..174**, or display **X98..222** (124px, 55.36% of the viewport). The existing fixed-point approach and **maximum 3px/tick** remain unchanged, including collective two-player targeting and 192px maximum center separation. No new camera algorithm or state is introduced. Starting solo in the center also makes the input distance to either threshold equal, avoiding the old 30px solo bias.

All artwork files, building tiles, pattern names, palettes, sprite textures, and the manifest are **byte-identical to the parent**. The existing 512x512 NBG1 hardware map stays allocated. A constant **96px map origin** selects its middle 320px: source **X96..415**. At the initial camera position, source **X144..367** is visible. At the left/right camera limits the view samples source X96..319 / X192..415. This centers the crop on the original map's X256 midpoint, retains its building layout and seams, and reveals its existing side streets symmetrically. No art is regenerated, scaled, mirrored or replaced.

NBG1 rendering converts camera 24.8 to SGL 16.16 with `(camera_x + (96-48)*256)*256`. Hardware X scroll is therefore 48px / 96px / 144px at the left / initial / right positions. Gameplay sprites still use `world_x-camera_x+48`. The artwork origin is an independent constant; it does not alter collisions or aiming. Y scroll remains the exact existing `-scroll*65536`, with the same one-pixel-per-tick pacing and 512px wrap. Loading configures NBG1 at zero before the first gameplay render, as before.

## Memory, before and after

| Resource | Working wide-camera parent | Balanced refinement |
|---|---:|---:|
| VDP1 texture bytes | 28,032 | 28,032 |
| VDP1 definitions | 18 | 18 |
| Maximum stage commands (including user clip) | 73 | 73 |
| VDP1 texture-area headroom | 430,456 | 430,456 |
| VDP2 cells / map | 2,752 / 8,192 | 2,752 / 8,192 |
| VDP2 background payload | 10,944 | 10,944 |
| VDP2 total reservation | 434,176 | 434,176 |
| VDP2 unreserved headroom | 90,112 | 90,112 |
| Stage CRAM payload | 32 | 32 |
| SCSP high-water / free | 307,260 / 217,028 | 307,260 / 217,028 |
| Gameplay state | 1,492 | 1,492 |

No new mutable camera/background state, texture, map, palette, audio allocation, heap allocation or per-frame upload. The 512px physical map is retained because the current VDP2 page format cannot shrink to 320px; cropping it avoids an unnecessary rendering/allocation change.

## Preservation and tests

The additive `docs/level2-balanced-lock.json` authorizes exactly seven existing source/test/validator updates, with exact before/after digests. It preserves the prior wide lock and adds the parent files that the older lock did not cover. Existing full preservation checks continue to run. No artwork, Level 1, Stage Clear/transition, X skip, workflow, music or Level 2 audio implementation changes. Complete Level 2 audio sources/banks/metadata remain byte-identical to the WebRetro-confirmed `78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e`. Runtime loader and audio-driving sections retain their original exact hashes.

Completed successfully: `make test` (**235 PASS reports**), `python3 tools/test-wingsuit.py` (**55 PASS reports**), native build, `make check`, audio/artwork byte comparisons and `git diff --check`.

Validation covers:

- Initial camera X48 and exact 48px travel available in each direction; solo X160 and symmetric coop X130/X190.
- Mirrored left/right inputs produce exactly mirrored fixed-point player/camera paths, equal threshold timing, bounded motion, and both extrema without overshoot; solo respawn retains the centered slot.
- Existing clamp/dead-zone/subpixel/no-overshoot tests, six two-player patterns, opposing maximum separation, stationary-partner protection, death/inactivity/join/respawn, and 10,000-tick camera visibility/speed stress.
- All 97 integer camera positions sample initialized cells inside source X96..415; preserved native cells/map/seams prevent exposed background edges or uninitialized names. Runtime mocks check the new NBG1 hardware X range and exact left/right values while Y scrolling stays unchanged.
- World/screen transforms for players, enemies, explosions, both projectile classes and Flame; camera-independent collisions, damage, aiming and trajectories; all 272 world spawn lanes.
- Full gameplay regression suite, 100,000-tick pooled stress, UBSan checks, Level 1, Stage Clear, transition and X skip regressions, original polyphonic audio/Flame readiness and overlap tests.
- Pinned native Saturn build and `make check`, including exact `/ALEVEL2` ISO payloads, Level 1 preservation and exported memory budgets; `git diff --check`.

These are host/native structural results. WebRetro confirmation of the refined composition and camera feel remains a manual step.

## Build and play

Local native build, with README prerequisites and pinned SDK installed:

```sh
bash tools/setup.sh
bash tools/build-level2-wingsuit.sh --native
make test
make check
```

Artifacts: `build/mullet-force.bin` and matching `build/mullet-force.cue` (MODE1/2048). Keep both together and open the CUE. In this session the missing host ISO tool was already available under ignored `.deps/host-tools/usr/bin`, added to PATH for build/check commands; no compiler, SDK pin, Docker base or workflow was changed.

Manual Actions settings: **Use workflow from `main`; Profile `stage-default`; Source ref the exact new delivery commit SHA**. No Actions run is dispatched automatically.

WebRetro: use X to enter Level 2, verify centered solo/coop entry, push left/right to compare the shorter equal camera travel, dodge inside the unchanged dead zone, and check side scenery/HUD clipping. Repeat while firing Shots, sustaining Flame and overlapping Explosions; test aimed bullets, opposing coop movement, respawn, pause/restart, and the normal Level 1 transition. Audible audio behavior and refined camera feel require manual confirmation.
