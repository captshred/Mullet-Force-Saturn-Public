# Level 2 top-down industrial city V2

Branch: `art/level2-topdown-city-v2`. Created **directly from approved commit `8504ddf8c9c04363862cb1e2cd3e068c0199d39e`**. The rejected `ad23b6b` visual experiment is not an ancestor or source of this branch's artwork. The delivery response supplies the exact new SHA. No GitHub Actions dispatch; workflows remain unchanged.

## Reference and composition

The attached reference was studied for overhead architecture, broad nested parapets, irregular footprints, machinery seen from above, shallow visible wall edges, road separation and damaged concrete. The new artwork is original and uses none of the reference's pixels, aircraft, sprites or exact layout. It retains Mullet Force's existing dark industrial palette, including restrained cyan facade windows, concrete grays, dark alleys and sparse amber road markings.

The playable composition is the approved middle **320x512** crop of a **512x512** native map. Six major building sections are spread across three city blocks, with two buildings per block:

1. **Dockworks:** a broad bevelled/notched warehouse, weathered concrete, rooftop access hatch, overhead tank, paired fan units, ducts and maintenance grating.
2. **Collapsed pump annex:** a smaller L-shaped footprint, jagged roof breach, exposed cross-members, rubble, round overhead tank and bent service route.
3. **Rail machine shop:** a larger L-shaped footprint, corrugated metal roof, skylights, ventilation fans and a grated access platform.
4. **Raised navigation works:** a stepped perimeter, shallow shaded walls, maintenance landing circle, numbered roof paint, fan and access room.
5. **Courtyard assembly works:** a U-shaped asphalt roof around an open courtyard, mechanical wings and a connected service bridge.
6. **Raised tank mill:** a staggered perimeter, two tanks viewed directly from above, overhead pipes and maintenance grating.

Silhouettes, footprint sizes, materials and wall depths distinguish buildings. Concrete wear stays low contrast; the roof collapse is an actual hole in the architectural silhouette/interior. Streets, crossing marks, drains, sidewalks, fenced passages and small service details provide separation. Partial neighboring compounds continue the city outside the gameplay crop. Every structure is drawn from above. There is no horizon, upright skyline, fixed decorative band or magenta strip.

## Aerial parallax and architectural integrity

NBG1 contains streets, paving, four complete lower buildings and neighboring city material. NBG2 contains **two complete taller buildings**, each including its entire roof, walls, equipment, hatch, machinery and attached shadow. Their ground plots contain paving, not duplicate roofs or matching facades. No individual building is split between planes.

NBG1 retains the exact approved horizontal camera scroll and vertical stage scroll. NBG2 uses **9/8 horizontal speed** about the same initial camera center. Its deviation from normal-speed ground is only **-6..+6px** over the complete camera range. Its full native pixel mask stays inside a reserved yard at both extremes, so the extra motion cannot cross neighboring structures or roads. This creates a subtle height cue while keeping the structure visibly intact.

Both planes use the **same original vertical scroll**, including the 512px wrap. This is intentional: continuously different vertical rates on the repeating city would eventually move buildings into unrelated streets and compounds. The aerial depth effect is horizontal; vertical registration is stable at all times. Both scroll submissions derive from the actual approved `camera_x` and `scroll` values, with no separate accumulated/eased state.

Using camera X in 24.8 and SGL scroll in 16.16:

- Ground X: `(camera_x + 48*256)*256` (unchanged).
- Raised X: `96*65536 + (camera_x - 48*256)*288`.
- Both Y: `-scroll*65536` (unchanged stage rate, one downward pixel/tick).

At camera X0/48/96, ground hardware X is 48/96/144 and raised X is 42/96/150. Both agree at center; raised apparent travel is **108px** versus the ground's **96px**. All arithmetic is integer/fixed point. No runtime scaling, floating point or per-frame graphics upload.

## VDP2 inspection and layout

The baseline transferred an A0 character arena of **106,496 bytes** and a B0 map arena of **65,536 bytes** from Level 1. Its stage payload used only 10,944 bytes. Including SDK-owned A1/B1 storage, reservation was **434,176 of 524,288 bytes**. NBG0 supplies text/HUD, NBG1 the city; NBG2 was available after the handoff disabled the old Level 1 skyline.

Both new planes use the established SGL tile format: **8bpp, 8x8 cells, PNB_1WORD/CN_12BIT, PL_SIZE_1x1, 512x512 map**, four plane pointers aliasing each map. Existing palette bank 1 is reused unchanged. All native indices fit its original 16 populated colors. Background pixels never use the existing pink/magenta palette entries 10/11.

| Plane | Cells | Pattern map | Priority |
|---|---|---|---:|
| NBG1 ground/lower city | A0+0, **36,864 bytes**, 576 tiles | B0+0, **8,192 bytes** | 1 |
| NBG2 complete tall buildings | A0+65,536, **12,416 bytes**, 194 tiles | B0+8,192, **8,192 bytes** | 2 |
| Gameplay sprites | Existing VDP1 | Existing commands | 4 |
| NBG0 HUD/text | SDK-owned | SDK-owned | 7 |

A0 starts at `0x25e00000`; B0 at `0x25e40000`. Raised pattern names include the absolute character offset **2,048 in 32-byte units**. Character regions and map regions do not overlap; all maps are properly page aligned. Both planes use the same full-height window X48..271/Y0..239. No plane is restricted to a horizontal decorative strip. SGL auto scheduling retains its existing checked E104 failure path and sprite state is restored afterward.

Ground characters have **no transparent pixels**. Raised transparency reveals this fully initialized backing plane. Ground top and bottom rows join the same road surface. Raised structures occupy neither wrap boundary, and both layers wrap in phase. Across all legal camera positions, visible ground source X stays inside 96..415 and raised source X inside 90..421, within their initialized 512px maps. No physical horizontal edge is reached.

## Modified background assets

- Updated `assets/wingsuit/WCELL.BIN`: native ground/lower building characters.
- Updated `assets/wingsuit/WMAP.BIN`: native ground map.
- New `assets/wingsuit/WROOF.BIN`: complete raised-building characters.
- New `assets/wingsuit/WRMAP.BIN`: raised-building map.
- Updated `assets/wingsuit/manifest.json`: exact payload hashes, resource totals and six-site authoring metadata.
- New generated `src/wingsuit_aerial_data.h`: byte counts, offsets and 9/8 rate constants.

`WPAL.BIN`, every hero/weapon/drone/explosion texture and all audio assets remain unchanged. No rejected skyline assets or files are present in this source tree. `tools/build-topdown-city-v2.py` generates only this new aerial composition; normal public builds use the committed native assets and do not regenerate art or require private inputs.

## Resource accounting

| Resource | Approved baseline | V2 |
|---|---:|---:|
| VDP1 texture bytes | 28,032 | 28,032 |
| VDP1 definitions | 18 | 18 |
| Maximum commands including user clipping | 73 | 73 |
| VDP1 texture-area headroom | 430,456 | 430,456 |
| VDP2 character payload | 2,752 | **49,280** |
| VDP2 map storage | 8,192 | **16,384** |
| VDP2 total background payload | 10,944 | **65,664** |
| Transferred stage arena reservation | 172,032 | 172,032 |
| Total VDP2 reservation | 434,176 | 434,176 |
| Unreserved VDP2 headroom | 90,112 | 90,112 |
| Unused bytes within stage arenas | 161,088 | **106,368** |
| CRAM payload | 32 | 32 |
| SCSP high-water / free | **307,260 / 217,028** | **307,260 / 217,028** |
| Gameplay state | 1,492 | 1,492 |

Additional VDP2 payload is **54,720 bytes**, with no new reservation. A0 retains 57,216 unused bytes in its transferred arena; B0 retains 49,152. Unreserved A0/B0 headroom remains 24,576/65,536; A1/B1 remain SDK-owned. No VDP1 or SCSP increase, new mutable gameplay/background state, per-frame file I/O or texture upload. One NBG2 scroll call is added per rendered frame. New graphics buffers remain smaller than the unchanged 158,312-byte audio tone file and are freed synchronously. Native `game.raw` is 230,288 bytes in this profile; hardware CPU/frame-time and heap/stack high-water were not measured.

`/ALEVEL2` contains **26 runtime files / 252,164 bytes**, with 28 directory records including dot entries, below the pinned 256-record GFS limit. Existing early-directory routing, length validation and error diagnostics cover both new files.

## Gameplay and audio preservation

`src/wingsuit.c` and `src/wingsuit.h` are byte-identical to `8504ddf`. Locked values remain **world320, viewport224/X48..271, initial camera48, limits0..96, +/-48 travel, existing dead zone, fixed point and max3px/tick**. Player movement, focus, controls, enemy spawns/aiming, collisions, damage and weapon timing are untouched. HUD and hero sprites are unchanged.

Level 1, Stage Clear, normal transition and X skip source remain unchanged. All Level 2 audio source/bank/metadata bytes remain identical to the WebRetro-confirmed `78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e`. The runtime audio-load/E108 block, audio progress callback and entire gameplay/audio frame-driving function retain exact approved parent section hashes. No music change.

Prior preservation locks remain unchanged. `docs/level2-topdown-v2-lock.json` authorizes exactly twelve changed existing files (backgrounds, renderer and relevant validation/staging/tests), with exact before/after hashes. It explicitly freezes the gameplay/camera/audio files and camera-delivery documents. Existing preservation suites stay active through exact additive scope helpers.

## Validation and visual review

Completed:

- `make test`: **240 PASS reports** across Level 1, transition/Stage Clear, X skip, approved camera, gameplay, audio and resource/loader regressions.
- Focused Level 2 suite: **60 PASS reports**, including UBSan gameplay/audio/runtime tests, original polyphonic Shot/Flame/Explosion checks, 100,000-tick gameplay stress and 10,000-tick coop camera stress.
- Native character/map/palette validation, no background pink indices, opaque lower backing, safe wrap boundaries and initialized coverage throughout the complete vertical cycle.
- Native raised-map connected-component analysis finds exactly **two complete objects**, with no disconnected equipment or wall fragments. Every object's full pixel bounding box stays inside its own yard throughout +/-6px motion; yards do not overlap unrelated lower architectural envelopes.
- **24,577 fixed-point camera positions** check exact 9/8 independent horizontal rate, bounded relative offset and legal source coverage. Actual runtime mocks test **193 half-pixel camera positions**, both plane pointers/formats/priorities/windows, unchanged vertical scroll and the 73-command sprite maximum.
- All **512 vertical phases** share registration between layers. The six main sites have distinct footprints and wall heights, spread across three blocks.
- Byte-identical art regeneration; exact native disc payloads; missing/corrupt raised-file rejection; idempotent staging; no stale root copies; parent-directory restoration; arena sentinels and unchanged CRAM/font/SCSP boundaries.
- Native Saturn build with the existing pinned Jo Engine/compiler; `make check` against matching BIN/CUE; `git diff --check`.

Visual review was **not limited to automated tests**: host composites were inspected at camera X0/48/96 and scroll0/128/256/384. Shapes, tanks/fans, material variation, streets and the full-height aerial perspective were reviewed, including a composite with unchanged hero/enemy/projectile sprites to assess contrast. There is no side-view city layer or fixed skyline band. The new art uses restrained colors and intact overhead architecture.

These are **host-rendered asset composites, not emulator screenshots**. No installed Saturn emulator runtime was available, so emulator appearance, actual VDP2 scheduling/timing, frame rate and final visual approval remain manual WebRetro checks. Passing tests does not establish those results.

Review artifacts (ignored, not committed):

- `build/topdown-v2-review/host-contact-sheet.png`: left/center/right across four vertical positions.
- `build/topdown-v2-review/host-view-<camera>-<scroll>.png`: individual 2x nearest-neighbor views.
- `build/topdown-v2-review/host-readability-with-original-sprites.png`: original sprite overlay, illustrative host positions.
- `build/topdown-v2-review/host-pan.gif`: panning asset preview.
- `build/topdown-v2-review/ground-map.png` and `complete-roof-map.png`: full native layer compositions.

## Build and manual acceptance

With README native prerequisites installed:

```sh
bash tools/setup.sh
bash tools/build-level2-wingsuit.sh --native
make test
make check
```

Art regeneration for deliberate edits: `python3 tools/build-topdown-city-v2.py`. Preview exports stay in ignored `build/`; no reference image or authoring PNG archive is committed. In this environment the existing host ISO utilities are under ignored `.deps/host-tools/usr/bin`, added to PATH for build/check commands.

Playable artifacts: matching `build/mullet-force.bin` / `build/mullet-force.cue`, MODE1/2048. Keep them together and open the CUE.

Manual Actions settings: **Use workflow from `main`; Profile `stage-default`; Source ref = the exact new delivery SHA**. No workflow is triggered automatically.

WebRetro acceptance: enter Level 2 with X, inspect all three blocks across a complete vertical cycle, pan fully left/center/right and reverse slowly around the raised sites. Confirm the complete taller buildings exhibit subtle faster motion while staying grounded in their plots, with no sheared roof/equipment, seam or HUD bleed. Check readability during aimed shots, sustained Flame, explosions and coop separation; then pause/restart and test the normal Level 1 Stage Clear handoff. The approved gameplay/camera remains locked; this aerial visual pass awaits manual approval.
