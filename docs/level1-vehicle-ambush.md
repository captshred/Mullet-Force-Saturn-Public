# Phase 2 · MF-88 downhill ambush

The car triggers once per game when a living player reaches world X 2,240.
The camera holds its current position while the normal player controls,
combat and spawning continue. The three passes run downhill in near lane 214, uphill in far lane 187,
and downhill in center lane 200. The initial warning lasts 90 ticks.
The car covers the same 520-pixel sweep in 109, 126 and 109 ticks
(about 15% faster). Each 120-tick gap includes a lane-specific warning in its final
48 ticks. The camera resumes after the third pass exits.
The Stage 2 handoff clears the encounter pose, and a
fresh game rearms it.

Contact takes 50 HP through the existing hurt path and knocks out enemies in one hit. Environmental KOs do not award player score or advance the spawn progression. The grounded danger bands are Y 194–229 downhill near, 168–202 uphill far,
and 188–212 downhill center, within the playable Y 168–229 road.
The grounded swept footprint extends 64 pixels along X from the car
center. An 8-pixel jump clears the low bumper margins, leaving the
56-pixel body footprint. At 18 pixels of jump height the body is
cleared. Both values use the existing 24.8 height and jump physics. Each hero has a separate hit latch per pass
and keeps their usual invulnerability. The warning displays CAR INCOMING
and uses the existing swoosh through the world SFX control. This is a
placeholder cue for a dedicated engine-rev recording. All three passes play
the exact Level 2 flame-hold PCM loop on an isolated MIDI channel of the world SFX control. A world impact can interrupt the loop.
The loop stops between passes, on pause, and during protected POOWAH
playback.

The supplied transparent 192 × 80 indexed PNG was mapped to the existing
street palette, excluding its animated indices. The zero-key mask is
identical to the PNG's alpha mask. One 15,360-byte indexed texture is
shared by all three passes. The VDP1 loader audit reports 178 definitions
and 386,432 bytes, leaving 72,056 bytes free, including the protected
49,152-byte reserve. The existing CRAM allocation is preserved. The separate Level 1 pass
bank uses 25,764 SCSP bytes and leaves 20,524 bytes free. The approved
Level 1 banks and the original Level 2 banks remain byte-identical.

The native profile is `stage-default`. Build with
`bash tools/build-stage.sh --native`, then run `make check` and
`make test`. In GitHub Actions select `stage-default` and supply the
implementation commit as `source_ref`.

## Upright car and inset lanes

The original horizontal sprite draw is used on all three passes.
The lane insets account for the 1:5 grade under the measured front and
rear tire patches in both directions. Rendering and collision continue
to use the same lane coordinate.
