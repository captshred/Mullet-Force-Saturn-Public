# Proposed native 88px animation contract

## Coordinates and source of truth

Author at final pixel scale on a **128x96 RGBA canvas**, facing right. Root is
(64,92), using a pixel-boundary convention: a planted sole ends at row 91 and
the ground line is y=92. The approved standing silhouette spans y=4..91 (88px).
Do not scale the head, torso or limbs independently to fill each crop. The
prototype uniformly downsamples each full generated pose to 88px and registers
its silhouette center; this is a provisional extraction, not final joint rigging.
Future approved walk frames may bob 1px while preserving the planted contact.
Keep a separate pelvis/root landmark and label near/far foot, contact/lift,
shoulder/hand and weapon sockets in frame metadata. Passing feet may lift;
never lower the ground root to hide a missing contact.

For wide moves, use a **192x128** authoring canvas with root (96,112), preserving
the same body scale and 88px neutral stature. Its purpose is spare space for
weapons/extended limbs, not larger standing characters. Airborne movement is
`ground_y-height/256` from the existing simulation; do not bake trajectory or
world displacement into the pixels. Defeat/landing crouches may be shorter.
Do not crop off hair, boots, hands, bat tips or flames to meet a texture cap.

Canvas extents, contact landmarks and runtime anchors are independent of the
unchanged hurt/attack boxes in game.c. Maintain the current 24.8 positions,
60Hz timing and hitstop. New visual poses can share existing active intervals;
adding a visual frame is not authorization to add an active hit or extend reach.
The existing root anchor is (canvas_center,92) in normal authored source art;
its crop-relative coordinates are recorded in src/art_data.h and the inventory.

## Palette and transparency

Keep source PNGs RGBA. No matte background, shadow baked into feet, soft alpha
in runtime pixels, palette-index-zero outlines, lossy image encoding or dither.
For the study, all frames map to the existing combined gallery palette: raw
index **0** transparent, **1..253** opaque; Jo's indexed-TGA loader adds one,
so hardware index 1 is the transparency key and indices stay below end codes.
Use the exact same RGB palette bytes across pieces and frames. Runtime color
is Saturn RGB555; do not infer extra effective color depth from PNG bit depth.

Premultiplied-alpha Lanczos is used only for reducing the high-resolution
candidate source. A threshold of 128 makes native coverage binary. Native
approved idle pixels are copied exactly and never filtered. Candidate colors
use nearest palette mapping without diffusion. The visible alpha mask, RGB
values, footprint and palette bytes must survive split/reassembly exactly.
Final pixel cleanup must be reviewed at 1x and enlarged nearest-neighbor.

## Packing and mirroring

The initial prototype partitions canvas rows [0,24), [24,80), [80,96), then
crops each band's transparent bounds. Piece width is padded to a multiple of
8 pixels; VDP1 allocation is rounded to 32 bytes. Metadata contains source
x/y, padded dimensions, palette reference and per-frame duration. Padding is
transparent and never treated as anatomy. Every visible pixel appears once.
Idle's bands exactly coincide with the approved three pieces after the 4px
canvas top offset; its existing six texture IDs are reused.

For right facing, screen piece x = root_x-64+piece.x. For left facing it is
root_x+64-piece.x-padded_width, with hardware horizontal flip enabled. Y is
ground_y-92+piece.y. This matches the approved gallery's mirrored anchors,
including odd silhouette widths. Do not merely negate crop origins or mirror
unpadded widths. No separate left-facing texture set is needed. Validate both
facings by independently assembling pixels and checking the ground boundary.

The fixed horizontal bands are a starting point, not a claim that limbs can be
rotated without redrawing. For bat/torch extensions allow separate body/weapon
pieces and explicit grip/tip/nozzle sockets. A frame exceeding its cache slot
budget must use more suitable packing or a larger declared class; never silently
clip, shrink, reduce gameplay reach or overwrite the next texture allocation.

## Extending the approved design after cycle review

* Walking: preserve the face, hair mass, costume ramps, knee detail and boot
  buckles. Redraw weight shift and near/far leg occlusion per pose. Rigidly moving
  a whole lower rectangle is a motion study, not sufficient finished walking.
* Jumping: reuse the old rise/air/landing/kick body mechanics and root trajectory
  as pose references, redraw compression and airborne legs at the new proportions.
* Punching: retain coil/contact/recover counters and active frames; author the
  forearm/torso turn and foreshortening instead of stretching an idle glove.
* Bat: keep seven stages, existing grip/tip path, CCW screen arc when right
  facing and mirrored CW when left. Ground and air share upper poses but need
  distinct lower-body support. Landing resumes recovery at counter 28.
* Torch: preserve charge, direct transition to fire, release/away timing,
  ground-only damage cone, and four-frame flame clock. Existing lower pieces
  provide pose references; new costume details require new pixels, not recolors.
* Hurt/recovery: the old art reuses coil and landing poses. Dedicated new
  reaction/get-up drawings may improve readability while preserving hurt,
  invulnerability, defeat and recovery timers and the unchanged collision root.

No candidates for these additional moves are generated in this phase.
