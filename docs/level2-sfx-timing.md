# Level 2 SFX timing

Branch: `fix/level2-sfx-timing`. Approved balanced-scroll parent:
`8504ddf8c9c04363862cb1e2cd3e068c0199d39e`.
The delivery response and built BUILD-INFO supply the exact new commit.

## Scheduling

Shot uses only controls/channels **2 and 3**, bank 0, program 1, key 60,
velocity 110 and the existing gain. Both players share this pool. Choose a free
control first; otherwise choose the greatest unsigned age since its last accepted
Note On. The alternating next-control index breaks equal-tick ties. Send direct
MIDI Note Off only to that control/channel/key, then Note On to the same control
from the start. A rejected Note Off retains the pending request; an accepted
Note Off with rejected Note On retains the selected control in RESTARTING state
until its Note On succeeds. There is no sequence stop/start or global command.

The unchanged `player_fire` assigns a projectile before setting its owner's
`shots_fired` bit. It returns failure without setting that bit when the 32-slot
projectile pool is full. Each player can spawn at most one bullet per simulation
tick. The unchanged runtime forwards this bitmask once per simulated tick.
Each set bit adds one attack request; dense dual-player tests drain two attacks
per tick, even while both Shot PCM leases remain occupied. The existing bounded
Shot pending mechanism holds four requests for command retries; prolonged SDK
rejection can still overflow that bound, counted by `dropped_shots`. Host tests
prove no drops during normal supported rapid fire and the mixed stress test.

`MF_WS_EXPLOSION_MIN_SPACING = 5u` VBlanks (about 83 ms at 60 Hz) gates accepted
Explosion Note Ons globally. Controls/channels **4..7**, bank 0, program 0,
key 60, velocity 110 and gain remain unchanged. Scan controls in index order,
reuse only FREE controls or expired conservative **49-tick leases**, and start
the next pending event as soon as both availability and the spacing gate permit.
SDK rejection does not consume an event or advance the gate. No Explosion Note
Off is issued, and no active Explosion is stolen.

The existing pending counter now has a fixed named capacity,
`MF_WS_EXPLOSION_PENDING_MAX = 8u`. Identical events require no payload FIFO.
Drop newest excess, count overflow, and preserve sounding voices. A fixed cap
also prevents unsigned room underflow as queued events fill the voice pool.
Visual deaths, gameplay and scoring do not wait for audio.

Three requests at tick 100 start at 100/105/110; separate requests at 100/106
start at those ticks. Explosion tails overlap: all four controls can remain live
following starts five ticks apart. Pool saturation waits for natural completion,
then drains pending work with the same minimum start interval.

## Preservation and resources

The complete 1,172-file baseline is covered by an additive exact digest lock:
six narrow implementation/test/validator exceptions and 1,166 unchanged files.
All old locks remain unchanged. Dedicated section hashes preserve the E108
loader, readiness handshake and Flame scheduler byte for byte. The 38-VBlank
Attack-to-Loop handoff, persistent loops, release and player independence remain
unchanged. Sound driver, maps, tones, PCM, gains, pitch, sample rate, loop points,
Level 1, stage transitions/dev skip, rendering, camera and gameplay are unchanged.

| Resource | Before | After |
|---|---:|---:|
| SCSP high-water | 307,260 B | 307,260 B |
| SCSP free | 217,028 B | 217,028 B |
| VDP1 textures / definitions | 28,032 B / 18 | 28,032 B / 18 |
| VDP1 maximum stage commands | 73 | 73 |
| VDP1 texture-area headroom | 430,456 B | 430,456 B |
| VDP2 background payload | 10,944 B | 10,944 B |
| VDP2 total reservation / free | 434,176 B / 90,112 B | 434,176 B / 90,112 B |
| CRAM payload | 32 B | 32 B |
| Additional mutable scheduler state | 0 B | 8 B |

Two new unsigned words store the Shot tie-break index and Explosion next-start
tick; no new heap allocation or PCM copies. RESTARTING uses the existing state
field. Resource figures are layout/payload accounting, not emulator telemetry.

## Validation and manual review

Passed: deterministic actual C transport/game simulation tests; successful spawn
versus Shot attack equality (including exhausted projectile pool); 2/3/2/3
rotation; isolated control-local stops; Note Off/Note On rejection retries;
100/105/110 and 100/106 scheduling; overlapping tails; occupied pool retention;
fixed eight-event overflow/drop-newest behavior; clock wrap; 600-tick dense
both-Flame/both-Shot/Explosion stress; all prior camera, gameplay, loader,
readiness and split-Flame regressions. Full `make test`, `make check` and the
pinned native Level 2 build are run for delivery. Existing SDK/other-source
compiler warnings remain; the SFX scheduler introduces no compiler warnings.

Native command: `bash tools/build-level2-wingsuit.sh --native` with
`MF_PRESERVE_AUDIO=1`. This environment uses a Debian genisoimage package
extracted into scratch storage and added to PATH; SDK/compiler pins and the
workflow remain unchanged. Matching BIN/CUE and BUILD-INFO identify the delivery.

No GitHub Actions run is triggered. For a later manual run: use workflow from
**main**, **Profile stage-default**, **Source ref the exact delivery SHA**.
This delegates to the Level 2 wrapper and enables the existing X dev skip.

WebRetro audible validation is still required: rapid shots from both players,
three simultaneous deaths, sustained chains and queue pressure, two independent
Flames through handoff/release/pause/death, no clipped/truncated Explosion tails,
and camera/Level 1/Stage Clear/dev-skip smoke checks. Listen for a fresh Shot
transient per spawned bullet, spaced Explosion attacks and undisturbed Flame.
These structural/host/native results do not approve the audible mix or establish
hardware playback behavior.
