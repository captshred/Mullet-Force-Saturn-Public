# Phase 1 · MF-88 downhill ambush

The car triggers once per game when a living player reaches world X 2,240.
The camera holds its current position while the normal player controls,
combat and spawning continue. The encounter runs for eight seconds of
60 Hz simulation time, with a 90-tick warning, a 125-tick downhill pass,
a 120-tick recovery and a 145-tick uphill return. The camera resumes as
the return exits. The Stage 2 handoff clears the encounter pose, and a
fresh game rearms it.

Contact takes 20 HP through the existing hurt path. The collision band is
centered on lane Y 198 and covers ±12 pixels of depth. A jump at least
24 pixels high clears it. Each hero has a separate hit latch per pass
and keeps their usual invulnerability. The warning displays CAR INCOMING
and uses the existing swoosh through the world SFX control. This is a
placeholder cue for a dedicated engine-rev recording.

The supplied transparent 192 × 80 indexed PNG was mapped to the existing
street palette, excluding its animated indices. The zero-key mask is
identical to the PNG's alpha mask. One 15,360-byte indexed texture is
shared by both directions. The VDP1 loader audit reports 178 definitions
and 386,432 bytes, leaving 72,056 bytes free, including the protected
49,152-byte reserve. There is no additional CRAM allocation or SCSP
sample data.

The native profile is `stage-default`. Build with
`bash tools/build-stage.sh --native`, then run `make check` and
`make test`. In GitHub Actions select `stage-default` and supply the
implementation commit as `source_ref`.
