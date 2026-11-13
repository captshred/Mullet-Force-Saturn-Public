# Ricky rose tattoo — art-review candidate

**Owner art approval is pending.** This branch is for review, not a new THE ONE.

Starting source: `76f50b4fb1bcfbbeb4bc8fb8287ea08219dc23c7` on
`polish/level1-ricky-flash-torch-charge`.
Candidate branch: `art/ricky-rose-tattoo`.

## Review images

- [All 25 native poses, before/after](all-25-before-after.png): each pair includes
  actual 1x runtime pixels, with a nearest-neighbor enlargement below where it fits.
- [All 25 shoulder close-ups, before/after](all-25-shoulder-closeups.png): consistent
  6x enlargements of actual native RGB555 pixels, not the unquantized source art.
- [Individual transparent native sprites](native/), one PNG for each pose.
- [Native Yabause captures: 50 pose/class/facing fixtures](native-yabause-50-poses.png),
  using the real loaders, `draw_game`, VDP1 and production assets. These are controlled
  test fixtures, not naturally spawned gameplay or hardware approval.
- [Updated authoritative source sheet](../../Ricky_HQ_Animation_Sheet.png).
- [Unmodified recovery source sheet](../../art/ricky/Ricky_HQ_Animation_Sheet.original.png).

The exposed shoulder/upper arm is skin-colored around a compact dark-outlined red
rose with a short green stem/leaf cluster. The flower sits near the deltoid and
follows the arm's rotation in the punch/chain/fall poses. The back-facing turn
places the rose on the corresponding anatomical right upper arm (image right),
not the back of the vest or the opposite arm. Native foreshortening limits the
stem/leaf detail to a few pixels in the smallest views; review those poses at 1x.

All 25 pose panels were compared against their originals, including the six walk
and four chain frames, hurt/fall and back-turn views. No torso recoloring, weapon
edits, gameplay overlays, additional sprites, animation changes or movement changes
were introduced. Faces, other characters, reference portraits and non-arm source
pixels remain untouched. Black vest edges outside the deltoid edit regions remain
original; the sleeve-like deltoid patches are the intentional clothing correction.

## Integration and preservation

The artwork lives in the updated root source PNG before conversion. The original
sheet, original indexed runtime payloads, manifest, region annotations and source
provenance are retained in [`art/ricky`](../../art/ricky/).

`python3 tools/prepare-ricky-art.py` regenerates native TGAs, individual PNGs,
shared palette, atlas, manifest and generated native metadata. It retains the
original dimensions, anchors and exact alpha/silhouette in every pose. Ten red,
green and dark ink colors reuse redundant RGB555 palette entries. Original
indices are remapped only to identical RGB555 words, so **every native pixel
outside the edited arm regions has exactly its original hardware color**.
This prevents a new global palette quantization from degrading the other art.
The standard warm-red flame-flash transformation remains unchanged in slots 2/3.

`python3 tools/preview-ricky-rose.py` regenerates the source/runtime review PNGs.
The source is already edited; no generated tattoo or overlay runs in gameplay.
Authoring conversion retains the existing Pillow/NumPy/SciPy dependencies.
Normal validation uses only the existing Pillow and standard-library dependency.

| Resource | Before | Candidate |
|---|---:|---:|
| Ricky texture definitions | 25 | 25 |
| Ricky VDP1 texture bytes | 114,048 | 114,048 |
| Total definitions | 177 | 177 |
| Total VDP1 texture bytes | 371,072 | 371,072 |
| Free usable texture bytes | 87,416 | 87,416 |
| Protected Buck/Chuck reserve | 49,152 | 49,152 |
| Margin beyond reserve | 38,264 | 38,264 |
| Additional CRAM allocation | — | 0 |

No gameplay, AI, spawn sequencing, player combat, audio, Level 2, texture bank
architecture or palette allocation code changed. The only runtime source-data
change is the generated Ricky palette in `src/ricky_data.h`; frame metadata is
unchanged. No THE ONE tag or prior branch moves.

## Validation

- `python3 tools/test-ricky-rose-art.py`: all 25 localized edits, source recovery
  hashes, exact dimensions/anchors/resources/alpha, exact RGB555 preservation
  outside arms, visible red/green tattoo colors in every native pose.
- Native `stage-default`, `make check`, `make test`: existing UBSan combat,
  charge/cancellation, independent Ricky/CP red flash and renderer regressions.
- Existing host suite: 256 enemy suffix reloads, all 25 poses/both facings,
  palette and persistent pixel integrity, failure latching and stale-handle guards.
- [Eight native suffix reloads](bank-reloads.json): nine identical generations of
  persistent/enemy pixels and palettes 2–5; unchanged texture peak; healthy Level 2
  entry afterwards with nonzero audio. No emulator RAM writes or bypasses.
- [50 native pose fixtures](native-fixtures.json): all 25 poses, both facings,
  mixed Corporate Punk/Ricky and two-Ricky scenes with both heroes present.

Hardware testing and subjective art approval remain pending. Emulator fixtures
and structural preservation do not establish that the user likes the design.

## Manual Saturn playtest build

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`).
Use workflow from: **art/ricky-rose-tattoo**. Profile: **stage-default**.
`source_ref`: the full candidate commit SHA from the delivery report.
Keep the matching BIN/CUE from `mullet-force-stage-default-<full SHA>` together.
Artifact retention is one day. No merge or baseline-tag update is authorized.
