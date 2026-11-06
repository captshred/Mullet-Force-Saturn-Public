# Level 2 drone dispersal and rooftop turrets

Approved parent: `812ecb6a8a22bc0de8ab698e6da4e8158a4d803e`.
Branch: `feature/level2-drone-spread-rooftop-turrets`.

## Drone dispersal

All five families remain: diagonal, staggered descent, crossing, curved
approach and lateral sweep. Three members still enter 14 ticks apart; formation
selection, LCG consumption, pacing, age-80 aimed shots, collision extents,
24×24 drone sprites and one-hit combat remain unchanged.

Initial adjacent separation rises from 16px to 32–36px for the corner/diagonal
families, and from 24px to 56px for staggered descent. Crossing uses different
start positions even for the two members entering from the same side. An
additional lane-relative +/-24px expansion settles over 56 ticks with an integer
smoothstep. Faster diagonal/sweep easing and faster corner curvature widen the
formation naturally without random jitter. The center member holds its lane;
only the outer members fan outward. Heading and lane index fit in the existing
`direction` integer, so aerial enemy structs do not grow.

At equal local age 56, all families span at least 90px (the parent's same-age
spans were 32/48/72/32/32px). Movement tests bound each step to 4px and centers to
the original stage limits. A separate actual staggered-entry trajectory check
measured bounding-box overlaps of 0/0/16/0/17 ticks for diagonal/staggered/
crossing/curved/lateral patterns. Crossing naturally has brief intersections.

Chrome Eye art, path branch, spawn branch, formation spacing, count selection,
RNG and pacing are preserved exactly, with original regressions retained.

## Turret artwork and roof placement

Shared top-down art consists of one 24×24 armored base and eight 16×16 directional
gun assemblies. Forest/olive green armor, a dark mechanical outline/base,
metallic bolts and a silver-gray barrel distinguish the emplacement from aerial
enemies. Directional frames are aim poses, not firing animation. No new audio
or bullet texture. Original integer-grid artwork is reproducible through
`tools/build-rooftop-turret-art.py`; embedded RGB555 data avoids new CD files.

Two fixed map anchors are used, one on each selected raised site:

| Native 512×512 map center | Site | Surface |
|---|---|---|
|308,244|Raised navigation roof / stepped landing works|Open painted maintenance pad|
|343,392|Raised tank mill / staggered perimeter|Solid open patch between the hatch and large tank|

Two of the six main city sites carry turrets. No placement is randomized. The
placement validator reconstructs native `WROOF.BIN`/`WRMAP.BIN`, verifies every
opaque base pixel lies inside exactly one authored roof footprint, and checks
it against machinery body masks. Flat painted markings are valid surfaces;
existing roof/equipment shadows remain unmodified beneath the sprite. All city
payloads and palette bytes remain identical to the approved parent.

## Anchoring and lifecycle

The stage repeats every 512 native rows; it is not a finite level map. A turret's
screen Y is `(map_y + scroll) & 511`, matching the renderer's `(screen_y-scroll)`
map sampling. Raised-roof X uses exactly the approved 16.16 transform
`96*65536 + (camera_x-48*256)*288`, including the 9/8 horizontal rate and fractional
camera positions. The result is converted into existing aerial world space for
shared weapon/projectile collision and projection. No independent drift or
camera-relative spawn position is introduced.

Each anchor owns one permanent ground slot. Camera culling neither respawns it
nor restores HP. When that map point wraps from row 511 to row 0, the next physical
roof instance restores 4 HP and a fresh activation timer. Destruction remains
latched until that wrap. Offscreen turrets stop aiming/firing, occupied slots
are never duplicated, and all bullets have normal TTL/four-edge expiry. Stage
initialization/restart clears the pools; pause freezes simulation.

## Combat and balance

Turrets have 4 HP. Ordinary hits and existing six-tick flame pulses each remove
one HP; one consumed shot cannot also hit an aerial enemy and a turret.
Destruction gives the existing 100-point award,12-tick explosion and one existing
death event. Destroyed turrets do not fire again for that roof instance. Bullets
already in flight retain their normal expiry.

A fully visible turret waits 45 gameplay ticks, then attempts one shot every 40
ticks. Aim updates every 8 ticks and again at firing. It selects the nearest
living, active, non-respawning hero by pixel distance, with Buck winning ties.
The eight-direction gun pose follows that target. Bullet velocity is normalized
once per aim update at 2.5px/tick; emitted bullets keep their velocity and never
home. No valid target means no bullet. Re-entering from horizontal culling gives
another activation delay without restoring HP.

Four separate turret bullet slots are shared between the two emplacements.
Pool exhaustion drops the scheduled shot and retains the 40-tick cadence. Drone
bullets keep their original 16 slots and 3px/tick speed. Chrome Eye chains retain
all eight aerial slots, including while both ground turrets are active.

## Resource accounting

| Resource | Approved Chrome Eye | This pass |
|---|---:|---:|
|Aerial / ground slots|8 /0|8 /2|
|Player / drone / turret bullets|32 /16 /0|32 /16 /4|
|Mutable `mf_wingsuit` state|1,672 bytes|1,880 bytes (+208)|
|VDP1 texture bytes|28,544|33,792 (+5,248)|
|VDP1 definitions|19|28 (existing ID0–18 unchanged)|
|Maximum sprite submissions + user clip|72+1|80+1 =81|
|VDP2 payload / reservation|65,792 /434,176|unchanged|
|VDP2 unreserved headroom|90,112|unchanged|
|CRAM payload|32 bytes|unchanged|
|SCSP high-water / free|307,260 /217,028|unchanged|
|Level 2 CD files / payload|26 /252,292|unchanged|

The 208-byte state increase is two 48-byte turret records plus four 28-byte bullet
records. The sprite-ID array grows by 36 CPU bytes. Shared read-only data adds
5,248 sprite bytes, a 24-byte anchor table and 32 bytes of gun pointers on SH-2,
plus generated code. Sprite definitions/picture tables remain capped at 255;
SGL's 1,761-command capacity and existing VDP1 texture arena are unchanged.
33,792 texture bytes leave 424,696 bytes of the 458,488-byte texture arena.

Base ID19 is 24×24; gun IDs 20–27 are 16×16. Explicit sort depths put base at 102,
gun at 101, aerial sprites at the original 100, and the user clip at 103. This
avoids relying on equal-depth insertion order, keeps the gun over its base and
aerial actors above the emplacement, and retains the same clipping rectangle
X48–271/Y0–239. All depths remain inside the existing SGL window. The full-pool
renderer test submits every aerial, gun/base, bullet, both heroes and both
maximum-length beams simultaneously:80 sprite commands plus one clip.

No SDK/compiler changes, path history, floating-point runtime math, per-frame
asset I/O, new heap allocation, VDP2/CRAM/SCSP reservation, music or sound changes.

## Validation and review

`level2-turret-lock.json` is an additive exact scope from the approved Chrome Eye
commit; all previous preservation lock files remain unchanged. It freezes all
runtime asset blobs, Level 1, audio, Chrome Eye art, HUD/transitions, workflow,
camera constants and camera/parallax source sections. Exact authorized updates
are resolved through the existing preservation chain without replacing prior
baselines.

The dedicated UBSan regression covers all 24,577 fixed-point camera samples,
all 512 native rows, five expanded drone families, nearest valid targets,
activation delay and 40-tick firing, bounded pool exhaustion, fixed bullet
trajectories, four-hit/beam destruction, permanent disable per instance,
camera/cycle handling, player damage, pause/restart and 50,000 deterministic coop simulation ticks. Existing camera/coop,30,000-tick eye and 100,000-tick aerial
stress tests remain active. Older isolated movement/audio fixtures receive
extended invulnerability so new background fire does not invalidate their
specific movement/transport assertions; their intentional damage tests remain.

Reproduce:

```
bash tools/setup.sh
bash tools/build-stage.sh --native
make check
make test
python3 tools/validate-rooftop-turrets.py
python3 tools/validate-wingsuit.py --disc
python3 tools/check-preserved-audio.py
python3 tools/preview-rooftop-turrets.py
python3 tools/preview-level2-enemies.py
```

On this rootless Debian host, `tools/setup-cloud.sh` provides genisoimage under
`/workspace/mf-host-tools`; prefix native build/check with
`PATH=/workspace/mf-host-tools/usr/bin:$PATH`.

Host review artifacts are `build/turret-review/rooftop-turrets.gif`,
`rooftop-turret-sequence.png`, `rooftop-anchor-map.png`,
`turret-sprite-sheet.png`, and `build/enemy-review/drone-paths.png`. These use
actual C simulation output and native city/sprite pixels. They demonstrate
anchoring, camera movement, aiming, fixed bullets and wider drone paths, but are
host composites rather than emulator captures. No emulator/hardware visual or
frame-rate validation was performed; command/memory/UBSan tests do not establish
actual Saturn frame timing.

Final automated results: native stage build passed and produced matching
`build/mullet-force.bin` / `build/mullet-force.cue`; `make check` passed;
`make test` passed with 247 PASS reports. Explicit turret/approved-parent,
Chrome Eye/night preservation, disc and preserved-audio checks passed.
`git diff --check` passed. Native compilation retains the parent's existing
`jo_print` const-qualifier warning; unrelated HUD/SDK code remains unchanged.

## Manual Actions settings

Open **Actions → Manual Saturn playtest build → Run workflow**, use the workflow
from `main`, choose profile **stage-default**, and set **source_ref** to
`feature/level2-drone-spread-rooftop-turrets` or the delivered full SHA. Download
the playable artifact and keep BIN/CUE together. The existing development X skip
and real Level 1 Stage Clear handoff remain. No Actions run is dispatched by this
pass; the workflow itself stays unchanged.
