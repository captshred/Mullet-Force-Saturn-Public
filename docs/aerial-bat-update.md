> Historical aerial-bat update. [The current torch update](torch-update.md) adds
> charging/fire and further reduces Chuck's nose while preserving the bat arc.

# Chuck face, corrected swing, aerial bat

Baseline: f8f5ff91b2de8ef7c6d988d985f81d1e885445e7.

## Art

Chuck now has rectangular framed dark sunglasses, a heavier straight brow,
slightly blunter nose and squarer jaw/chin. The same conditional face construction
is used by every idle, walk, punch, jump, kick, hurt/defeat selection and bat pose.
His brown mullet, exposed arms, black denim and native head/body scale remain.
Buck's 15 non-bat source pixel hashes match the baseline exactly, including his
face and round shades; the shared drawing code leaves his face unchanged.

The seven bat poses are in playback order, with anticipation and recovery
retained: low draw, low coil, outward rising acceleration, forward contact,
upward sweep, high follow-through, and stow/recovery. This redraw is not the old
animation played in reverse. In right-facing screen coordinates (y points down),
the grip-to-barrel-tip vectors turn counterclockwise from low left through low
right, forward, high right and high left. Mirroring naturally gives a clockwise
left-facing screen rotation. Both hands derive from the same wrapped-handle
axis and elbows/torso follow the new geometry. Active trails now trail beneath
the rising strike. Muted trail pixels occur only in the three active poses.

Aerial poses use compact bent-knee chains for wind-up, staggered knees for
contact, and shifted bent legs for follow-through, shared below the belt between
costumes. The corrected upper-body/weapon arc is shared with the ground move;
the complete airborne silhouettes are distinct. Assets remain native pixel art
with no enlargement. The actual exported layers are reconstructed into the
updated bat-contact-sheet.png, showing ground and air, Buck and Chuck, and both
facing directions. Each row runs left-to-right in playback order (0..6).
Generated metadata includes complete assembled pixel hashes, anchors and arc
geometry. Validation also checks actual wood pixels around the declared tips.

## Controls and state

Existing controls remain: D-pad moves, A punches, B jumps, airborne A without a
bat gesture jump-kicks. P1 Start owns pause; physical P2 Start joins Chuck from
title or gameplay. Port mapping (SDK slots 0/6), polling, join safeguards and
raw diagnostics (P1 C, hidden initially) are preserved without changes.

Ground or air: two distinct taps in the character's current facing direction,
with a release between them, then A; second tap+A together works. The existing
250ms between taps and approximately 183ms for A apply in both states, configured
in src/combat_config.h. Facing changes/opposite taps cannot combine. Gesture
history is independent for each player. Actual takeoff clears all pre-jump
history, including forward+B, so two fresh airborne forward taps are required.
Combo recognition precedes ordinary kick selection. Each player can use at most
one aerial bat per jump; a new actual takeoff re-arms it. Ordinary kicks remain
available when no valid bat gesture exists, including after the bat has been used.

The air move retains normal gravity, jump velocity, horizontal/depth steering,
world bounds, shadow at ground position, shared camera and ground-based actor
sorting. No hover or jump-height lock is introduced. Existing three-tick impact
hit-stop still briefly holds gameplay when a hit connects; music keeps running.

On landing during an aerial bat, height/velocity become zero normally and the
move enters its final nine-tick, non-damaging recovery (attack tick 28 onward).
It changes to planted legs, does not reset the target mask, replay active frames
or reissue the swing sound. Landing outside a bat follows existing kick/jump
rules. New ground actions work after recovery. Damage/reach/knockback remain
2/78/1350 versus punch 1/52/850. Ground recovery and bat duration remain unchanged.

## Combat synchronization

Damage remains attack ticks 12..17, corresponding to acceleration/contact/lift
poses 2..4. Swing SFX is issued once at first active tick; both players' same-type
SFX coalesce through the existing quieter rate-limited ports. The y/depth/facing
and one-hit-per-target rules remain. Multiple enemies/barrels may be hit by the
same swing, with no player-player damage or repeated defeat scoring.

The rising bat's local vertical hit intervals are 14..58 during acceleration,
40..64 at forward contact and 54..90 during lift. Airborne height translates
these intervals instead of granting a ground-height attack. Thus a bat near
head height can hit a standing enemy, but a genuinely high swing misses. Depth
alignment is still based on ground y, not jump height. Sparks use the midpoint
of the actual attack/target vertical overlap for bat hits, including head hits.

## Verification and limits

Host tests cover both characters and facing directions, ground and aerial timing
boundaries, fresh-takeoff history, held/opposite direction rejection, bat priority,
normal punch/kick fallback, all seven bat frames, exact jump-physics equivalence
with and without a bat, both-axis air steering, one aerial bat per jump/re-arming,
active-only damage, vertical/depth/facing misses, landing before/within a strike,
retained masks/non-damaging landing recovery, simultaneous two-player air bats,
coalesced sound events, no friendly fire and exactly-once score. Legacy gameplay,
co-op, actual pinned SDK poll-body fixture, converter and native transport tests
remain in the suite. Sanitizers check aerial combat and co-op state paths.

Native compilation and ISO validation check exact payloads/source fingerprints,
normal and bat anchors, lossless mirrored ground/air assemblies, bat direction,
unclipped actor/weapon bounds, texture budget and work-RAM separation. VDP1
textures including HUD total 456456/458488 bytes (70 TGA + two runtime HUD
textures), with four shared CRAM palettes. Three new lower-body textures are
shared by both characters; no extra upper-body bank or palette is allocated.
Music/SFX assets, balance and native transport are unchanged. Sound RAM remains
283748/524288 reserved/payload bytes, with the existing conservative 28/32 slot
bound including music releases, SFX and retiring tails.

No configured Saturn emulator/BIOS test setup is available here. No actual
emulator animation/input/audio audition, two-controller playtest or physical
Saturn test was performed. Those tests are still needed for game feel, visible
animation timing, hardware performance and final audio playback. This build uses
the existing toolchain and matching MODE1/2048 BIN/CUE packaging unchanged.
