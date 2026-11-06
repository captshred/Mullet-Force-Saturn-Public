# Level 2 wide playfield and horizontal camera

Baseline: `78cc4dfa4fac6dcde3d8d21ac9e78ca8337ee75e`, the user-confirmed WebRetro polyphonic-audio build. Branch: `feature/level2-wide-camera`. The exact delivery commit is supplied in the delivery response. No Actions dispatch; workflow files are unchanged and have only `workflow_dispatch` triggers.

## Baseline audit

The hardware display is **320x240**, but the actual Level 2 gameplay/background viewport is **224x240**, at screen X **48..271**. Existing text HUD columns occupy the sides. This pass preserves that viewport and HUD; treating 320 as the gameplay viewport would overwrite them.

NBG1 already uses a **512x512** cell map (64x64 8px cells), `COL_TYPE_256`, `CHAR_SIZE_1x1`, `PNB_1WORD|CN_12BIT`, `PL_SIZE_1x1`; all four plane pointers alias the same map. This is an indexed tile background, not a bitmap. Each 8bpp character occupies 64 bytes; 43 deduplicated characters consume **2,752 bytes**. Each pattern name is two bytes: 4,096 names consume **8,192 bytes**. Pattern names use palette bank 1 and tile IDs in 32-byte hardware units. The original authoring city was 256x512 and its 32 columns were copied into both halves of the hardware map. Horizontal repeat was 256px. Cross-streets repeat every 128px; rooftop accent arrangements alternate every 128px.

Baseline NBG1 X scroll was always zero. Y was `-scroll*65536`, with `scroll=(scroll+1)&511` once per unpaused simulation tick: one downward pixel/tick, 512-tick hardware wrap. Existing vertical object coordinates use the screen-height simulation model; enemies move downward 320/256 px/tick independently of background scrolling.

Baseline player/enemy/projectile coordinates were 24.8 centers effectively in screen X. Player centers were constrained to 64..255; drone spawn X was 72 + wave*47 mod 176. Player shots expired outside 52..267; hostile bullets outside 44..275. Collision tests used those same coordinates directly. Aimed shots selected the nearest living, active, nonrespawning player at age 80 and normalized a fixed snapshot velocity. Flame used world-compatible rectangular coordinate comparisons already, with no camera input.

Transferred VDP2 arenas: A0 starts at `0x25e00000`, reservation **106,496** bytes; B0 starts at `0x25e40000`, reservation **65,536** bytes. Loader clears these arenas before installing stage assets, preserving SDK NBG0/font, back-screen, and other protected storage. NBG2 remains disabled. Including the existing **262,144** SDK-protected bytes, total reservation is **434,176** of 524,288. The stage uses 16 colors/**32 bytes** in CRAM bank 1; seven transferred banks are cleared, bank 0/font preserved. No new palette allocation.

## Width calculation and choice

| Logical width | Columns | Logical name bytes at 512px height | Required existing hardware page | Tile+map payload | Additional reservation | Camera travel |
|---|---:|---:|---:|---:|---:|---:|
| 448 | 56 | 7,168 | 8,192 bytes / 512x512 | 10,944 | 0 | 224px |
| **512** | **64** | **8,192** | **8,192 bytes / 512x512** | **10,944** | **0** | **288px** |

448 cannot reduce the hardware page allocation in this architecture. **512** fully uses the existing page, adds useful scenery/travel, and costs no additional tile, map, palette, or reservation bytes. There is no larger map or conversion to a bitmap/VDP1 background.

## Camera and world behavior

Named controls live in `src/wingsuit.h`: stage width 512; viewport left 48/width 224; dead-zone thresholds **50 and 174 relative to the viewport** (screen **98 and 222**), width 124px / **55.36%**; maximum camera speed **3px/tick** (768 in 24.8); hero half-width/margin 16px. Camera clamps to **0..288px**. Player centers clamp to **16..496px**. Initial camera X=48px preserves the baseline screen registration of the original 130/190 world-X starting positions.

Every gameplay X stays in world space. Viewport-relative X is `world_x-camera_x`; full-display X is **`world_x-camera_x+48`**. One fixed-point helper implements that transform for players, drones, explosions, both projectile types, and the Flame body/emitter. Collision rectangles remain in world space; transforming both Flame edges preserves their width exactly. No per-object screen coordinate is stored.

For the living players' world bounds [lo,hi], the normal feasible camera interval is `[hi-174, lo-50]`. If it is nonempty, choose its nearest point to the current camera, preserving a stationary dead zone. If the players span more than the dead zone, use their collective midpoint. Restrict the target to the interval that shows both complete 32px heroes and then to the stage boundaries. Approach the target by at most 3px/tick, never overshooting. This uses integer arithmetic, retains subpixels, and has no floating-point requirement or frame-rate-dependent easing. The maximum hero movement remains 2.5px/tick, below the camera speed.

Coop containment caps center separation at **192px** (224 minus two 16px margins). When proposed movement exceeds it, undo only outward movement, proportionally when both move outward. A stationary partner is not dragged; neither player receives leader priority. The resulting visibility interval takes priority over the ordinary dead zone. Both players can reverse or move together afterward. A defensive symmetric repair handles an externally invalid restored state; normal movement uses the bounded correction.

Inactive, dead, and respawning players do not pull the camera. A disconnected but active living hero remains visible and receives zero controller input, preserving existing disconnect semantics. Late join and respawn place the returning hero at its original screen slot inside the current camera view, avoiding a teleport of the camera. X reset moves from damage time to actual respawn; damage/lives/invulnerability/respawn delay remain unchanged. The respawn completion tick still skips weapon/movement processing as in the baseline. Pause freezes the camera; restart initializes it with the stage.

## Enemies, projectiles, and background

Drones now spawn at **24 + wave*47 mod 464**, covering world X 24..487 independently of the camera. The fixed pool, 45-tick cadence, downward trajectory, age-80 shot, explosion lifetime and scoring are preserved. Coprime stride 47 traverses every lane. Off-camera enemies remain simulated and can be revealed without teleporting.

Aimed-snapshot implementation is byte-identical to the baseline, including nearest-target rules, integer normalization, and non-homing velocities. Projectiles use wider world cleanup bounds (player shots 4..508; hostile bullets -4..516). Velocity, TTL, shot cadence, HP/damage, Flame geometry and pulse cadence are unchanged. No collision or velocity calculation reads camera X. Only join/respawn placement intentionally uses the current visible area.

NBG1 hardware scroll remains `slScrPosNbg1`: X **`(camera_x-48*256)*256`** converts the camera's 24.8 into SGL 16.16; Y is the exact original `-scroll*65536`. X drives the NBG1 SCXIN1/SCXDN1 path; Y drives SCYIN1/SCYDN1. Unity zoom and all plane/bank allocations remain unchanged. At camera 0, visible map columns cover world 0..223; at camera 288, 288..511. The display's hidden HUD areas may wrap, but no wrapped/blank area enters the visible playfield.

`tools/recompose-wide-city.py` retains the original left 256px district and populates the right district from the original rows offset by 128px. Cross-streets still meet, alternate rooftop details differ, and the exact horizontal map repeat becomes **512px**. No scaling, mirrored cells, new palette, or new art is used. Native map words and shared cells remain independently replaceable for the later art-variety pass. The tool is idempotent; run it after the historical private asset generator if regenerating the original assets. No authoring masters were added.

VDP1 culls fully off-camera sprites and uses one user-clipping command (depth 101, ahead of the existing depth-100 sprites) to clip partial sprite/Flame edges to X48..271/Y0..239. Clipping attributes are restored afterward. This keeps bullets and enemies from drawing over the HUD while leaving their world physics active.

## Resource report

| Resource | Before | After |
|---|---:|---:|
| VDP1 texture bytes | 28,032 | 28,032 |
| VDP1 definitions | 18 | 18 |
| Gameplay sprite commands | 72 | 72 |
| Maximum stage commands, including user clip | 72 | **73** |
| VDP1 texture-area headroom (458,488-byte area) | 430,456 | 430,456 |
| Definition headroom (255) | 237 | 237 |
| Command headroom (1,761 budget) | 1,689 | 1,688 |
| VDP2 character payload | 2,752 | 2,752 |
| VDP2 map storage | 8,192 | 8,192 |
| VDP2 total background payload | 10,944 | 10,944 |
| VDP2 stage arena reservation | 172,032 | 172,032 |
| VDP2 total reservation | 434,176 | 434,176 |
| VDP2 unreserved headroom | 90,112 | 90,112 |
| Stage CRAM payload | 32 | 32 |
| SCSP high-water | **307,260** | **307,260** |
| SCSP free | **217,028** | **217,028** |
| Gameplay state (32-bit integer ABI) | 1,488 | **1,492** |

Bank headroom, unchanged: A0 **24,576** bytes outside its arena, plus **103,744** unused bytes inside the transferred reservation; B0 **65,536** outside its arena, plus **57,344** unused inside it. A1 and B1 retain the conservative SDK reservation of 131,072 bytes each, with **zero newly claimable** bytes reported. Inside-arena space is available for future stage art but is not returned to the SDK allocator. Combined unreserved A0/B0 space is 90,112 bytes, and another 161,088 stage-arena bytes are unused.

Additional mutable camera state is one 4-byte integer; no additional persistent map/background state, heap allocation, per-frame upload, or file read. The renderer adds a 72-byte constant width table. Update scratch values are bounded automatic locals; exact stack high-water and CPU frame time require emulator/hardware measurement. Native linked `game.raw` is 230,032 bytes in this build. No SCSP allocation, music, tone, PCM, audio clock, or event-transport change.

## Preservation and verification

`docs/level2-wide-lock.json` freezes **1,146** unchanged baseline files and records exact before/after digests for the 17 explicitly changed existing files. Prior locks remain unchanged. Additive scope helpers authorize only exact new digests, including WMAP/manifest and test adaptations; no broad exemption or disabled preservation suite. `tools/validate-level2-wide.py` checks this scope, the whole audio bank/source/metadata, the byte-identical loader/runtime audio sections, map cells/seams, and budgets. Original aiming and Flame collision sections retain their exact section hashes.

The following completed successfully:

- `make test`: **230 PASS reports**, including Level 1, Stage Clear, X skip, Level 2 combat, audio, loader, rendering and disc/staging regressions.
- Final `python3 tools/test-wingsuit.py`: camera clamp/left/right/no over-scroll, central dead zone and both threshold crossings, bounded approach/no overshoot, subpixel conversion, all object draw transforms and Flame geometry, actual NBG1 horizontal/vertical scroll values, six coop movement patterns, maximum separation, stationary-partner protection, death/inactivity/join/respawn, 10,000-tick visibility/speed and all 464 world spawn lanes.
- Identical world-state fixtures with distinct camera X values produce identical complete gameplay state (after excluding the camera field): Shot/Flame kills and score, hostile/contact damage, enemy trajectory and age-80 aimed world velocity. Existing non-homing flight tests continue passing.
- UBSan gameplay/runtime/audio regressions; 100,000-tick pooled gameplay stress; original 20-tick focus, 65% movement, centered single Shot and full-height Flame tests.
- Audio checks: independent direct-MIDI Shot/Explosion, four overlapping Explosion controls, two-player split Flame, 38-VBlank handoff, 600-VBlank mixed holds, readiness/E108, natural endings and no persistent Loop stop/restart. All audio source files/assets/metadata match baseline bytes.
- Actual pinned 2.10 allocator instruction snapshot audit: 2,000 allocations with two Flames and six one-shot controls, zero active replacements in the tested normal schedule; pinned driver SHA `68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6`. Driver was found in the SDK's INC directory and copied into the existing audit search location under ignored `.deps`; no SDK source/pin was changed.
- Native build with pinned Jo revision `556d081146211b6a1cfa6591d70f9487d406758b` and bundled GCC 8.2.0; `make check` including exact `/ALEVEL2` ISO content, payloads and Level 1 preservation; `git diff --check`.

Native artifacts are `build/mullet-force.bin` and its matching MODE1/2048 `build/mullet-force.cue`; neither is committed. No emulator/hardware play or camera-feel approval is claimed.

## Manual WebRetro validation remaining

Use **workflow from `main`**, profile **`stage-default`**, **Source ref = the exact new delivery commit SHA**. Do not use the baseline SHA for this test. No workflow was triggered by this pass.

Use Saturn X to enter Level 2. Move Buck fully left, then fully right; verify new city area, camera boundary stops, no blank scenery/HUD bleed, and stable movement inside screen X98..222. Check responsive bounded panning and unchanged vertical pace. Fire Shots, sustain Flame, and overlap multiple explosions while panning; confirm the user-approved audio mix remains audibly identical. Test drone aiming during camera movement and after its shot has fired. Join Chuck, test opposed and collective horizontal motion, maximum separation, reverse movement, death/respawn and late join at both camera extremes. Confirm both heroes remain visible and no partner is dragged by an outward attempt at maximum separation. Test pause/restart and the normal Stage Clear transition as well as X skip.

Camera feel and audible behavior during camera movement require user approval in WebRetro before the separate city-art variety pass.
