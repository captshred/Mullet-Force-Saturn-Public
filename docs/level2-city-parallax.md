# Level 2 industrial city variation and parallax

Parent: `8504ddf8c9c04363862cb1e2cd3e068c0199d39e`, the approved balanced camera. Branch: `art/level2-city-parallax-variation`. The exact delivery SHA is supplied in the response. No Actions dispatch or workflow change.

## Composition

The 512x512 physical city map retains the approved middle 320px crop (source X96..415), original industrial palette, top-down rooftop vocabulary, street grid and restrained colors. Eight individually authored compounds inside that crop replace the uniform repeated blocks:

1. Rivet mill: two vent banks, long pipe run and faded MILL 07 sign.
2. Sawtooth foundry: taller footprint, repeated sloping roof bays and recessed loading frontage.
3. Boiler house: a narrower footprint with paired cylindrical stacks and service pipework.
4. Broken rail depot: fractured roof corner, debris, cracked wall and boarded openings.
5. Water-tower works: elevated round tank, legs, ladder and rooftop vent.
6. Power substation: transformer banks, bus piping and a faded GRID panel.
7. Narrow brick loft: stacked recessed windows, lean service strip and a smaller footprint.
8. Freight loading hall: broad low frontage, multiple shutter doors and faded signage.

Footprints vary from 62 to 134px wide and 61 to 106px deep. Alley gaps, fenced service yards, sparse grime and varied setbacks separate them. Outer map districts continue the same industrial vocabulary. Landmarks include the tank, boiler stacks, broken depot and foundry roof. Bright projectile/flame colors remain distinct from the muted scenery.

A separate distant panorama adds seven skyline silhouettes: stepped factory, sawtooth shed, water tower, stepped mill, twin stacks, damaged roof and gantry hall. It occupies the upper 104 display pixels, with an ordered-dither haze edge fading to transparency; it does not attach to lower facades that could tear apart during parallax. The lower city continues behind the fade. This upper panorama stays vertically distant while the lower city retains its existing one-pixel/tick downward motion. It is a deliberate two-depth composition, not a split connected building.

Review exports are generated into ignored `build/city-review/`: full city/sky maps and nine composites at camera X0/48/96 and vertical scroll 0/96/256. No PNGs, source audio or private masters are committed. `tools/build-level2-city.py` creates the native cells/maps from deterministic drawing code using the existing palette; regeneration was verified byte-identical for all runtime assets, manifest and generated header.

## Approved behavior preserved

`src/wingsuit.c` and `src/wingsuit.h` are byte-identical to the approved parent. World width **320**, viewport **224** at **X48..271**, initial camera **X48**, clamp **X0..96**, exactly **48px** travel each direction, dead zone **50..174** relative to the viewport and maximum **3px/tick** remain unchanged. Player controls, coop containment, spawning, aim snapshots, velocities, damage, Flame geometry, shot cadence, HUD and sprite art are unchanged.

Level 1, Stage Clear, normal stage handoff, X skip and `/ALEVEL2` routing retain their existing implementations. Only Level 2 background loading, setup and rendering change. All Level 2 audio sources/banks/metadata remain byte-identical to `78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e`, including direct-MIDI Shot/Explosion, four Explosion controls, split Flame and 38-VBlank handoff. The runtime audio-loading call/E108 failure block, progress callback and entire gameplay/audio frame driver retain exact parent section hashes. No music work.

## VDP2 implementation

Both layers use the existing known SGL indexed-tile path: **8bpp, 8x8 cells, 1-word/CN_12BIT pattern names, 512x512 map, PL_SIZE_1x1**, four plane pointers aliasing each map. Both use existing palette bank 1 with only its original 16 colors populated. No bitmap conversion, line-scroll table, per-frame upload or VDP1 scenery.

| Layer | Cells | Map | Priority | Motion |
|---|---|---|---:|---|
| NBG1 lower city | A0+0, 55,232 bytes / 863 cells | B0+0, 8,192 bytes | 1 | Full approved camera rate; unchanged vertical auto-scroll |
| NBG2 distant city | A0+65,536, 15,424 bytes / 241 cells | B0+8,192, 8,192 bytes | 2 | Half camera delta, fixed Y=0 |
| Gameplay sprites | Existing VDP1 textures | Existing commands | 4 | Existing world-to-screen rendering |
| NBG0 HUD/text | SDK-owned, unchanged | SDK-owned, unchanged | 7 | Fixed |

A0 base is `0x25e00000`; B0 base is `0x25e40000`. The sky pattern names include the absolute character offset **2,048 in 32-byte units** for A0+65,536. Both maps are 8KiB aligned, and neither cells nor maps overlap. SGL `slScrAutoDisp` schedules NBG0/NBG1/NBG2/sprites and retains its existing E104 failure path. Sprite state is restored afterward as before. NBG2 uses the same window 0 as the lower city, preventing HUD bleed.

The lower horizontal 16.16 scroll remains exactly `(camera_x+(96-48)*256)*256`. The upper scroll is **`96*65536 + (camera_x-48*256)*128`**, preserving every camera subpixel. At camera 0/48/96, lower hardware X is 48/96/144 and upper X is 72/96/120: the skyline travels **48px** while the city travels **96px**. Both are centered on the same source X256 at the initial camera. No independent eased state can drift or jitter. Skyline Y stays zero; NBG1 Y remains the exact `-scroll*65536` with the existing 512px wrap.

The visible lower sample range stays inside source X96..415; upper samples stay inside X120..391. The lower map has no transparent cells and its top/bottom rows join the same road surface. The upper map has a transparent terminal row and transparent rows from Y103 onward; its fade exposes the fully populated lower map, not VRAM gaps. No horizontal map edge is reached during legal camera travel.

## Resources

| Resource | Approved parent | This pass |
|---|---:|---:|
| VDP1 texture bytes | 28,032 | 28,032 |
| VDP1 definitions | 18 | 18 |
| Maximum VDP1 commands, including user clip | 73 | 73 |
| VDP2 cell bytes | 2,752 | 70,656 |
| VDP2 map bytes | 8,192 | 16,384 |
| VDP2 background payload | 10,944 | **87,040** |
| VDP2 transferred arena reservation | 172,032 | 172,032 |
| VDP2 total reservation | 434,176 | 434,176 |
| VDP2 unreserved headroom | 90,112 | 90,112 |
| Unused bytes inside transferred arenas | 161,088 | **84,992** |
| CRAM payload | 32 | 32 |
| SCSP high-water / free | 307,260 / 217,028 | 307,260 / 217,028 |
| Gameplay state | 1,492 | 1,492 |

Payload increases by **76,096 bytes**, with **zero new VRAM reservation**. A0 keeps 35,840 unused bytes inside its 106,496-byte arena, including the intentional gap before sky cells; B0 keeps 49,152 unused bytes inside its 65,536-byte arena. Unreserved bank headroom remains A0 24,576 and B0 65,536; A1/B1 remain SDK-owned. The two maps are the minimum existing 512x512 page format. Eight-bit storage preserves the already proven Level 1/2 tile paths and avoids changing rendering formats for a palette optimization.

No new mutable camera/background/gameplay state, texture definitions, SCSP allocation or per-frame file I/O. The only per-frame addition is one fixed-point NBG2 scroll submission. The largest temporary resource buffer remains the existing 158,312-byte audio tone file; new graphics reads are smaller and freed synchronously. The native `game.raw` is 230,288 bytes in this build. Exact hardware frame time and heap/stack high-water are not measured by host tests.

`/ALEVEL2` now contains **26 runtime files / 273,540 bytes**, including new `WSKY.BIN` and `WSMAP.BIN`. Existing file length checks and per-asset error paths cover both additions; the child directory has 28 records including dot entries, well below the 256-entry GFS limit.

## Validation

Completed successfully:

- `make test`: **240 PASS reports**, including approved balanced camera tests, Level 1, Stage Clear, X skip, combat, audio, sprite state, filesystem and staging regressions.
- Targeted Level 2 suite: **60 PASS reports**, including UBSan gameplay/runtime/audio tests, 100,000-tick gameplay stress, 10,000-tick coop visibility stress, and original polyphonic audio overlap/readiness/E108 checks.
- Native indexed-tile reconstruction of both maps, every cell's palette/address/range, eight distinct authored compounds and seven silhouettes, initialized lower backing, transparent skyline fade and continuous lower vertical wrap.
- **24,577 camera positions** at 1/256px precision checked for exact half-rate algebra and in-map coverage; all **512 vertical scroll phases** remain legal. Actual runtime mocks check **193 half-pixel camera positions**, both layer scroll submissions, unchanged lower Y, skyline Y=0, priority, window, map/cell pointers and the 73-command VDP1 maximum.
- Exact preservation of approved camera/gameplay files, all hero/weapon art, audio sources/banks/metadata, Level 1 and workflow files. Prior locks remain unchanged; `docs/level2-city-lock.json` authorizes only twelve exact existing-file updates and freezes the new camera-delivery documents too. Background-specific checks advance to the new art rather than disabling preservation checks.
- Missing/corrupt upper payload rejection, exact 26-file staging and ISO contents, no stale root files, parent-directory restoration, arena sentinels and no gameplay allocations/uploads/I/O.
- Native build using the unchanged pinned Jo Engine/compiler; `make check` validates the real BIN/CUE and all exported payloads. `git diff --check` passes.

Host/native tests verify structure and deterministic behavior. They do not establish the new art's appearance, SGL timing or frame rate in WebRetro/on hardware. The approved camera is unchanged; the new visual presentation still needs a manual playtest.

## Build and review

With README native prerequisites installed:

```sh
bash tools/setup.sh
bash tools/build-level2-wingsuit.sh --native
make test
make check
```

Art regeneration, only when deliberately editing the city: `python3 tools/build-level2-city.py`. The normal public build uses committed native assets and needs no art regeneration or private inputs. In this environment the host ISO tools are under ignored `.deps/host-tools/usr/bin`, added to PATH for build/check commands.

Artifacts: matching `build/mullet-force.bin` and `build/mullet-force.cue`, MODE1/2048. Keep them together and open the CUE.

Manual Actions settings: **Use workflow from `main`; Profile `stage-default`; Source ref = the exact new delivery SHA**. No Actions run is triggered automatically.

In WebRetro, use X to enter Level 2. Pan fully left/right, reverse slowly, dodge within the dead zone and verify half-speed skyline movement without a seam or HUD bleed. Allow a full vertical cycle to see all eight compounds and the road wrap. Check readability with both heroes, aimed shots, held Flame and overlapping explosions; then test pause/restart and the normal Stage Clear transition. Capture performance or display issues before accepting this visual pass.
