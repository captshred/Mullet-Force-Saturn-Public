# Phase 2 · MF-88 downhill ambush

The car triggers once per game when a living player reaches world X 2,240.
The camera holds its current position while the normal player controls,
combat and spawning continue. The three passes run downhill in near lane 216, uphill in far lane 180,
and downhill in center lane 198. The initial warning lasts 90 ticks.
Each 120-tick gap includes a lane-specific warning in its final
48 ticks. The camera resumes after the third pass exits.
The Stage 2 handoff clears the encounter pose, and a
fresh game rearms it.

Contact takes 50 HP through the existing hurt path and knocks out enemies in one hit. Environmental KOs do not award player score or advance the spawn progression. The collision band is
centered on the current lane and covers ±12 pixels of depth. A jump at least
24 pixels high clears it. Each hero has a separate hit latch per pass
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
