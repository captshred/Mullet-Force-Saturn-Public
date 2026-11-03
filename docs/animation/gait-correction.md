# Six-frame opposite-stride correction

Checkpoint: ebc9d79169bd91bbd982fb4c036041734618664f, on
character-animation-upgrade; ff24c5e and ba4938e remain ancestors.

## Finding

The user was right about the repeated gait. Neither fighter had literal duplicate
RGBA frames, and the preview selected six distinct mappings at five ticks each.
However, each second half repeated the first half's contact/down/passing leg
configuration with shading and small offsets. Those changes did not establish
opposite leg ownership. Earlier support-role annotations and the associated
full-gait interpretation were misleading; they are replaced, not offered as proof.

Comparing native lower-body rows52..95, old pose3/6 differed at only 21 silhouette
pixels for Buck (96.72% overlap/union), and 45 for Chuck (93.64%). See
assets/animation-polish/gait-audit.json for all three pairs before/after. Pixel
uniqueness alone cannot establish anatomical alternation.

## Changes

Walking frames1..3 are byte-identical PNGs to ebc9d79. Frames4..6 import edited
legs only below row52; rows0..51 remain pixel-identical in **all six frames**.
Thus faces, sunglasses, hair, shoulders, chest, arms, costume upper details and
body scale cannot drift. Existing idle/breathing and guard bridge poses are also
unchanged. The original prototype, gallery, gameplay banks and combat code are
untouched; this remains the optional preview, not a gameplay replacement.

The intended cycle is near contact → near down/far trailing → near support/far
passing → far contact/near trailing → far down/near trailing → far support/near
passing → near contact. Frame4 changes the hip-to-knee paths/overlap, rear toe-off
and front heel contact. Frame5 is a low recoil with the trailing boot leaving the
floor, rather than repeating the old down pose. Frame6 puts the raised knee/boot
in front of the opposite supporting leg. The existing facing is retained; these
are edited legs, not horizontally mirrored characters. Buck keeps the sharper
knee-pad/lift read; Chuck's denim/thicker legs and lower recoil read heavier.
Their existing distinct upper-body secondary motions remain unchanged.

Canvas128×96, opaque height88 (rows4..91), ground/root(64,92), six poses × five
ticks, transparent index0, existing shared indexed palette and native display
remain fixed. Contact4 rolls the heel/toe sole edge one pixel without moving the
ground. The pelvis boundary is retained. Support soles stay on row91; this does not
assert a stationary world-space heel across all holds. Physical per-tick foot lock is **not**
claimed: held five-tick poses necessarily advance discretely, and preserving the
first three poses constrains how much the whole loop can be reworked. Review
3→4 and 6→1 at native size before accepting this candidate for playable sprites.

## Exact texture budget

| Allocation | Previous polish | Corrected |
|---|---:|---:|
| Existing game/gallery/prototype | 355,808 | 355,808 |
| Additional unique polished textures | 74,688 | **71,296** |
| Total VDP1 textures | 430,496 | **427,104** |
| Available allocator bytes | 458,488 | 458,488 |
| Remaining | 27,992 | **31,384** |

A first fixed-split candidate required 75,616 bytes and was rejected by the budget
guard before being accepted. Sharing larger unchanged walking upper-body pieces
and selecting even lower-piece split lines recovered the space. Every pose still
uses exactly three pieces, with unchanged source pixels and logical anchors.
The resource key includes padded dimensions and exact indexed bytes. There are
39 new unique pieces versus32 previously (176 total sprite slots versus169);
more smaller shared pieces cost fewer bytes. Naive independent polished pieces
would take119,360 bytes; exact sharing avoids48,064. No new palette, CRAM, VDP2,
heap allocation, playback upload or animation cache is introduced.
VDP2 parallax remains123,008 layer bytes /385,152 reserved; eight512-byte CRAM
banks remain unchanged. Disk-only before/after images are never loaded into VDP1.

## Review

Open polished/gait-review.html from the review artifact: before ebc9d79 left,
corrected right; pause, step and mirror supported. gait-compare-native.png and
-2x.png show all six. gait-before/*-walk.gif and current *-walk.gif provide
animated comparison. The old ff24 versus corrected viewer remains preview.html.
Saturn controls are unchanged: Down from gallery opens preview; Up idle/walk,
B pause, A mirror, Left/Right step, A+B ff24/corrected toggle, Start original game.

## Validation

All seven native build/asset configurations pass (VDP1 with/without gallery,
VDP2 without gallery, gallery, parallax, animation, animation+parallax). Existing
gameplay/combat/co-op/input/music/graphics tests and preview tests pass; preview
ASan/UBSan checks pass. Native pixel reconstruction,
palette/transparency, mirrored anchors and seams, preserved first half/upper
bodies/idle/bridges, changed lower silhouettes, unique resources and the stricter
no-growth427,104 budget are checked independently. Geometry assertions guard
against regressions; visual review remains necessary for anatomical quality.
The combined build resident image/BSS ends at **0x06097CF4**, 208 bytes above
the prior polish (metadata/IDs/alignment), with no new CPU frame bank.
No real-hardware or new WebRetro compatibility claim is made from host/CI tests.

The final local libretro Yabause v0.9.15 /8926b0c run (software renderer,
interpreter, HLE BIOS, one thread, no RAM cartridge) completed 2,000 frames.
All corrected idle/walk and original poses in both facings, guard bridges,
automatic idle durations and gallery restoration pass: **7,171,200 compared
actor/ground pixels, zero mismatches**. Controller input also exercises return
to parallax and original gameplay. See gait-validation.json and
polished/gait-runtime/*.png. These checks verify exact native rendering and
load/control behavior, not aesthetic approval or physical Saturn performance.
