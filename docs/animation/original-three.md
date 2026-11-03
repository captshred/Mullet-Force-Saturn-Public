# Exact original three-pose walk restoration

Branch original-three-walk-test from Swagger milestone 8e86fa1. No artwork edits.
The source is assets/animation-study/{buck,chuck}-01.png through-03.png, created
at 5a6bd36 and preserved byte-identically in approved recovery checkpoint ff24c5e.
Historical Git comparisons verified all six PNGs and all 18 indexed TGA pieces.
These are the ORIGINAL complete frames, not the later polished first half or
Swagger legs. Full original faces, upper motion, knees/boots and costumes remain
untouched. Corrected six and Swagger source trees are unchanged.

## Play and timing

Unzip the matching BIN/CUE. Start leaves the gallery; Start again begins play.
Port2 Start joins Chuck. Both builds use the same exact three images in order.
No controller combination changes timing or consumes gameplay controls.

| Build | Frame holds at 60Hz | Loop |
|---|---|---|
| A moderate |8/8/8 ticks|24 ticks, 0.400s|
| B slower |10/10/10 ticks|30 ticks, 0.500s|

MF_ORIGINAL_THREE_WALK=1 enables the restored bank. MF_ORIGINAL_WALK_SLOW=0/1
selects A/B. Tick constants are in src/original_three_timing.h. Gameplay walk
counters, movement/diagonal speed, physics, combat, input and hitboxes do not
change. Approved FOUR-frame idle breathing is retained unchanged, with independent
player clocks. All unfinished actions still use the complete original renderer.
No dash, running art or Corporate Punk content is added.

## Memory

Both timings allocate **351,104 /458,488 VDP1 bytes**, leaving **107,384 bytes**,
using 125 sprite slots. They reuse 18 original walk pieces and the existing idle
bank; no new textures, palettes or duplicate uploads. This is 4,736 bytes more
than Swagger’s 346,368-byte fresh bank, because the original pieces share less.
It is 76,000 bytes below the 427,104-byte full corrected-six comparison bank.

Down from the initial gallery loads the preserved full old preview ONCE, adding
only missing resources; total becomes 427,104 bytes, free 31,384, 176 slots. Gameplay
remains original-three after leaving that review. Cold-boot restores compact
allocation. No gameplay-time CD reads/uploads or full animation cache. Swagger
art remains in source and the disk-only comparison viewer, not resident textures.
VDP2, CRAM, sound RAM and the existing heap are unchanged.

## Visual review

In the original-three artifact, open
animation-review/original-three-walk/comparison.html. It animates original-three,
Swagger and corrected-six side by side; the original timing button selects 8/10.
contact-3x.png/contact-native.png show the exact restored poses. Per-character
moderate/slow GIFs are included; GIF holds round to centiseconds, HTML/game use
exact 60Hz timing. No original pixel was adjusted to smooth 3→1: the strong knee
lift and transition are intentionally restored for this experiment.

Review 3→1, starts/stops, visible stepping versus sliding, reversals/diagonals,
both players independently and action/landing transitions. Three held drawings
cannot provide physical foot IK. Idle/action stance or silhouette changes remain
visible; all logical roots/depth and the native 88px three-piece construction stay
fixed. Physical Saturn and this build's WebRetro testing require user/device tests.
The prior intermittent host emulator shutdown observation remains in Swagger's
historical report; it was not suppressed with gameplay changes.

## Validation

All 13 native build/asset configurations pass, including the original VDP1
fallback, preserved Swagger/six builds and both restored timings. Full gameplay,
input, combat, music and graphics suites pass. Focused tests pin two complete
three-frame cycles at 8/10 ticks, both players independently, idle/fallback
transitions, mirror/root placement, required-only uploads and expansion guards.
ASan/UBSan pass for both timing variants and the compact/expanded bank loader.

Local Yabause ran 1,050 frames per playable/control sequence. Moderate matched
431,782 character pixels; slow matched 432,603, zero mismatches. All three
restored poses and all four idle poses were observed for both actors and facings.
Each run's complete game struct matches the original renderer on every one of
720 compared frames. Original action fallback pixels also match, and resident
texture-area hashes stay constant during gameplay. The 1,600-frame review test
confirms actual allocation/descriptor counters 125→176 and 351,104→427,104 bytes,
old preview pixels and game return. The preserved full preview’s 2,000-frame
regression compares 7,171,200 actor/ground pixels, zero mismatches.

This task's runs exited normally, including emulator shutdown. The historical
Swagger host-shutdown limitation remains documented; it has not been fixed by
altering gameplay. See original-three-validation.json and runtime/*.png. These
checks validate source identity/rendering and the tested input sequence; style,
3→1 landing, held-frame foot sliding and actual hardware performance need review.
