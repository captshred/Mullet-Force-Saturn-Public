# Canonical development baseline — THE ONE v4

Canonical development tag: **`the-one-v4-source-complete`**.

Canonical development source SHA:
`1e7077616f7da57436500b3d9cddda2e61e6a727`

Owner-approved BIN SHA256:
`e2d89a26aa5a27f8994a5425078e5329ca3818047739312d68a5c21606b2d554`

**Owner WebRetro result: PASS / APPROVED.** The owner tested this exact build
and confirmed Level 2 entry without E108, repaired startup ordering and 0x041a
readiness, approved Fire on every successful tap-A projectile, approved new
non-lethal Hit and surviving-hit routing, lethal-hit Explosion behavior,
five-VBlank Explosion spacing, Music, independent Flame sustain, gameplay,
balanced camera and neon artwork.

This source is complete and clean-checkout reproducible. The preservation tag
must always point to the approved source SHA above, never to a subsequent
documentation commit. Matching BIN/CUE use MODE1/2048. SDK/toolchain remain
Jo Engine `556d081146211b6a1cfa6591d70f9487d406758b` and SH GCC 8.2.0.
Successful Actions run/artifact IDs were not supplied; do not infer them.

## Mandatory development and promotion rules

Future feature branches MUST start from `the-one-v4-source-complete` or exactly
`1e7077616f7da57436500b3d9cddda2e61e6a727`, unless the owner explicitly instructs
otherwise. Preserved executables are validation references only, never
substitutes for missing source.

No future THE ONE may be promoted unless all five conditions hold:

1. All executable-affecting source, assets and configuration are committed.
2. A clean checkout can rebuild the game without private or hidden dependencies.
3. Verification passes.
4. Exact source SHA -> BIN SHA256 provenance is recorded.
5. The owner tests and approves the resulting playable build.

Preserve older THE ONE tags as historical recovery points; never move or replace
them. In particular, `the-one-v3` remains at
`5ca590d774cc91d0ac1bb4ce6b325aa647b3dd59`, and
`the-one-v3-source-complete` remains at
`6596c96d30569bdfc0fdaa0b72e6da4bab0a32e0`.

## Reproduction and artifact provenance

Use x86-64 Linux and the README's host prerequisites, including genisoimage,
GCC, Python/Pillow and documented host libraries. From a clean committed checkout:

```sh
bash tools/verify-canonical-build.sh
```

The gate installs the pinned SDK, cleans build products, builds from committed
source, runs the recovery/current audio/gameplay/UBSan/preservation regressions,
and records the source SHA and source-file checksums with matching BIN/CUE
checksums. Inspect `build/BUILD-INFO.txt` and `build/CANONICAL-SHA256SUMS.txt`.
ISO timestamps can vary between local rebuilds; retain each actual artifact's
hash and its exact source SHA. The hash above identifies the approved artifact.

The native path is `tools/build-source-complete.sh`; it compiles and links game
source. Runtime audio and neon assets are committed. Authoring WAVs may remain
private because no external WAV is needed for a build. Historical delivered
executables and the old background-patching recipe are references only.

For a future owner-requested manual Actions build: workflow from `main`, profile
`stage-default`, Source ref the exact intended source SHA. Do not use historical
binary-review packaging profiles for source development. Do not dispatch Actions
without owner instruction.

## Approved implementation and history

Fire remains on controls/channels 2/2 and 3/3; Hit is control2/channel8. Music and
independent Flames retain their approved ownership and gains. The initial
56-byte bootstrap/28-word initialization/60-byte backing completes before the
Fire tone and later 64-byte map publication; 0x041a consumption, queue and map
acknowledgments remain mandatory. No obsolete 0x8838 readiness fallback.

Implementation, resource accounting and historical verification details:

- `docs/fire-hit-startup-repair.md`
- `docs/source-complete-sfx-timing.md`
- `docs/level2-shot-hit-swap.md`
- `docs/level2-new-hit-sample.md`

Their historical pending-approval statements describe earlier development
stages; the exact v4 source and artifact identified above are now owner-approved.
