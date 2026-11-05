# Level 2 hero sprite pass 3 — canonical concept translation

Branch: `feature/level2-hero-sprite-pass3`.
Parent: `2347d91f0979df846471c2eb13a92b93929eb256` on
`feature/level2-player-sprite-pass2`. Protected and earlier branches remain
unchanged. No GitHub Actions run was launched.

## Concept to native assets

The supplied Mullet Force concept sheet is the primary design source. Its six
central hero poses were adapted into an isolated six-pose review using the image
generation/editing tool, then converted to native 32x32 RGBA grids, quantized to
compact character palettes and encoded as big-endian RGB555 with zero
transparency. The attached reference was used directly for the silhouettes,
membranes, head/sunglasses/mullet treatment, suit shading, belts, boots and roll
attitudes; this is not a fresh character invention or reuse of the earlier
procedural silhouettes.

The fixed native pixels live in `tools/hero_sprite_pass3_data.py`. The existing
asset generator reads those exact rows and reproduces the six committed BIN
files. Runtime builds need neither the concept sheet nor generated high-resolution
review art. Review exports stay in `work/`; no high-resolution art master,
reference sheet or art archive is committed. The generator still reproduces the
unchanged drone, bullets, explosion and industrial-background payloads.

Buck keeps the concept's broad silver body, high-contrast shoulder/sleeve folds,
red wing membranes, gold/copper mullet, black sunglasses band and separated dark
boots. Chuck keeps its leaner black/charcoal body, cool highlights, purple wing
membranes, brown mullet, black band and separate legs/boots. Native palettes use
at most sixteen nontransparent colors per hero, with direct RGB555 storage;
there is no new CRAM palette allocation.

All six canvases remain 32x32. The artwork is fitted into the compact canvas
rather than enlarging the actor or changing anchors/collision boxes. The bank
poses retain upward flight but roll diagonally: left bank lowers the left wing,
raises the right wing and carries head toward upper left / boots toward lower
right; right bank does the opposite. The two sides are separate adapted poses,
not mirrored substitutions. Asymmetric lighting and membrane folds remain.

## Integration and preservation

The same six asset names and existing center/left/right texture IDs are used.
There is no change to `src/wingsuit_runtime.c`, `src/wingsuit.c`, or
`src/wingsuit.h`: banking selection, actual-movement filtering, render positions,
SGL initialization, focus/tap timing, speeds, projectile behavior, damage and
restart all retain their exact parent bytes. `/ALEVEL2` remains a thirteen-file
bank with the same directory-change/error handling and exact ISO validation.
The nineteen-character restart-field clear and compile-time width check that
removed the stray T are unchanged and still tested.

Only the six hero BIN payloads and their manifest hashes change among runtime
assets. Level 1 art/audio/gameplay, stage clear/transition, drone, both bullet
textures, explosion, background, native build profile, workflows and preservation
locks remain unchanged. No exception or bypass was added to existing checks.

## Resources

| Resource | Usage | Delta from pass 2 |
| --- | ---: | ---: |
| VDP1 texture bytes | 15,744 | 0 |
| VDP1 definitions | 10 | 0 |
| Six hero textures | 2,048 bytes each, 32x32 | 0 |
| VDP2 SDK + arena reservation | 434,176 bytes | 0 |
| Stage cell/map payload | 10,944 bytes / 43 tiles | 0 |
| Stage CRAM payload | 32 bytes | 0 |
| SCSP loaded stage resources | 0; sound CPU remains halted | 0 |
| Player shots / hostile shots / enemy slots | 32 / 16 / 8 | 0 |
| Shooter simulation state | 1,408 bytes | 0 |
| Banking presentation state | two integers / 8 bytes | 0 |
| Maximum shooter object draw commands | 58 | 0 |

The Python pixel grids are authoring/reproduction inputs, not linked into the
Saturn executable. There are no new textures, definitions, frames, allocations,
per-frame uploads, simulation fields or runtime loading steps. Whole-program
RAM, stack usage and frame timing are not newly measured here.

## Tests and limitations

The full `make test` exits 0 with 189 PASS reports. The new canonical-asset
regression verifies six exact native grids, 32x32/RGB555 encoding, visible
red-versus-purple membranes, center symmetry, both lowered-wing roll directions,
and that bank poses are not bitmap mirrors. Existing tests cover all six pose
IDs, per-player state selection, movement/focus/tap combat, the 100,000-tick
stress run, restart/HUD clearing, all thirteen asset loads/failures, SGL state,
ISO order/content and stage-clear behavior.

Approved art/audio/source-preservation checks pass. Byte comparisons against the
parent verify all gameplay/runtime/banking/loading code and all nonhero runtime
art are unchanged. Existing resource and source-preservation checks remain
active; no preservation hashes needed adjustment.

Native build setup still fails because the configured shell proxy cannot fetch
the pinned SDK. No new native BIN/CUE, Saturn/WebRetro playtest, CRT readability
assessment or hardware frame-time result is claimed. Inspect the new heroes at
actual scale, both alone and together, and verify all bank attitudes in the next
manual playtest. The baseline's playability does not validate this new art pass.

## Exact manual build

On a build-capable x86-64 Linux checkout of the delivered commit:

```sh
git switch feature/level2-hero-sprite-pass3
bash tools/bootstrap.sh
make clean
bash tools/build-level2-wingsuit.sh --native
make check
make test
```

Outputs: matching `build/mullet-force.bin` and `build/mullet-force.cue`. Keep
them together and open the CUE. For an explicitly requested manual Actions build,
use **Manual Saturn playtest build**, workflow branch `main`, profile
`stage-default`, and source_ref set to this feature branch or the exact delivery
SHA. No workflow change or automatic run is required.
