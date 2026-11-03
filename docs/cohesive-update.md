# Cohesive combat, art and mix update

## Percussion diagnosis

The actual unchanged `assets/music/drop-zone.mid` was inspected across **all six
tracks and all raw channels**, using MIDI status bytes rather than track names.
Standard percussion channel 10 is raw/zero-based channel 9.

| Track | Raw channel(s) | Percussion note-ons | Percussion note-offs |
|---|---|---:|---:|
| 0, conductor | none | 0 | 0 |
| 1 | 0 | 0 | 0 |
| 2 | 2 | 0 | 0 |
| 3 | 4 | 0 | 0 |
| 4 | 6 | 0 | 0 |
| 5 | 8 | 0 | 0 |

**Percussion note numbers/counts found: `{}` — zero events.** Human channel 9
(raw 8) is a melodic overdriven-guitar part, not channel-10 percussion. No SysEx
reassigns a percussion channel. The playable SEQ still matches all 5,120 source
notes, their gates and velocities, and all 1,206 rounded pitch bends; its bytes
are unchanged. Conversion has not dropped a source drum part. No replacement
percussion part was invented or described as restored.

`assets/music/drum-diagnosis.json` records the raw-channel trace. The existing
kick/snare/closed-hat/open-hat/cymbal sample bank remains available. Source notes
would map to separately selected fixed-root (60) PCM drum sounds, not a melodic
program transposed by the GM drum key. A fixture checks simultaneous kick, snare
and hi-hat with independent note releases, timing and velocity. This file calls
for no additional drum/tom samples because it contains no percussion.

The conservative music/release budget remains 22 SCSP voices, under the 24-voice
music limit. Three fixed SFX ports plus three interrupted-release guards total
28/32 voices. Enemy sounds reuse these ports, so they do not increase that bound.
There is no budget evidence of music voice stealing; actual voice allocation
and playback have not been measured on hardware.

## Exact gain changes

All settings live in `assets/music/config.json`. Native driver sequence levels
remain 82 (music) and 112 (SFX); those controls are not assumed to be linear gains.
Instead, the TON PCM sample payloads receive these exact multipliers:

| Class | Requested multiplier | Shared headroom | Final multiplier vs previous build |
|---|---:|---:|---:|
| Music, including available drums | 1.50 | 0.90 | 1.35 |
| Every gameplay SFX | 0.75 | 0.90 | 0.675 |

Music-to-SFX relative balance changes by **2x**. The common 10% headroom prevents
sample saturation: the original music peak 22,575 would become 33,862.5 without
it; final music peak is 30,476 and SFX peak 13,063. No hard clipping or silent
clamping occurs. Integer PCM rounding error is at most half a sample unit.
Direct comparison with the preceding committed banks confirmed the exact final
multipliers while all tone headers, tuning and payload lengths stayed identical.

Punches, jump, barrel hits/breaks, enemy attacks, fighter impacts and enemy defeat
use the same scaled SFX bank. No role has an independent volume override.
Sample validation does not prove the summed hardware mix is free of clipping;
that still requires a listening/output test with concurrent music and effects.

## Art, enemy and combat

Buck retains his 88px standing scale, outfit, mullet and sunglasses. A shared
native face construction supplies brow, nose bridge/tip, cheek, mouth and
jaw/neck shadows in every exported animation and its horizontal flip.

The new original businessman has 12 frames: idle/guard, four walks, windup,
punch, recovery, hit, falling and defeated. A dark suit, pale shirt, red tie,
dress shoes and narrow bright green mohawk distinguish him from Buck.
There is exactly one enemy state object. He approaches both ground axes and
locks his facing for a 24-tick telegraph, six-tick attack and 36-tick recovery.
Both fighters have explicit horizontal/depth/height attack and hurt boxes.
A swing can damage a target once. Punches deal one enemy HP; jump kicks two.
He has six HP, recoils, and awards 250 score exactly once on defeat.

His 30-tick defeat animation is followed by removal and an eight-second absent
period. Respawn chooses the far level endpoint offscreen, with 120 ticks of
attack grace. These values are editable in `src/combat_config.h`.
Buck takes 12 damage per punch, has 60 ticks of invulnerability and brief recoil,
and automatically recovers after two seconds if defeated. Score and barrels
persist; the enemy resets far away with grace so recovery is safe.

A successful melee hit applies a three-tick gameplay-only hit-stop, sparks and
impact SFX. The 68000 music sequencer keeps running; only Start pause sends
native pause/continue commands. Input edges are buffered during hit-stop.
Actors sort by **ground** depth with stable ties, including while Buck jumps.
The matching dither-edged ground shadows remain at landing positions.

The arcade windows now contain low-contrast cabinets; the vinyl shop contains
record sleeves/discs and racks. Layout and controls are preserved. To fit the
enemy animation, street sections now use a shared indexed palette with exact
color mapping and no quantization. Three palette groups are used: street, Buck,
enemy. Total VDP1 texture/HUD allocation is **393,600/458,488 bytes**.
Updated HP indicators and attack telegraph are normal HUD; C toggles diagnostics.

## Validation and limits

- Nine original gameplay regression groups still pass with the new opponent
  isolated in those legacy fixtures; eight dedicated combat groups exercise AI,
  telegraph/contact/recovery, hit-once rules, hurtboxes, range/facing/depth/height,
  jump kicks, knockback, invulnerability, hit-stop, score, respawn and recovery.
- Nine music/converter tests include percussion overlap, exact linear gain and
  clipping rejection. The native transport mock covers partial pause retries
  and three simultaneous fixed SFX ports.
- Independent ISO/data checks cover all 37 TGA files, native music, source hashes,
  palette/anchor consistency and sound/texture/work-RAM budgets.
- `fighters-contact-sheet.png` and per-fighter sheets decode the actual exported
  TGA frames. The scene illustration is an art composite, not an emulator capture.

Actual emulator audio/play testing and Saturn/SAROO hardware testing have not
been performed in this update. Test audible mix/clipping, camera-edge combat,
airborne sorting, pause during impacts, repeated enemy defeat/respawn and Buck
recovery on the target system before claiming those results.
