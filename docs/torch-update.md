Current control refinement: charging uses normal D-pad speed, diagonals and
facing changes, independently of idle/walk/punch animation. At tick 60 firing
starts immediately in the current direction (no extra equip delay). Active fire
retains its slower, facing-locked strafe. Release before tick 60 cancels the hold.
Host tests cover stationary, moving, turning and independently staggered co-op
charges; emulator/hardware playtesting remains outstanding.

# Charged repair torch and smaller Chuck nose

Baseline: 64704ecf5b4a997bf5e8e868529abfce30f2c417.

## Controls and safety

P1 Buck / P2 Chuck: a quick A press still punches. Hold that same press
continuously for 60 input ticks (1 second at the existing 60 Hz clock) to fire
the repair torch. The initial punch finishes normally; holding never repeats
punches. A small warm cue pulses during the final 20 charge ticks. The threshold enters firing directly in the current facing direction. Hold A to keep firing; release immediately stops
flame/damage/hiss and plays a brief put-away pose. A fresh A or jump can cancel
put-away immediately; fresh bat gestures also work from the release frame. Charge never accumulates across
separate taps.

Both players have independent charge, tool state and damage cadence. While
firing, slow strafe movement is allowed at 140 versus normal 390
fixed-point units/tick. Aim stays in the existing facing direction; move backward
or in street depth without turning the lit tool. Punch, jump and bat inputs are
blocked until release. Ground-only: jumping cancels charging. Recognized ground
or aerial bat inputs take priority, disarm charging and require release/new A
before charging again. Existing bat gestures and ordinary jump kicks remain.

Actual damage, defeat, jumping, pause and controller disconnect clear the tool
and charge. Holding A across interruption, reconnect, unpause or respawn cannot
start another charge until release/new press. Connection state is explicitly
passed from the existing physical-port input adapter into the simulation;
physical port mapping remains slots 0/6. Disconnect drops pending edges without
despawning Chuck. P2 Start joining, P1 pause ownership and debug toggle are kept.
Input charge advances on fixed input ticks, including restrained melee hit-stop;
world damage runs on simulation ticks and never once per rendered callback.

## Art and resources

Chuck's nose is now one pixel shorter than his previous version, with a tip at
local face x+7 versus Buck's x+9. His rectangular frames, brow/jaw, brown mullet,
black sleeveless denim and exposed arms remain. The shared face function applies
to all normal, bat, air-bat and torch poses. Buck's existing non-torch full-frame
pixel hashes match the baseline; his face is unchanged.

Three original poses per costume show equip, supported aiming/firing and put-away.
The compact tool has a metal angled nozzle, grip/trigger and small green fuel
cylinder. Both hands follow their own elbow/wrist chains. Four shared flame
textures connect nozzle (x+34, source y52) diagonally downward to floor
(x+74, source y92). Facing left mirrors both tool and flame around the same
anchor. Down means vertical height toward the floor, never a different street
lane. A pale core, yellow/orange body and red tips flicker over a muted floor
glow. Floor embers are capped at three baked clusters per flame. Burning enemies
use a short warm alternative palette and at most two small ember sprites each.
No unbounded particle allocation occurs.

The torch contact sheet is assembled from actual exported upper/lower/tool/flame
textures. Both costumes, both directions, three poses and all four flame frames
are included. It is an art/data composite, not an emulator screenshot.

To make room without reducing art scale, existing normal player frames now use
shared lower-body textures beneath source y60. Full-frame pixel hashes and both
mirrored assemblies verify exact reconstruction. Distinct Chuck/Buck clothing
pixels are preserved where they cross that cut. Existing bat/air-bat assembly is
unchanged. Slow torch walking reuses the existing stepping lower bodies beneath
the aiming upper body. Texture use including HUD is 444216/458488 bytes: 98 TGA
textures plus two runtime HUD textures. Five indexed asset palettes plus one
runtime warm enemy palette fit with the font in eight CRAM banks.

## Combat

The flame is a sloping region from x34/z40 to x74/z0 relative to the fighter,
with a small width allowance. Horizontal reach, ground-depth overlap and the
sloped vertical interval must all intersect the target hurtbox. Screen overlap
with a different street lane cannot cause damage. Grounded fire cannot hit a
high hurtbox above its actual flame. No player hurtboxes are tested: no friendly
fire or self damage.

Each firing player deals 1 direct damage to each overlapping target every 12
simulation ticks (0.2s), starting on first firing tick. This is 5 direct HP/s,
versus approximately 2.5 HP/s from repeated 24-tick punches before hit-stop.
Contact refreshes one 48-tick burn duration per enemy, never adds timers. A
separate 30-tick cadence deals 1 burn damage, continuing briefly after release;
refreshing contact does not reset/duplicate the cadence. A six-HP enemy held in
one flame falls in about 0.8s after firing starts (plus the initial charge/equip).

Fire flashes do not set the enemy HURT state or extend hit-stun. Enemies remain
able to walk/attack and interrupt a torch. Damage timers are per firing player;
burn state is per enemy. Both players can hit the same enemy, but the first
zero-HP transition alone starts existing defeat/removal/respawn and awards score.
Barrels take direct timed fire damage and retain normal score, break and respawn
rules. Fire never adds repeated melee hit-stop. Break/death impacts use existing
quiet SFX; ordinary burn ticks do not flood the impact sound port.

## Native sound

Music sequence, instrument bank, gain and priority are unchanged. The existing
FX bank gains original generated ignition and hiss PCM voices. Existing global
SFX scale remains 0.6375*0.9=0.57375; ignition is additionally x0.45, hiss x0.20
at source. The initial three SFX programs/samples retain their tuning/gain.
Ignition shares the existing punch control port and can preempt it; simultaneous
ignitions coalesce. Hiss uses one shared native SEQ/PCM-loop port (4), regardless
of one or two firing players, preventing doubled loop loudness. Native SEQ has
finite 250ms gates/releases at its loop boundary; RR remains 31. No new driver,
SH-2 audio mixer or song recording is used.

Hiss desired state is the OR of actual live firing states, including during
melee hit-stop. Release, damage, death, pause or disconnect removes that player's
request. When neither remains, StopSeq is retried until accepted, even while
paused. The hiss port is stopped, never paused/resumed into a stale flame. An
interrupted equip does not start the loop. Native music retains its previous
pause/resume retry handling and continues during hit-stop.

The expanded FX bank fits by regenerating aligned, non-overlapping sequence/tone
addresses in CUSTOM.MAP and the runtime header; boot/driver/work/DSP reservations
stay fixed. Total reserved/payload sound RAM is 296256/524288 bytes, high water
296416. The conservative slot bound is 22 music+release slots, 4 live SFX slots
and 5 retiring slots (including ignition preemption) =31/32. The build rejects a
future song/bank that exceeds the physical bound. PCM and sequence levels are
data-validated; final hardware summation/loudness and loop seam need listening.

## Validation and remaining playtests

Host tests cover the exact charge threshold, quick taps/one initial punch,
release/re-press, independent players, slow facing-locked walking, jump/bat
suppression during fire, bat priority, damage/jump/defeat/pause/disconnect clears,
stale respawn/unpause/reconnect holds, 0.2s damage, diagonal vertical/depth misses,
finite non-stacking burn, no permanent hit-stun, barrel respawn, shared enemy
kills and exactly-once score. Existing ground/air bat, jump, co-op and actual
pinned SDK poll-body/join regression tests still run. Native command mocks cover
one shared hiss, stop retries, release/pause/reset and no stale resume. Sanitizers
exercise torch and co-op paths.

Native compilation and ISO checks validate every embedded payload, source
fingerprint, normal/bat/torch assemblies and mirrors, flame-core connectivity,
palettes, memory budgets, sound-bank pointers, loop gates and MIDI/SEQ equivalence.
No configured Saturn emulator/BIOS setup or physical hardware test is available
here. No audio audition, two-controller emulator playtest or hardware verification
was performed. Torch aiming/movement feel, flame/flash readability, final mix,
loop seam and Saturn performance still need those playtests. BIN/CUE packaging
and pinned toolchain remain unchanged.
