# Native character polish — ff24c5e comparison

> Historical ebc9d79 report. The later gait audit confirmed that shading and
> support labels did not create an alternating stride. The stance-lock claim
> below described repeated geometry and is withdrawn as a full-gait claim.
> See [gait-correction.md](gait-correction.md) for corrected artwork, measurements
> and current memory totals. This file preserves the earlier milestone record.

The branch remains character-animation-upgrade. ff24c5e is preserved as the
recovery checkpoint, and all earlier experimental branches and main are untouched.
The ff24 prototype PNG/TGA files, approved master references and gameplay banks
remain byte-identical. This milestone edits only the optional review artwork
and its preview/pipeline; no combat, movement, hitbox, attack or game timing changes.

## Artwork changes

Six original walk poses per fighter remain the basis; there is no regenerated
moveset. A localized boot-edit guide supplies 69 conservative sole-shade pixels.
No generated replacement heads, torsos or whole poses are used. The rest of the
polish uses the existing native pixels with integer cluster/row translations,
explicit pelvis/ankle registration and shallow far-leg shade mapped back into
the exact existing shared palette. No rescaling, interpolation or new colors.
The offline generator records the edited guide and hashes for reproducibility.

The head/crown and a protected face/sunglasses region are fixed to each fighter's
approved walk reference across all six poses. The belt/pelvis reference is fixed
at native x=66. Existing leg rows retain their widths; small lateral corrections
register the support heel at x=80,72,64 per half-cycle. Near/far support roles
alternate through explicit annotations and depth shading; heel landing, rear
toe-off and a lifted trailing boot separate contacts from passing poses.

At the unchanged 390/256 px/tick reference speed, each five-tick keyframe advances
the root by 7.617px. The registered stance heel therefore drifts less than 1px
across each three-keyframe planted interval. This is a keyframe measurement,
not a claim of per-tick foot IK: held five-tick poses remain discretely animated,
and the toe-off/crossing silhouette still warrants visual acceptance at 1x.

Buck has a two-pixel trailing lift, lighter jacket/chest changes and a small
blond-tail follow-through. Chuck lifts one pixel, keeps a heavier planted read,
and has slower breathing with delayed brown hair/vest motion. Head/torso widths
are stable rather than independently redrawn or resized between steps.

Each fighter has **four distinct idle drawings**, with the exact approved idle
as pose 0 and the identical returning pose when the loop wraps. Feet and all
pixels below row 48 stay unchanged throughout breathing. Tiny shoulder/chest,
lapel/vest and tail-cluster movements stay above that line; face features do not
move. Buck's cycle is 24/16/24/16 ticks (80 total); Chuck's 30/18/24/18 (90).
Two five-tick guard handoff poses ease idle/walk switching, including a reused
breathing pose. Stop requests finish at a contact phase before lowering guard.
These are preview presentation timings, not modifications to game animation logic.

## Memory before and after sharing

All 42 old pieces are unique; byte hashing found **no savings** merely deduplicating
the original prototype. Before adding the new bank, the pipeline interns by
padded dimensions plus exact indexed payload (palette fixed). Translation/crop
origins are not part of a texture's identity. Identical head, foot and bridge
pieces reuse the same existing or newly loaded sprite ID.

| VDP1 texture allocation | Bytes |
|---|---:|
| ff24c5e original gameplay + approved gallery + prototype | 355,808 |
| New polished poses loaded independently without sharing | 120,032 |
| Actual new unique polished resources (32 pieces) | **74,688** |
| Avoided allocation through exact sharing | **45,344** |
| Actual review-build total | **430,496 / 458,488** |
| Remaining texture arena | **27,992** |

The naive comparison would exceed the arena by 17,352 bytes; sharing makes the
complete A/B build fit without removing old sprites. The actual allocator end
is checked before uploads, after every unique upload and at completion. Existing
palette bank 7 is shared read-only; there is no additional palette/CRAM bank,
VDP2 allocation, CD read or texture upload during playback. All frames are
resident for this review. The full animation cache is not implemented.
VDP2 remains 123,008 layer bytes / 385,152 reserved with parallax enabled, or
106,624 / 368,768 without it. The eight existing 512-byte CRAM banks are unchanged.
The link map and BUILD-INFO identify the final SH-2 code/metadata/state footprint.

## Review controls and files

Cold-boot the matching BIN/CUE. Down opens the review from the gallery.
The default set is polished. **Hold A+B** to toggle polished / ff24 prototype;
pressing the second key while the first is held also works. The chord consumes
mirror/pause actions. Up requests idle/walk, B pauses, A mirrors, Left/Right
steps the selected cycle, Down returns to gallery, and Start enters the original
normal title/game flow. C retains the existing asset diagnostic page.
When paused, Up changes cycle directly for inspection; when playing it uses the
handoff. Selecting original never substitutes gameplay sprites.

Open polished/preview.html in the review artifact for the side-by-side original /
polished viewer. walk-compare-native.png and idle-compare-native.png show native
pixel size; the 2x versions use nearest-neighbor enlargement. Transparent PNGs,
walk and idle GIFs, the shared-resource manifest and the original references are
included. GIF times are quantized to centiseconds; the Saturn/HTML clocks use
60Hz ticks. The three-piece system and hardware mirrored padded origins remain.

## Validation and limits

Asset validation independently reconstructs every pose/palette/alpha, both
facings, all three seams, protected face and head regions, idle feet, distinct
breathing phases, support annotations, resource interning and arena bounds.
Host tests exercise independent idle clocks, old/new walk cadence, both handoff
directions, comparison chords, pause/step/mirror, original ID reuse and load
failure guards. Existing gameplay and previous graphics tests remain required.

No new attacking or other move banks are authored or replaced. This is an
artistic review milestone; remaining acceptance is visual, particularly contact
reads at 88px, the discrete five-tick foot motion and the guard handoff. Physical
Saturn timing and this new candidate's WebRetro behavior require user/device tests;
local emulator checks do not establish hardware compatibility.


## Measured verification result

All seven native build/asset configurations pass: VDP1 with/without gallery,
VDP2 without gallery, gallery, parallax, animation-only and the combined build.
Existing game/combat/co-op/input/music/graphics tests and new presentation tests
pass; ASan/UBSan preview checks pass. Original game.c, game.h, combat_config.h,
art_data.h, input.c, original gameplay assets and ff24 prototype assets have no
changes. ff24c5e is a preserved ancestor, not rewritten.

Local libretro Yabause (v0.9.15 8926b0c, software/interpreter, HLE BIOS, one thread,
no RAM cartridge) runs 2,000 frames of controller-driven comparison. Independent
RGB565 reconstruction checks every new idle/walk and every old prototype pose
in both facings, frame-by-frame guard stopping, and both automatic idle clocks:
**7,171,200 actor/ground-region pixels, zero mismatches**. Complete observed
breathing holds match 24/16/24/16 and 30/18/24/18 VBlanks. Gallery restoration
is byte-exact; diagnostics, comparison, pause/step/mirror, parallax handoff and
entry into original gameplay are exercised. See polish-validation.json and the
polished/runtime-captures folder. The report hashes identify the tested source;
subsequent report-only commits do not alter that code.

The resident SH-2 image/BSS end is **0x06097C24** with both experiments, versus
0x06097094 for ff24c5e: **2,960 extra bytes** including code, metadata, state and
alignment. Animation-only increment is 2,832 bytes. Preview persistent state is
344 bytes versus 196 (148 extra), included in those totals. No CPU frame bank is
retained and the 384KiB Jo heap reservation is unchanged; temporary loader peak
was not separately profiled. New polished TGAs occupy **99,840 CD bytes** including
palettes/headers. There are 169 VDP1 sprite descriptors, below Jo's 255 maximum.

The preview remains in-place, with discrete five-tick drawings. It is not a
per-tick foot-lock/IK system, nor an expansion of gameplay move banks. Near/far
occlusion, the small guard handoff and perceived cloth/hair weight still need
your native-size visual verdict. No physical Saturn, audio listening, exhaustive
combat playtest or WebRetro test of this new candidate is claimed here.
