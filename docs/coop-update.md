> Historical co-op/audio update. Physical port mapping and title-screen joining
> are corrected by [the input/bat update](bat-input-update.md).

# Buck + Chuck co-op update

Baseline: 999cef8bca349aeec02d4f24b90ca0ac83b03f9b.

## Controls and actors

Port 1 Buck: D-pad ground movement, A punch, B jump, airborne A kick,
Start starts/pauses/resumes, C debug (off initially).
Port 2 Chuck: Start joins an existing game, D-pad/A/B same moves and stats.
P2 Start never changes pause; P1 owns pause. No second pad is required.
There is no friendly fire or physical player blocking. The camera follows the
living pair's midpoint, with a 260px shared-screen tether; when one is down,
it follows the survivor. Each player independently auto-recovers after 120
simulation ticks, with 120 ticks of protection. Recovery changes neither the
other player nor the enemies, barrels or score. Global hit-stop adds a few ticks.

Chuck uses 15 original native-resolution costume variants of every selected
Buck pose, including the existing hurt/defeat selections (coil and crouch).
Exposed articulated arms replace sleeves; black denim has pockets, seams,
frayed cut-off edges, and a short hem. Brown mullet, sunglasses, dark pants
and boots share Buck's adult anatomy and 88px idle scale. Cropped texture
anchors are generated from authored 72/112x96 canvases, without scaling or
losing opaque pixels. Flipping mirrors the cropped anchor too. All three
actors have a single palette each; the second enemy shares existing textures.
Contact sheets are decoded from the actual exported TGAs, not emulator captures.

Two suit enemies maintain separate AI, HP, target, target lock, timers,
per-player hit masks and death/respawn state. Target selection favors a nearby
living player, with a mild distribution preference and a 120-tick lock; targets
are not switched during attacks. A second attacker waits if its shared target
is already being telegraphed/attacked, and recovery durations are staggered.
Player invulnerability is 60 ticks against all enemies, preventing damage every
frame or chained simultaneous hits. Windup remains 24 ticks, active 6 ticks.
Each player swing can hit each enemy once; each enemy swing can hit each
player once. Depth, height, range and facing checks apply; no player-player
attack checks exist. Each enemy awards 250 once, disappears after its defeat
animation, and independently respawns after 480 ticks at the endpoint furthest
from the living players with at least 120 ticks of grace. Stable sprite sort
uses ground position, never jump height.

## Audio path and actual change

The previous PCM music peaks were already near full scale (up to 30476/32767),
so simply doubling the bank would clip. Global SCSP master was already 15,
maximum; direct slot output DISDL was already 7, maximum; DSP sends were off.
Music sequence volume is 82, versus SFX 112, and TON instruments added TL
attenuation: rhythm 20, lead 18, bass 14 (nominal 7.5/6.75/5.25 dB).
SFX TL was zero. Source note velocities are uniformly 76/127; source has no
CC7 volume or CC11 expression events. Normalization initializes channel volumes
100 (rhythm), 108 (lead), 112 (bass), and expression 127. The binary driver
applies its own sequence/channel/velocity attenuation; its exact transfer curve
has not been measured. Sample scaling alone was not the entire gain path.

Central settings remain assets/music/config.json. Keep the preceding music PCM
scale 1.5*0.9=1.35 and sequence volume 82; reduce instrument TL by up to 16
steps (0.375 dB each). Rhythm TL20->4 and lead TL18->2 produce +6 dB.
Bass TL14->0 adds 5.25 dB, plus a safe +0.75 dB PCM multiplier (1.09018449)
for +6 dB total. Every melodic instrument used by this song therefore gets
+6 dB relative to the baseline, without altering velocities, envelopes, timing,
pan or expression. Bass sample peak remains below 32768. The unused starter
kit also gets +6 dB where safe; kick receives +4.5 dB because an additional
PCM boost would overflow. This smaller kick boost is explicit in the report.
No sample saturation or silent maximum-volume clamp is used. Sequence/master
controls remain unchanged. This does not establish that the final hardware
summation is clipping-free: listening/output measurement is still required.

SFX PCM scale changes from 0.75*0.9=0.675 to 0.6375*0.9=0.57375: exactly
0.85 of the latest build before integer rounding (-1.41 dB). All player,
enemy and barrel SFX share this scale; no role-specific bypass exists.
Music/SFX ratio thus improves by about 7.41 dB. Music priority changes 8->31,
SFX 31->8, protecting music from effects if hardware voice pressure occurs.
Three fixed SFX ports are retained; simultaneous same-type events from all
actors coalesce rather than stacking. Punch/jump/impact retriggers are limited
to 6/8/8 simulation ticks respectively, never adding more effect ports.
Pause freezes music and SFX through the existing retryable native commands;
hit-stop freezes gameplay only, leaving the native music clock running.

Source MIDI still has ZERO note-on/off events on human channel 10/raw 9,
across all six tracks; no drums were restored or invented. Existing explicit
kick/snare/hat/cymbal note mapping and fixed-tuning routing are preserved.
The 5120-note, 1206-bend SEQ remains unchanged. A percussion overlap fixture
checks independent kick/snare/hat routes, velocities, gates and root tuning.

## Validation and limits

Host tests cover legacy gameplay, both simultaneous controller streams,
independent health/actions/recovery, friendly-fire absence, player crossing,
shared enemy damage masks, target lock/reselection, staggered attacks,
independent deaths/score/respawns and long simultaneous combat. Transport mocks
check shared SFX bounds/rate limits and pause/retry behavior. These do not
simulate the SCSP's audio waveform or a two-controller emulator.

Native compilation and ISO validation check every exported payload, source
fingerprint, lossless anchor restoration, palette consistency, tone pointers,
SEQ event equivalence, and memory regions. Textures including HUD total
401856/458488 bytes; a second enemy allocates no additional texture. Sound RAM
reservations and data remain 283748/524288 bytes, high water 296020. Conservative
music+release bound is 22 slots, plus 3 SFX and 3 retiring tails =28/32, leaving
four physical slots; normal music allocation budget remains 24. Actor count
does not multiply SFX ports or sound bank memory.

No emulator audio audition, two-controller playtest or physical Saturn test
has been performed. Final mix clipping, hardware voice behavior and controls
still require those tests. BIN/CUE uses the unchanged working disc toolchain.
