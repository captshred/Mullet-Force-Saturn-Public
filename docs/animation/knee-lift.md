# Frame1 leading-knee refinement, Timing B

Branch walk-knee-lift-test from a44464f. Only walking frame 1 changes.
Timing B remains 10/10/10 ticks at 60Hz, 30-tick loop. MF_WALK_KNEE_LIFT=1 requires
MF_ORIGINAL_THREE_WALK=1 and slow timing 1; slow defaults 1 when this flag is set.
The downloadable knee-lift build enables these options automatically.

The small leading-leg edit lifts the front knee about 2–3 native pixels and bends
the shin/ankle, with the front sole at row 88 instead of 91. The rear sole remains
at 91. This is a localized anatomical edit, not translation of an entire leg.
Only the front-leg polygon below the hip is imported from the edited guide;
all upper pixels, the hip/pelvis core and every pixel left of x64 stay unchanged.
Exact mask: x72..99,y56..57; x64..99,y58..79; x64..101,y80..91.
Frames 2/3 are exact PNG copies from the approved source; idle assets are untouched.
All colors map to the same indexed palette. Canvas 128×96, root (64,92), opaque
height 88, three-piece boundaries, dimensions, padded widths and offsets stay fixed.

Four existing indexed TGA pieces (AB11/12, AC11/12) are replaced at disc staging
ONLY in this build. No additional texture is uploaded and no new resident frame,
state, palette, draw call, CD read during gameplay, or animation cache is added.
The corrected polished six-frame bank and idle bank do not reference those four
IDs; they remain unchanged. The optional original-prototype review also shows
its frame 1 with the same refinement, since it shares these exact resources.
All original source TGAs/PNGs remain byte-identical in their existing directories
and are still used by normal builds with the refinement flag disabled.

## Play and review files

Cold-boot matching BIN/CUE. Start leaves the gallery; Start again plays. Port 2
Start joins Chuck. Controls and all movement/physics/combat/hitbox code are
unchanged. Original action art remains the fallback. No dash/new content.

Open animation-review/knee-lift/before-after-native.png or before-after-6x.png.
The adjacent buck-cycle.gif/chuck-cycle.gif show all 3 poses at Timing B (GIF
centiseconds alternate 170/160/170ms to preserve the 0.500s cycle). PNGs 00 are
adjusted; PNGs 01/02 are unchanged. The edit guide is provenance only: its upper
bodies/background effects are discarded and never used in the game.

VDP1 stays 351,104 allocated / 458,488 budget, free 107,384, 125 sprite slots.
Opening the old full review once raises this to 427,104 allocated, free 31,384,
176 slots, exactly as before. Palette/VDP2/work RAM and playback state are unchanged.

Review front-foot clearance, planted rear foot, 1→2 and 3→1, both facings, starting/
stopping, and action transitions. Human visual approval and WebRetro/physical
Saturn tests remain separate from automated pixel checks. No other pose is tuned.

## Validation results

All 14 native build/asset configurations pass, including original VDP1 fallback,
Swagger, both restored timings and this refinement. Full gameplay/input/combat/
movement/music tests pass, as do Timing B presentation and bank-loader ASan/UBSan
checks. The wrong Timing A/refinement combination is rejected before building.

Local Yabause v0.9.15/8926b0c (software/interpreter, HLE BIOS, 1 thread, no RAM
cartridge) completed 1,050 frames per playable/control input sequence. **430,830
character pixels** match the edited native references with zero mismatches; all
three poses and both facings were observed for each fighter. The complete game
struct matches the control on every one of 720 compared frames; original action
fallback regions also match. Texture-area hashes stay constant during gameplay.
The baseline build with overrides disabled still matches 432,603 pixels exactly.

The 1,600-frame optional-review test confirms actual allocation and descriptor
counts 125→176 and 351,104→427,104 bytes, unchanged preview idle pixels, game return
and stable expanded textures. Runs exited normally. Runtime image/BSS end remains
0x060983C4. No runtime C/header, game, timing, input, original art or anchor file
changed relative to a44464f. The frame 2/3 byte hashes and strict upper/pelvis/rear
pixel locks, palette/header/layout equality, mirrored reconstruction and GIF
colors are checked independently. See knee-lift-validation.json and runtime/*.png.
