# Three-pose swagger walking experiment

Branch swagger-walk-test, from playable milestone 05b53c0. All six original walk
frames, all four approved idle poses and every original gameplay bank remain
unchanged. No dash, speed, physics, hitbox or combat changes.

The low recoil poses were suitable references, but selecting them alone retained
a broad contact and an abrupt high-knee loop. Three localized leg edits make a
near weight-bearing step, a narrow low neutral transfer and an opposite toe-off.
No high passing knee. This is a deliberate stylized three-pose weight-rock,
not a claim of a fully sampled anatomical two-step. Source upper rows 0..51 are
pixel-identical to approved poses; only the lower legs are edited and mapped
into the existing palette. Source guide, native PNGs, contact sheet and exact
resource mapping are in assets/swagger-walk. Native 128×96 canvas, root (64,92),
opaque rows4..91 (88px), binary transparency, three pieces and hardware mirroring.

Buck uses 14/14/14 ticks (42 total, 0.700s); Chuck 15/14/15 (44 total, 0.733s).
The preserved six-frame comparison is 40 ticks (0.667s) at the approved 75% rate.
Tune only src/swagger_timing.h to adjust holds; rebuild offline review images
with tools/build-swagger-walk.py and tools/build-swagger-review.py after
changing the documented constants, and update the cadence assertions. Gameplay
walk counters remain authoritative and independent for both players. All idle
breathing clocks/poses are untouched. No new controls intercept gameplay input.

## Builds and resource lifetime

The swagger artifact enables MF_SWAGGER_WALK=1 and defaults to three poses in
normal gameplay. Start leaves the gallery; Start again begins play. Port2 Start
joins Chuck. The separately labeled playable-animation artifact leaves the flag0
and uses the preserved six-frame walk under identical game mechanics.

At boot, only existing gallery sprites, four breaths and three swagger poses
are uploaded. Down from the gallery opens the existing complete animation review;
it preflights and loads its missing resources ONCE at this stopped mode boundary.
This can pause visibly for CD reads. Returning to gameplay retains that expanded
bank; no eviction or full animation cache is introduced. Neither gameplay nor
animation playback reads the disc, uploads textures, or allocates frame memory.
The old gallery walk preview retains its original 30-tick cadence. Use the
six-frame PLAYABLE artifact for the 75% gameplay comparison.
A failed optional review load uses the existing asset diagnostic error 710.
Cold-boot to return to the smaller allocation. The gallery and diagnostics show
the actual current allocation after expansion.

| Configuration | VDP1 allocated | Free |
|---|---:|---:|
| Preserved six-frame gameplay/review |427,104|31,384|
| Swagger default, before opening animation review |346,368|112,120|
| Swagger after opening the complete old review |439,776|18,712|

All include original gameplay sprites/HUD and the approved gallery. Actual boot
savings are 80,736 bytes, not an assumption that unselected frames disappear.
The new leg textures cost 12,672 bytes when combined with the full old bank.
Exact byte/dimension interning reuses upper-body pieces. Sprite slots 123 at boot,
188 after expansion, limit 255; palette bank 7 reused, zero new CRAM/palettes.
VDP2 parallax reservations 385,152 and eight 512-byte palette banks are unchanged.
All source files remain on disc for the optional review, even when not resident.

The comparison artifact always retains the old full preview and is also a
regression reference for controls, actors, palettes, background and combat.
The future dash can be a separate presentation selector later; no dash state,
input gesture, aggressive artwork or extra allocation is implemented here.

## Review and limitations

In the Swagger artifact, open animation-review/swagger-walk/comparison.html for native-pixel animated
six/three comparison and swagger-contact-3x.png for the three poses. The HTML
uses exact 60Hz timing; GIF timing rounds to centiseconds. All art is experimental.
Review loop 3→1, starts/stops, diagonals, reversals, near/far weighting, both
fighters independently and transitions into original attack/jump/torch sprites.
Stopping still selects the unchanged wider idle stance immediately; no extra
transition artwork is allocated. Three held poses can still slide or pop; no per-pixel foot IK is claimed. Old
fallback art can change size/posture abruptly while preserving the logical root.
Physical Saturn/WebRetro user testing remains separate from local emulator tests.

## Measured validation

All 11 native configurations pass builds/asset validation, including original
VDP1 fallback, gallery/animation/parallax and swagger with/without parallax. All
existing gameplay/input/combat/audio tests and focused bank/pose tests pass.
ASan/UBSan pass for swagger presentation, selective loader/expansion and the
preserved preview. No original art, input/game/combat or hitbox source changed.

Local Yabause completed 1,050 frames per playable/control sequence: **469,220**
swagger sprite pixels and **452,213** six-comparison sprite pixels match native
references, zero mismatches. Both builds' full game structs match the original
renderer on every one of 720 compared frames. All four idle poses and all three
swagger poses are observed for each fighter, both facings; original action
fallback regions also match. Resident texture-area hashes remain stable.

The 1,600-frame review-entry test reads actual allocation and descriptor counters:
346,368 bytes/123 slots before entry, 439,776 bytes/188 slots after entry, unchanged
after returning to gameplay. The expanded old idle preview matches 28,800 pixels
exactly. The unchanged six-frame gallery/preview regression runs 2,000 frames with
7,171,200 actor/ground pixels compared, zero mismatches and exact gallery restore.
Read-only standard libretro save states provide diagnostics; no game hooks or RAM
writes are used. Occluded/UI pixels are excluded from character-only comparisons.

Combined swagger image/BSS ends at 0x06098574, versus baseline 0x06098034 (+1,344
bytes code/metadata/state/alignment). The six-comparison ends at 0x06098244 (+528).
The larger ID map and one-shot loader bookkeeping cost 56 extra mutable bytes;
no CPU animation-frame bank or new idle/walk per-player clock state is allocated.
The existing 384KiB heap and sound-RAM budget 296,416 bytes remain unchanged.
See swagger-validation.json and the Swagger artifact's runtime/*.png for evidence.
These local core tests do not establish real Saturn performance or WebRetro
compatibility; please playtest the three-pose style and foot contacts.

## Exported-build test limitation

Both exported playable ZIPs passed their gameplay/pixel checks. One exported
Swagger expanded-review run wrote all 1,600 frames (last trace 1599) and then the
frontend/core process exited with SIGSEGV11 during the shutdown path. A repeat
passed the complete allocation/pixel/game-return checks and shutdown; another
instrumented repeat completed both retro_unload_game and retro_deinit normally.
The cause is unresolved and remains a test limitation. No game/graphics changes
were made to suppress it. See runtime/shutdown-observation.txt in the Swagger
review files. WebRetro and physical-device testing are still needed.
