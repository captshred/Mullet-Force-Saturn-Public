# Art workflow

Read [ASSET_INDEX.md](ASSET_INDEX.md) before choosing a source. The approved
reference is `v0.1-playable-baseline` (`921ed1d`); current main includes that
milestone and the consolidation documentation. A newer filename, concept sheet
or branch is not automatically approved replacement art.

## People and review

Dustin is the visual art collaborator / art director: visual identity,
proportions, silhouettes, anatomy, costume continuity, shading and animation
readability. Collaborate with the project owner on approval of native contact
sheets and playable previews. This document does not grant repository access or
change GitHub permissions; those are managed separately.

The integration contributor maintains palette/index conversion, piece placement,
resource manifests, memory accounting and tests. Keep visual changes distinct
from gameplay, timing, hitboxes, movement, audio and engine work. Do not infer
permission for those changes from an artwork request.

## Start an isolated candidate

1. Branch from current main, for example `art/chuck-jump-recovery`; record the
   parent SHA, approved references and requested change.
2. Identify the active native PNG, indexed TGA, manifest, registered pieces and
   final disc override. Some TGA names have multiple historical source versions.
3. Preserve original source art and comparison frames. Existing checksum locks
   deliberately protect them. Add a candidate folder/variant rather than
   rewriting old reference assets or loosening locks to conceal a change.
4. Inventory the current allocation and definition count **before** adding art.
   Main's starting point has only 12,184 VDP1 bytes and two definitions free.
5. Agree on a small review set first. Do not generate full movesets or integrate
   new gameplay states merely to display a candidate.

## Native frame contract

| Item | Current convention |
|---|---|
| Display | 320×240, fixed 60Hz simulation |
| Heroes | 88px standing scale; most idle/walk/run art on 128×96 canvases |
| Hero root | Native (64,92), aligned to simulation center/ground |
| Larger attack/jump review canvases | Often 160×112, with the same root registered at (64,108) |
| Corporate Punk | Current approved opaque height 92px; base canvas 96×96, root (48,92); HQ combat canvas 144×112, root (64,108) |
| Facing | Author right-facing; mirror using the existing hardware/anchor formula |
| Transparency | Binary transparent background, not a baked black backdrop |

These describe source canvases and registration, not a requirement to allocate
one full-frame Saturn texture. Inspect each manifest: trimmed pieces and reused
parts retain the original root. Do not change a root to hide a seam, stretch an
actor to match a concept comparison, or horizontally mirror a whole character
to fake an alternating stride.

Keep pelvis/thigh/knee/ankle connections, planted feet, costume asymmetry and
head proportions consistent. Use diagnostic leg identities or joint markers
only in development previews. Piece crops must reconstruct the approved native
pixels exactly in both directions. The latest running waist fix is a good
example: its visible waist join is inside a texture, not at the actual piece cut.

Concept sheets are visual references. Isolate the approved illustration before
using it; captions, comparison screenshots and proposed animations are not
finished native game assets. Reduce size as a reference step, then clean clusters
at native resolution. Preserve deliberate outlines and shading; avoid blurry
resampling, excessive dithering, detached anatomy and copied commercial sprites.

## Palette and Saturn texture rules

- Reuse the current shared hero palette from `assets/gallery/GB0.TGA` unless a
  separately reviewed palette change is required. Corporate Punk has its own
  approved lighting palette. Torch/tool pieces can use different existing groups.
- Runtime sprites use the existing indexed 8-bit TGA path. Headers carry 256
  padded palette entries; keep raw opaque indices in 1–253. Raw index 0 is the
  transparency key. The pinned Jo loader adds one to indices, so the loaded key
  is 1; do not treat arbitrary black pixels as transparent.
- Hardware palette colors are RGB555. Preview the indexed and hardware-converted
  result, not only an unconstrained RGB drawing. Preserve binary alpha and make
  enlarged previews nearest-neighbor.
- Texture widths are multiples of eight; retain existing even-height conventions.
  Count the actual `align_up(width * height, 32)` allocation for 8-bit textures.
  RGB555 textures cost two bytes/pixel before alignment. Include shared tools,
  HUD, shadows, palettes and definition-only views in the audit.
- Main's full-profile pool is 458,488 bytes, with 446,304 allocated and 253/255
  definitions used. Transparent pixels still occupy a texture rectangle. Two
  identical enemy instances share one bank; do not upload copies per instance.
- Reuse identical pieces and palettes. Do not assume three pieces are always
  optimal, remove approved fallbacks to make room, add per-frame CD reads or
  start a texture-cache redesign in an art-only PR.

## Conversion and integration

Use the scoped generator/packer associated with the active asset folder and
its manifest. Update the candidate's source/recipe, exported TGA, metadata and
preview together. A direct TGA-only edit or a PNG that the packer never reads
will not provide a maintainable source of truth.

The full profile copies base banks and then applies targeted substitutions.
Read `tools/build-native.sh` and [ASSET_INDEX.md](ASSET_INDEX.md) for precedence.
Do not replace the entire sprite sheet. In particular, do not run
`tools/draw-assets.py`, `tools/build-animation-polish.py` or older full-bank
recipes as a general cleanup command: they regenerate historical sources and
can overwrite material outside the approved scope. Do not regenerate audio.

For a source-pixel change, record a mask or before/after coordinates and verify
all pixels outside it. For an assembly change, prove the crop coordinates,
registration, ordering and mirroring rather than masking the symptom in a GIF.
Do not rebase an art candidate by copying an older branch over main.

## Required review packet

- Native and 4× nearest-neighbor contact sheets, with consistent ground roots.
- Native transparent PNGs and the exact indexed assets used by the test build.
- Both-facing loops, including the last-to-first transition; before/after close-ups.
- Piece/seam/root or leg-identity diagnostics, explicitly marked development-only.
- Actual controller-driven gameplay captures when available, clearly separated
  from offline composites/GIFs. A manually repeated artwork loop is not proof
  of input-driven attack sequencing.
- Exact VDP1 bytes/free space, definitions, palette changes and shared-piece reuse.
- Parent/commit SHA, enabled build profile, test results, limitations and matching
  downloadable BIN/CUE with build identity/checksums.

Build the full approved profile with `bash tools/build-run-waist-seam.sh --native`,
then `make check` and `make test`. Candidate integration may need its own explicit
wrapper. Do not silently modify the baseline wrapper to select unapproved art.
Optional emulator scripts live under `tools/test-*-runtime.py`; use controller
inputs and compare gameplay state against the approved control. Do not inject
RAM writes and present them as normal gameplay.

Final approval of an artwork candidate is a visual/playable review decision.
Compilation, pixel tests and emulator captures do not certify physical Saturn
performance, SAROO/optical-drive compatibility or every browser emulator.
