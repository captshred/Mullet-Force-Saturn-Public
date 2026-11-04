# Neon city cleanup review candidate

Branch: `art/city-neon-cleanup`, based on the approved neon-stage commit
`d664f26108f9a958ad1d2ecea3fc2e59a2bba3b9`. The previously interrupted generated
background edit and three-state trash-can sheet were reused; no art was
regenerated during task resumption. Native sources and scoped exports live in
`assets/city-cleanup/`. Original neon, prop and historical assets are preserved.

## Visual changes and scope

Both repeated solid lamp wedges are removed. Brickwork and storefront glazing
continue behind them, while the original lamp heads and slim poles remain.
There is no replacement light cone. Exactly two polygon masks around the old
wedges permit edits (5521 native pixels in the allowed masks, including some
pixels whose final color is unchanged). Every pixel outside the masks is
byte-identical to the approved packed neon scene. The street palette is reused
exactly, including all eight animated colors; animated pixel indices and the
skyline payload are unchanged. The new art is mapped only to static colors.

The old bright drums are replaced by charcoal/blue-gray metal street cans with
elliptical lids, ribbed cylindrical shading, restrained cool/warm rim highlights
and progressively dented sides. All three existing health-selected frames are
updated: intact (HP3), dented (HP2), and heavily dented (HP1). Destruction still
uses the original hit spark, disappearance, scoring and respawn logic. No debris,
new frames, state transitions or palette banks are added.

`CIPIX.BIN` is the native indexed scene source; `PATCHMASK.BIN` specifies the
allowed edit regions. `CANS555.BIN` contains three native 32x48 RGB555 frames,
with zero denoting transparency. `tools/build-city-cleanup.py` deterministically
exports the VDP2 cells, map, parallax chunks and RGB TGA props without redoing
image generation or touching old assets. High-resolution generated masters and
review PNGs stay outside the public repository.

## Alignment and memory

No anchor, offset, collision or dimension changes were needed. Each can keeps
its original 32x48 canvas and draw offset `(x-16, ground-46)`. Opaque art stays
inside columns 2..29, rows 2..45. Existing shadow rendering is unchanged.
The original 24-bit TGA / RGB555 runtime path and magenta transparency key are
retained; the pinned Jo loader supports the explicit top-row TGA descriptor.

| Resource | Approved neon | Cleanup | Delta |
| --- | ---: | ---: | ---: |
| VDP1 texture bytes | 453,344 | 453,344 | 0 |
| Definitions / payloads / views | 255 / 241 / 14 | 255 / 241 / 14 | 0 |
| Three prop textures | 9,216 | 9,216 | 0 |
| VDP1 free bytes | 5,144 | 5,144 | 0 |
| VDP2 street cells | 106,496 (1664 cells) | 106,496 (1664 cells) | 0 |
| VDP2 street map | 16,384 | 16,384 | 0 |
| VDP2 skyline cells/maps | 16,384 | 16,384 | 0 |
| Palette banks | Existing banks | Existing banks | 0 |
| VDP2 allocated + protected SDK banks | 401,408 | 401,408 | 0 |

The lossless indexed cleanup atlas fits the existing budget without a new lossy
pass. A0 retains 24,576 bytes and B0 retains 98,304 bytes free. No SDK-reserved
region, VDP2 priority, animation waveform or gameplay callback was changed.

## Build and validation

```sh
bash tools/build-city-cleanup.sh --native
make check
make test
python3 tools/audit-sprite-memory.py
```

The cleanup wrapper enables `MF_CITY_CLEANUP=1` and delegates to the approved
neon/punch-combo wrapper chain. The old neon and bat-fix wrappers still select
their original assets. The cleanup override changes only staged background and
DR0/DR1/DR2 payloads. Both selected source/profile and a source fingerprint are
recorded in BUILD-INFO. No SDK, Jo Engine or compiler pin changed.

Targeted checks run before the final native build: exact masked preservation,
unchanged neon palette/indices, complete native cell/map reconstruction, matching
parallax chunk mapping, frame dimensions, transparency/ground alignment, actual
street-loader bounds and immutable gameplay/input/actor/audio source hashes.
The full host regression suite covers barrel health, collision, damage,
destruction/scoring, torch/bat interactions and respawn using unchanged code.
Final native build and `make check` verify the actual ISO payloads and matching
BIN/CUE; the sprite audit verifies allocation totals.

Native previews are offline reconstructions, not new emulator captures. The
wedge-free scene and all three prop states were visually inspected at native
resolution and enlarged nearest-neighbor. Emulator/hardware playtest is still
needed to approve the small can's shading/readability during movement and hits.
No claim of physical-Saturn performance certification is made.

## Manual playtest artifact

The existing dispatch-only workflow on main retains the approved **neon-stage**
and **bat-fix** selections and adds **city-cleanup**, pinned to this review
commit. Select workflow branch **main**, profile **city-cleanup**, and leave the
SHA blank or enter the exact cleanup SHA reported with the source commit.
Mismatched profile/SHA pairs are rejected. The single Ubuntu-hosted job builds
the cleanup wrapper and uploads matching BIN/CUE, BUILD-INFO, licenses and
SHA256SUMS as one downloadable ZIP artifact retained for one day. No run is
dispatched during setup; no art/game code is merged into main.

Suggested emulator review: inspect both lamp positions while scrolling; compare
all three can damage states against the pavement, in both camera halves; confirm
jab-jab-cross, immediate/running bat, jump/kick and torch still interact with the
props normally. Keep the current design unless that focused review identifies
another specific issue.
