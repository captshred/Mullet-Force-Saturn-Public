# Level 2 flame / focus / death audio / development skip

Historical report for the first flame build. For current beam geometry, activation,
and Saturn X controls, see [flame tuning pass 2](level2-flame-tuning-pass2.md).

Branch: `feature/level2-flame-focus-pass`. Parent: approved hero-art commit
`785d2f8c0ea602c1d65f348154c107a4f1c3cd96`.

## Weapons and movement

Tap A retains the original atomic three-projectile fan, bullet texture, seven-tick
minimum repeat interval, velocities and fixed pools. Normal axial speed remains
640/256 = 2.5 pixels/tick; diagonal components remain 452/256. The twelve-tick
hold threshold remains unchanged. At that threshold the held weapon becomes an
attached flame, without allocating focused projectiles. Releasing A or disconnecting
cancels it at the next simulation tick; life loss and respawn also deactivate it.
Existing visible tap bullets finish their original flight.

Focus speed is `normal * 65 / 100`, using integer fixed-point arithmetic:
416/256 = 1.625 pixels/tick axially, 293/256 per diagonal component. Banking still
uses actual player motion. No hero coordinates or approved hero textures changed.

Four native RGB555 32x128 frames (`WFL0.BIN` through `WFL3.BIN`) form the flame.
They reuse the red-orange/yellow/hot-cream palette of Level 1's `FL0..3.TGA`,
whose four-frame rendering was inspected before implementation. Irregular sides,
a changing tip, and a bright core animate every three simulation ticks (20 frame
changes/sec at 60 Hz; one full cycle every twelve ticks). Each player submits one
sprite through the existing restored SGL render path, at player center X minus
16, center Y minus 15 minus 128. Both players share the same four definitions;
Chuck's animation has a one-frame phase offset. Pause freezes simulation/animation.

Collision is simulation-only: one pulse immediately on focus activation and one
per six held simulation ticks thereafter (10 Hz). Each pulse checks the current
player position against active drones in a 24x128 rectangle extending upward
from Y minus 15, expanded by each drone's existing collision half extents 10x10.
Each overlap takes one damage; current drones have one hit point. This amounts to
10 damage/sec against a continuously vulnerable target, with at most one kill
per drone. Two beams cannot double-count the same death. Rendering never applies
damage. No hidden focused projectile survives release. Maximum range is 128 pixels.

## Canonical death sound and SCSP handoff

`src/music.c` routes `MF_WORLD_IMPACT` (Level 1 barrel/inorganic destruction) to
`assets/cd/FX.SEQ` song 2, which selects `assets/cd/FX.TON` voice 2. This is the
canonical `explode_1.wav` conversion already present in the approved runtime bank.
The original PCM is 31,680 bytes, SHA256:
`2eca5219e7a0255532d46c6c0a4835dee475781787334da46bfb451363e4fa6b`.

`tools/flame_focus_assets.py` extracts that exact voice and PCM into a single-voice
`WDEATH.TON`; only its sample pointer changes. Tuning, envelope, gain and samples
remain exact. It retains the required eighteen-byte mixer record. `WDEATH.SEQ`
retains the canonical one-shot song, changing only program 2 to program 0.
All deaths share this one sample in SCSP; there is no per-player/per-drone copy.
The extra ISO bank is necessary because the Level 1 sound bank is released.

After the existing sound-CPU halt and whole-SCSP wipe, the loader reads the compact
map/sequence/tone from `/ALEVEL2`. It uses the approved `SND_Init` + `slInitSound`
pairing and the already linked 26,610-byte driver, waits for DMA before freeing
buffers, resets the driver's transfer-complete flag, then starts the sound CPU.
The reserved DSP/work regions remain silent. The old music dispatcher is bypassed
once Level 2 owns the stage. No stale Level 1 ID is played.

The simulation emits a transient death count only when an active drone is killed
or Buck/Chuck actually loses a life, including their last life. Invulnerability,
respawn, and lingering explosions emit no further events. The runtime queues each
tick's count once. Four sequence ports (1..4), bank 0/song 0, play independent
one-shots with the approved SFX gain/priority. Busy ports finish before reuse:
47 canonical ticks plus a two-VBlank release guard. Bursts queue in a fixed-size
counter and drain without replacing another death's playback; rejected SDK commands
remain pending. There is no heap allocation, file I/O, or sample duplication during
play. Timing uses the hardware VBlank clock, so catch-up steps cannot bypass the
guard. Queued burst sounds may be delayed. SCSP playback still requires playtesting.

All twenty stage files retain asset-specific missing/read/length reporting;
`WDEATH.MAP`, `.SEQ`, and `.TON` failures display their own name and expected size.

## Development Z shortcut

`MF_DEV_STAGE_SKIP=1` enables `JO_KEY_Z`, the Saturn pad Z constant (SGL bit 4),
through the existing active-low Jo input adapter on physical ports 1 and 2
(logical slots 0 and 6). No WebRetro keyboard key is embedded. A pressed edge in
started, unpaused Level 1 enters its existing settling state with a one-tick timer.
The normal stage-transition function then enters Stage Clear and its normal
120-tick banner, followed by `MF_STAGE_LEVEL2_ENTRY`. The sole existing main-loop
handoff performs all draining, `/ALEVEL2` loading, and SGL restoration. Holding Z
cannot restart that path, and the actual kill counter is not falsified.

The `stage-default`/Level 2 development wrapper defaults the flag to 1. Other
profiles default to 0. Set `MF_DEV_STAGE_SKIP=0` for a release build: both the input
mapping and shortcut body compile out. Z has no other current game action. The
shortcut ignores title, pause, Stage Clear, and Level 2; it does not add a Level 2
restart or alter normal forty-kill completion. BUILD-INFO records the flag.

## Exact resources

| Resource | Approved hero pass 3 | This pass | Delta |
| --- | ---: | ---: | ---: |
| VDP1 texture payload | 15,744 B | 48,512 B | +32,768 B |
| VDP1 definitions | 10 | 14 | +4 |
| Maximum object draw commands | 58 | 60 | +2 attached beams |
| VDP2 reservation | 434,176 B | 434,176 B | 0 |
| Level 2 VDP2 cells/map payload | 10,944 B | 10,944 B | 0 |
| Level 2 CRAM payload | 32 B | 32 B | 0 |
| Level 2 sound-bank data in SCSP | 0 B | 31,788 B | +31,788 B |
| `/ALEVEL2` file contents (before ISO sector padding) | 26,720 B / 13 files | 91,316 B / 20 files | +64,596 B / 7 files |
| Player/hostile/enemy pools | 32 / 16 / 8 | 32 / 16 / 8 | 0 |
| Simulation state (host, 32-bit fields) | 1,408 B | 1,420 B | +12 B |

New graphics: four frames x 8,192 B. New sound files: SEQ 44 B, TON 31,744 B,
MAP 40 B (31,828 B on disc). SCSP regions: sequence `[148864,148908)`,
tone `[148908,180652)`; lower 148,864 B conservatively reserved for driver/work,
transfer, DSP and PCM work. Total reserved high-water 180,652 B of 524,288 B,
leaving 343,636 B contiguous. The 26,610-byte driver fits inside the lower reserve;
the map buffer is released from work RAM after initialization. The prior Level 1
432,308-byte sound reservation is unchanged and is wiped at handoff.

The new audio dispatcher uses 28 B of static counters/port state. Runtime texture
IDs gain 16 B. Largest logical transient stage-read buffer is 31,744 B, then freed.
No additional projectile/explosion pool exists; eight existing drone explosion
slots remain. Two beam cooldowns and one death count explain the +12 B simulation
state. Native code/allocator overhead cannot be measured until SDK access works.
The stage-specific bank remains well below the original memory budgets.

## Preservation and validation

All thirteen prior Level 2 payloads are pinned by `docs/flame-preservation.json`;
all six hero exports, industrial background, drones, bullets and explosions are
unchanged. Existing Level 1 asset locks remain in force. `src/game.c` and game.h
are unchanged. Only the existing exact integration after-hashes are updated for
main/build files; two new exact before/after input locks cover the Z adapter.
No preservation check is removed or converted into a broad exemption.

`make test` passed (206 PASS reports): existing full-profile gameplay traces, normal forty-kill transition,
canonical hero art, VDP1 restoration, exact `/ALEVEL2` contents/location, malformed
asset diagnostics, plus the flame/audio/dev controls all run. The flame runner
also compiles the actual simulation, weapon, audio and runtime tests with UBSan
and abort-on-error. A 100,000-tick simulation stress test remains active.

Source checks: `python3 tools/validate-wingsuit.py`,
`tools/validate-arcade-fx.py`, `tools/validate-full-gameplay-sfx2.py`,
`tools/validate-sfx2.py`, `tools/check-public.py`, `tools/check-city-neon.py`,
`tools/check-gameplay-parallax.py`, `tools/check-city-cleanup.py` (each with python3).
Disc-layout tests construct a 303-record root to verify the early stage directory,
all twenty exact child payloads, corruption/missing/late-directory rejection and
unchanged Level 1 staging. These are structural fixtures, not a compiled game disc.

Native compilation is blocked in this environment: `tools/setup.sh` cannot connect
to the configured proxy at port 8080 to obtain the pinned Jo Engine checkout.
No BIN/CUE is produced here, and no emulator, audio listening, or real-Saturn
validation is claimed. GitHub Actions is not dispatched by this change.

## Manual build settings

On GitHub, open **Manual Saturn playtest build** (`.github/workflows/build.yml`):

- **Use workflow from:** `feature/level2-flame-focus-pass`
- **profile:** `stage-default`
- **source_ref:** full delivered commit SHA (reported with delivery; the feature
  branch name also resolves to it until further commits).

The workflow is `workflow_dispatch` only; publishing this branch does not run it.
The development build enables Saturn Z and preserves committed audio. Download
`mullet-force-stage-default-<full SHA>` and keep its BIN/CUE together. BUILD-INFO
must show that same commit, Level 2 wingsuit 1, and Dev Saturn Z stage skip 1.

For a local build on x86-64 Linux with host prerequisites installed:

```sh
bash tools/setup.sh
bash tools/build-stage.sh --native
make check
make test
```

For release controls use `MF_DEV_STAGE_SKIP=0 bash tools/build-stage.sh --native`.
No workflow input was added and no workflow file was modified.

Manual playtest: verify Level 1 forty-kill completion and Z both reach the same
Stage Clear/handoff; join Chuck; tap while moving; hold through twelve ticks and
compare drag/diagonals; move both active beams; release; destroy drones; lose one
life and a final life for each player; listen for one barrel sound per death;
pause/restart and confirm no stray T. Check background/HUD priority and every hero
bank pose on actual Saturn/WebRetro before treating visual/audio behavior as approved.
