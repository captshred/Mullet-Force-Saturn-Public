# Level 2 — Wingsuit Assault prototype

This branch implements a Saturn shooter, with host-tested gameplay and resource
handoff. See [the E102 filesystem repair](level2-e102-fix.md) for the subsequent
successful manual build, reported Level 1 playthrough, directory-table failure,
and /ALEVEL2 fix. The initial implementation status below predates that build. It is not yet a validated playable Saturn release. The pinned SDK could
not be installed because the configured shell proxy refused connections. No
native compilation, BIN/CUE, emulator run, real-controller test, hardware memory
measurement, or 60 Hz performance measurement is claimed. No Actions run was
launched.

## Source and progression

The exact baseline is `467fc259b2afce35a210db4e10d467c758fced7f`, the
Level 1 stage-clear branch including all three preservation-validation fixes.
Its Git commit objects and complete tree were retrieved through the GitHub
connector and verified by object SHA, because shell Git networking was unavailable.
The local feature branch has that exact parent; `main` and `the-one-v1` are not
modified. All 623 existing asset files retain their baseline blob hashes.

Level 1 still counts only legitimate Corporate Punk defeats. At 40 shared KOs,
the original settle and STAGE CLEAR sequence runs. The first Level 2 entry tick
transfers ownership away from Level 1, drains rendering, loads the shooter bank,
and displays a 120-tick LEVEL 2 / WINGSUIT ASSAULT title. There is no motorcycle
sequence or indefinite placeholder on the wingsuit profile. Other build profiles
keep their approved behavior. Level 2 restarts itself; returning to Level 1
requires rebooting. There is no supported runtime path back into old caches.

## Resource lifecycle

The pinned Jo Engine is `556d081146211b6a1cfa6591d70f9487d406758b`.
`jo_engine/sprites.c` has a real `jo_sprite_free_from(0)` API, exposed as
`jo_sprite_free_all()`. It resets both the texture allocator cursor and last ID.
`jo_sprite_init()` alone resets the ID but does not reset the address cursor and
is deliberately not used. The approved profile has no 3D sprite quads or slave
renderer. Level 2 uses raw `jo_sprite_add()` registrations, not filename hashes.

The main update callback's permanent `stage2_owned` gate prevents all Level 1
simulation, gallery, sprite draw, music updates, and animation callbacks after
handoff. The VBlank callback stops the Level 1 CRAM animation. Level 1 IDs and
alias views become obsolete, unreachable values; their referenced texture bank
is actually released. They cannot be used by the independent shooter renderer.
No heap pointer is freed while another renderer can access it.

Three separate callbacks with advancing VBlanks submit no sprites and pass
through Jo's core `slSynch()` barriers. The loader then stops automatic VDP1
restarts (`PTMR=0`), requires current-list completion (`EDSR.CEF`), releases all
sprite definitions, and wipes the old VDP1 texture area. A bounded wait failure
leaves VDP1 stopped and shows an NBG0 text error. Successful loading requires
an early /ALEVEL2 directory, exact file lengths and IDs 0 through 5 before restoring the saved trigger mode.
Partial texture-load failure releases the partial bank and never draws it.
Missing background files also enter a terminal text-only error state. No retry
can accumulate registrations. Saturn validation of synchronization remains a
release gate; host tests cannot prove SGL/VDP1 timing on hardware.

VDP2 uses reusable arenas rather than modifying the SDK allocation cursor. The
approved A0 cell allocation (106,496 bytes) and B0 map/sky allocations (65,536
bytes) transfer permanently to the shooter owner. Both are cleared, removing
Level 1 city and skyline data. Only 2,752 tile bytes and 8,192 map bytes are then
populated. SDK NBG0/text and back-screen memory remain untouched. NBG2 is
disabled, and NBG1 uses a 512x512 cell map with the window x=48..271. Seven CRAM
banks starting at street bank 1 are cleared; the shooter uses 16 colors in bank
1. Bank 0/font remains intact. No new VDP2/CRAM allocation occurs. The arenas
remain reserved and reusable; this is explicit reservation, not an assertion
that the SDK allocator has returned those bytes to a free list.

`slSoundOffWait()` halts the sound CPU before the loader clears the entire
512 KiB SCSP RAM, removing Level 1 samples and driver state. Level 2 is silent
for this prototype. No sound callback runs again and no audio pointer is reused.
A future stage-specific sound bank must explicitly reload/reinitialize audio.
The approved Level 1 music, samples, and transport are unchanged before handoff.

## Resource accounting

These are exact payload/static-allocation counts, not hardware telemetry.

| Resource | Level 1 | Level 2 |
| --- | ---: | ---: |
| VDP1 texture bytes, including alignment | 452,800 | 7,552 |
| VDP1 definitions, including aliases | 255 | 6 |
| VDP2 reserved (SDK + reusable arenas) | 434,176 | 434,176 |
| Stage cell/map payload | city + skyline | 10,944 |
| Stage cell/map arena reservation | 172,032 | 172,032 |
| Stage CRAM payload | existing banks | 32 bytes |
| SCSP loaded/reserved driver/sample plan | 432,308 | 0, CPU halted |
| Maximum player shots | n/a | 32 |
| Maximum hostile shots | n/a | 16 |
| Maximum drone slots, including explosions | n/a | 8 |
| Maximum simultaneous shooter sprite commands | n/a | 58 |

VDP1 textures are Buck 32x32/2,048 bytes, Chuck 32x32/2,048, drone 24x24/1,152,
player shot 8x8/128, hostile shot 8x8/128, explosion 32x32/2,048. All use RGB555
with zero transparency. The background uses 43 deduplicated 8x8 indexed tiles.
The native integer-only shooter simulation state is 1,208 bytes; the loader adds
six integer IDs, state flags, a clock, and a palette pointer. Load buffers are
bounded by the largest file, 8,192 bytes, and freed synchronously. There are no
per-frame allocations, texture uploads, or file reads. Exact total linked work
RAM, stack high-water marks, native binary size, and measured frame times await
a native build and emulator/hardware profiling.

## Gameplay and art

Buck and Chuck use original small overhead wingsuit art, heads facing up and
mullets trailing down. D-pad moves independently; held A fires every seven
ticks. P2 Start joins Chuck. Only Buck appears until Chuck joins. Players are
clamped inside the 224-pixel playfield, including sprite extents. Cardinal speed
is 640/256 pixels per 60 Hz tick; diagonal components are 452/256, giving less
than 0.13% rounding error from normalized speed. Disconnected ports cannot steer
or shoot; their existing actor can still be damaged.

Drones enter at a paced 45-tick interval after an initial 60-tick delay, descend,
fire once at age 80, and despawn. Shots expire and leave the screen safely. One
shot destroys a drone, starts a 12-tick explosion, and awards its owner 100
points. Pool exhaustion drops the request; no live object is overwritten.
Enemy contact/hostile fire removes a life, with 60-tick respawn delay and 120
ticks of post-respawn invulnerability. Each player starts with three lives.
P1 Start pauses; when both joined players have no lives, P1 Start restarts Level
2 with cleared pools and scores. No friendly fire, upgrades, bombs, or cinematic.

Industrial roof/vent/road/intersection/dock markings and restrained neon repeat
seamlessly over a 512-pixel downward scroll. Side margins carry player name,
score, lives, weapon-level placeholder, and P2 join prompt. This is intentionally
small prototype art and conservative bullet density; CRT readability and feel
need playtesting. `tools/build-wingsuit-assets.py` regenerates only the new
runtime assets; it requires Pillow. Builds consume committed payloads and do
not require Pillow or private art masters.

## Validation and build

Host checks:

- Complete `make test` exited 0 with 182 PASS reports, including the new
  `test-wingsuit` target.
- Existing stage-clear tests: legitimate kill attribution, both players/weapons,
  no duplicates, settle/clear timing, pause, and Level 2 entry.
- Actual shooter code: movement, diagonal speed, bounds, independent controls,
  disconnected input, both projectile pools, exhaustion/expiry, spawn cap,
  despawn, scoring, collisions, lives, invulnerability, respawn, pause/restart,
  and 100,000 simulation ticks.
- Actual Level 2 loader against hardware mocks: three advancing-VBlank drain,
  EDSR timeout, allocator reset, exact IDs/bytes, font and arena boundaries,
  SCSP wipe, partial file failure, and no gameplay I/O or registrations.
- Exact old asset hashes and unchanged Level 1 gameplay/render/audio/input
  modules; existing preservation checks remain active. Four source/build
  integration exceptions have exact before/after hashes chained after the
  existing Level 1 lock. No artwork or unrelated validator lock was relaxed.
- Address/undefined-behavior sanitizers for the new gameplay and loader;
  LeakSanitizer is unavailable under this environment's ptrace supervisor.

`make check` validates source/runtime preservation successfully but stops at
its existing disc-image check because no native BIN exists. This is an
outstanding check, not a passing native build. Pinned SDK setup and the native
build attempt fail at the configured proxy; compiler/engine pins are unchanged.

For a build-capable x86-64 Linux environment:

```sh
bash tools/bootstrap.sh
make clean
bash tools/build-level2-wingsuit.sh --native
make check
make test
```

Outputs are matching `build/mullet-force.bin` and `build/mullet-force.cue`.
The unchanged manual-only Actions workflow already supports `stage-default`.
After explicit user approval to launch a build, select **Manual Saturn playtest
build**, choose this feature branch (or exact delivery commit) as `source_ref`,
and select `stage-default`. Its checked-in build-stage wrapper selects the
wingsuit profile; normal preservation/disc/gameplay checks run, including exact
Level 2 disc payload validation. It uploads one matching BIN/CUE artifact with
one-day retention. No new workflow, push trigger, or automatic build is added.

Before treating this as playable, run that native build, boot its CUE in a Saturn
emulator, complete the real 40-KO path, exercise both controllers and repeated
Level 2 game-over/restarts, inspect the title/resource handoff for stale sprites,
and measure frame timing. Repeat on hardware before claiming Saturn stability.
