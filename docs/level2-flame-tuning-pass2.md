# Level 2 flame tuning pass 2

Historical report for the confirmed tuning build. For the added ignition cap and
snapshot aiming, see [flame origin and aimed drones](level2-aimed-drone-pass.md).

Branch: `feature/level2-flame-tuning-pass2`.
Parent: confirmed playable `5b07fe92676d4f3cc8c431be057ae6bbb6efa1fe`
(`feature/level2-flame-focus-pass`). This document supersedes the earlier flame
geometry/activation and Z-control instructions. Existing audio and handoff details
in the [first flame report](level2-flame-focus-pass.md) still apply.

## Visible width and animation

The four flame frames are now **32x32 RGB555 body tiles**, retaining the original
four red/orange/yellow/hot-cream colors and zero transparency. The visible body
averages **23 pixels** per row (range **21..25**), compared with **27.40625 pixels**
in the old fully developed body (range 23..32). That is **16.08% narrower**, close
to the requested 15%. The old measurement uses rows 88..127 across all four old
32x128 frames, where their designed growth/taper has reached its full width. It
excludes the old narrow terminal tip, which has been removed rather than used as
a width reference. The container remains 32 pixels wide for native alignment.

Every new row has a wide, contiguous opaque body and the bright central core.
The width and center wobble periodically; no row intentionally converges to a
point. First and last rows meet pixel-for-pixel in every frame. Animation shifts
the body upward eight texture rows per frame, changes frame every three simulation
ticks (20 Hz), and repeats every twelve ticks. Both players share the same four
textures, with Chuck offset by one animation frame. All segments of one beam use
the same phase, preserving exact tile seams during animation. Pause still freezes
simulation and animation.

## Full-height rendering and collision

The emitter is unchanged: player center Y minus 15 pixels. Starting there, the
renderer repeats 32-pixel body tiles upward until the final tile reaches or passes
**Y=0**, the upper gameplay boundary. Adjacent command positions differ by exactly
32 pixels: their raster rows are contiguous, without gaps or overlapping alpha
edges. The existing VDP1 system clip trims the uppermost tile, whose top is between
-31 and 0. Tiles follow the player's current X/Y without scaling or coordinate
workarounds, through the existing restored SGL path at Z=100.

Commands per player are `ceil((floor(playerY)-15)/32)`:

| Player center Y | Emitter Y | Flame draws | Top tile Y |
| ---: | ---: | ---: | ---: |
| 16 | 1 | 1 | -31 |
| 32 | 17 | 1 | -15 |
| 47 | 32 | 1 | 0 |
| 64 | 49 | 2 | -15 |
| 128 | 113 | 4 | -15 |
| 200 | 185 | 6 | -7 |
| 223 | 208 | 7 | -16 |

Collision is a single continuous region from **Y=0 to the emitter**, centered on
player X with **11-pixel half-width** (22-pixel core width). The surrounding visible
edge flickers between 21 and 25 pixels. The test expands this region by the existing
drone collision half extents (10x10); a drone touching either boundary can be hit.
The former fixed 128-pixel limit is gone. Collision does not multiply with the
number of rendered tiles: pulses occur on focus activation, then every **six
simulation ticks** (10 Hz), at one damage per overlapping drone. Current drones
have one hit point. Damage/death events and six-tick cadence are unchanged.
Release or disconnect deactivates focus at the next simulation tick; no focused
projectile remains. Existing visible spread bullets retain their normal lifetime.

## Activation and controls

Focus now engages on the **twentieth continuous held tick**, about 0.333 seconds
at 60 Hz. At nineteen ticks the player still uses spread behavior and full movement
speed. The first press still produces the same atomic three-way fan. Releasing
resets the hold counter and flame cadence immediately on the next simulation tick;
repeated nineteen-tick taps never accumulate focus.

Movement remains unchanged: full axial speed 640/256 (2.5 pixels/tick), diagonal
components 452/256. Focus uses **65%**, yielding 416/256 axial and 293/256 diagonal
components with the existing integer rounding. No gameplay coordinates, hero art,
or banking selection changed.

Development stage skip now uses **Saturn X**, via **`JO_KEY_X`**. Verified directly
against pinned Jo Engine revision `556d081146211b6a1cfa6591d70f9487d406758b`,
[`jo_engine/jo/input.h`](https://github.com/johannes-fetz/joengine/blob/556d081146211b6a1cfa6591d70f9487d406758b/jo_engine/jo/input.h):
its SGL branch defines X as `1 << 6` and Z as `1 << 4`. No WebRetro keyboard key is
hardcoded. The dedicated dev-input mock now uses that actual SGL layout; the old
protected Level 1 fixture remains unchanged. The earlier report/mock's bit-0
annotation for Z was the non-SGL value; production always used the symbolic SDK
constant.

`MF_DEV_STAGE_SKIP` keeps its existing guard/defaults. Only an X **pressed edge**
in started, unpaused Level 1 changes its existing settling state. The normal Stage
Clear and sole Level 2 entry/handoff then release resources, load `/ALEVEL2`, and
restore SGL. Holding X cannot restart the stage; Z has no shortcut action. Normal
forty-kill completion is unchanged. Development `stage-default` builds enable the
shortcut; `MF_DEV_STAGE_SKIP=0` compiles out both mapping and shortcut body. BUILD-INFO
now labels it `Dev Saturn X stage skip`.

## Resources

| Resource | Prior flame pass | Tuning pass 2 | Change |
| --- | ---: | ---: | ---: |
| Flame frames | 4 x 32x128 | 4 x 32x32 | Reusable body tiles |
| Flame texture payload | 32,768 B | 8,192 B | -24,576 B |
| Total VDP1 textures | 48,512 B | **23,936 B** | -24,576 B |
| Total VDP1 definitions | 14 | **14** | 0 |
| Max flame draws/player | 1 | **7** | +6 |
| Max two-player flame draws | 2 | **14** | +12 |
| Max object commands, all pools | 60 | **72** | +12 |
| VDP2 reservation | 434,176 B | **434,176 B** | 0 |
| Background cells/map payload | 10,944 B | **10,944 B** | 0 |
| CRAM payload | 32 B | **32 B** | 0 |
| SCSP bank data | 31,788 B | **31,788 B** | 0 |
| SCSP reserved high-water | 180,652 B | **180,652 B** | 0 |
| `/ALEVEL2` file payload | 91,316 B / 20 files | **66,740 B / 20 files** | -24,576 B |
| Simulation state | 1,420 B | **1,420 B** | 0 |
| Player/hostile/drone pools | 32 / 16 / 8 | **32 / 16 / 8** | 0 |

The count of 72 is 2 players + 32 spread shots + 16 hostile shots + 8 drones or
explosions + 14 flame commands. HUD remains NBG0 text. The pinned SDK makefile links
`Compiler/COMMON/SGL_302j/LIB_ELF/SGLAREA.O`; inspecting its `_MaxPolygons` word at
SLPROG offset 0x0a gives **0x06e1 = 1761**. The tested worst case is well inside
that existing capacity, without expanding SGL work/command buffers. Fourteen
texture definitions also remain below Jo's 255-definition limit. No dynamic
allocations, extra effect pool, sprite scaling, or per-frame file I/O is added.

Sound remains exactly the same compact canonical barrel bank: `WDEATH.SEQ` 44 B,
`WDEATH.TON` 31,744 B, `WDEATH.MAP` 40 B; sequence at 148864, tone at 148908,
end 180652 of 524288 SCSP bytes. Reserved lower driver/work regions and the linked
26,610-byte driver are unchanged. There is no native code-size measurement here.

## Preservation and tests

`docs/flame-tuning-preservation.json` pins all sixteen non-flame stage payloads
and the unchanged audio/game/main/workflow sources to the parent commit. The
original thirteen-payload hero/background lock and every existing Level 1 asset
check remain active. Only the existing input after-hashes and build-native
BUILD-INFO after-hash change; all baseline hashes remain intact. The handoff,
VDP1 restoration, background, approved six hero poses, drones, spread bullets,
explosions, exact death PCM/SEQ/TON/MAP, stray-T erase, and 2P architecture remain.

`make test` passed with **211 PASS reports**, including the full existing host suite, normal forty-kill transition,
16,000-tick full-gameplay equivalence trace, exact canonical audio, all assets,
100,000-tick wingsuit stress, and the tuning regressions. New checks cover:

- Measured narrowing, every row's contiguous body/core, no terminal tip, exact
  tile-edge equality, and upward cyclic frame motion.
- The actual renderer at seven player Y positions and twelve animation ticks;
  row-by-row gap-free coverage, attachment, top clipping extent, and simultaneous
  full-pool two-player 72-command output.
- Collision at Y=0, just outside the top, and just below the emitter across six
  player heights; release, lateral movement, six-tick pulses and one death event.
- P1/P2 activation exactly at 20 ticks, no flame at 19, repeated sub-threshold
  taps, unchanged 65%/full movement and diagonal normalization.
- Actual input adapter X held/pressed edges on physical slots 0/6, Z ignored,
  dev enabled/compiled-out configurations, and normal settling/clear/entry path.
- Exact twenty-file `/ALEVEL2` contents, directory order, corrupted/missing files,
  unchanged death bank and original hero/art/preservation checks.

The actual simulation, weapon, flame, audio, and runtime tests also run with UBSan
and abort-on-error. Static validation commands remain:

```sh
python3 tools/validate-wingsuit.py
python3 tools/validate-arcade-fx.py
python3 tools/validate-full-gameplay-sfx2.py
python3 tools/validate-sfx2.py
python3 tools/check-public.py
python3 tools/check-city-neon.py
python3 tools/check-gameplay-parallax.py
python3 tools/check-city-cleanup.py
```

Native compilation remains blocked here: `tools/setup.sh` cannot connect to the
configured proxy on port 8080 to fetch the pinned SDK. No new compiled BIN/CUE,
emulator/WebRetro playtest, audio listening, or real-Saturn validation is claimed.
The user's successful playtest applies to the parent flame build. ISO checks here
use structural fixtures, not a newly compiled game disc.

## Exact manual Actions settings

Open **Manual Saturn playtest build** (`.github/workflows/build.yml`):

- **Use workflow from:** `feature/level2-flame-tuning-pass2`
- **profile:** `stage-default`
- **source_ref:** full new commit SHA supplied in delivery. The feature branch name
  also resolves to that commit until further changes.

The unchanged workflow is `workflow_dispatch` only. No Actions run is dispatched
by this change. Artifact: `mullet-force-stage-default-<full SHA>`; keep BIN/CUE
together and verify BUILD-INFO records that SHA, Level 2 wingsuit 1, and
`Dev Saturn X stage skip: 1`.

Local build on x86-64 Linux with the pinned SDK/prerequisites available:

```sh
bash tools/setup.sh
bash tools/build-stage.sh --native
make check
make test
```

For release controls: `MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
Playtest both X and normal forty-kill entry, nineteen-tick taps versus deliberate
holds, full-height beams at top/bottom movement limits, both players' banking and
beam seams, release, unchanged death sounds, pause/restart and HUD/background.
