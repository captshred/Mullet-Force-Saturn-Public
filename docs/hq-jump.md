# Stage B — HQ jump and aerial kick review

Baseline: `2ce28c4b0c2e809b22b43aefa659aeb8f62943cc` on
`hq-blowtorch-animation-test`, the completed Stage A native-Yabause-tested build.
New isolated branch: `hq-jump-animation-test`. No merge or protected-branch edit.
Physical Saturn and WebRetro testing remain outstanding.

Build with `bash tools/build-hq-jump.sh` using the native prerequisites in README.
`MF_HQ_JUMP=1` requires the preceding complete torch/jab configuration. Set it to0
with the Stage A helper to restore that exact rendering path and texture bank.
No runtime buttons, gameplay clocks or input states were added.

## Original asset investigation and first comparison

`assets/hq-jump/initial-comparison-{1,4}x.png` was prepared before changing the
renderer: legacy standing, airborne and jump-kick poses for both fighters, plus
actual approved HQ idle references. Later before/after sheets add the new phases.
Native sheets use true pixels; all enlarged previews use nearest-neighbor4×.

The normal jump **does not use AL0..2**. It uses BU/CH11 (takeoff),12 (air) and14
(jump kick), plus NL11,12,14. These six upper and three lower textures cost
22,784 aligned VDP1 bytes. Their anchors remain recorded unchanged in art_data.h.
BU/CH13 and NL13 serve both landing and defeat: these remain loaded for defeat.
BU/CH08 hurt, the other normal frames, every combat bank and all approved art remain.
All original files remain on disc/in source control for the fallback configuration.

AL0/AL1 are56×26, AL2 is64×25. They belong **only to aerial bat assembly** through
`air_lower_for_frame`. That entire existing upper/lower pairing and all its
anchors, art, timing and palette selection are deliberately unchanged. Mixing a
new HQ lower with those old bat uppers would require further character art changes;
this task preserves their previously connected complete assembly instead.
The primary implemented aerial attack is a jump kick, not an aerial punch.

Authoritative HQ references are current `animation-polish/{buck,chuck}-00.png`,
the original-three/knee-lift resident pieces and the current jab/torch banks.
Outdated six-frame and old low-detail costumes were not used as HQ masters.

## New native artwork and assembly

Four native lower poses per fighter: rising knee, compact two-knee tuck,
unfurling descent and a forward flying kick with the other leg bent.
Buck retains silver jacket, armored denim knees and buckle boots. Chuck has his
own bare arms, dark denim vest, ripped knees and boots. No costume recoloring.
An arm/leg guide was edited from the approved reference sheet; guide heads and
standing legs were discarded. Native cleanup registers the pelvis, corrects guide
leg length to the approved scale and removes isolated fragments. The exact
original head/sunglasses piece is reused; no whole-character scaling is performed.
Edited upper/lower pixels are quantized without dithering into the existing shared
HQ palette. Ten losslessly decoded indexed pieces reconstruct the delivered art.

The authoring canvas remains128×96, root(64,92), approved standing height88px.
Review compositions add a16px top margin (160×112, root64,108). Lower poses share
the registered hips; folding legs reduce the visible height naturally at the apex.
The flying boot extends approximately50px from the root at the existing kick's
vertical strike height, rather than inventing a new attack reach or volume.
The torso overlaps the pelvis and draws in front; the exact head overlaps the neck.
Both native silhouettes and assembled emulator pixels are validated.

Two new shared airborne upper textures support ascent, apex and kick. Descent uses
a cropped view of the approved guard torso. Takeoff/landing reuse the approved
head, guard torso, lower body and boots with small coordinated offsets:

- Takeoff: torso/head down2px and forward1px; hips down2px; boots fixed.
- Landing counters6..3: Buck torso/head down3px, Chuck down2px; hips down2px;
  boots fixed. Counters2..1 show the existing guard; restrictions still last6ticks.

Upper and lower row views are permanent indexed references to existing resident
pixels. Cropped view heights stay even: an odd-height31-row experiment failed the
SGL pixel comparison and was replaced by a30-row view. Source knee rows are trimmed
only in that view; no source pixels or approved standing frames are changed.
Five new zero-payload definitions (two torso, two compressed lower, one allocator
tail) follow the Stage A approach; they neither copy pixels nor read disc in play.
There is no streaming cache or new gameplay animation state.

## Phase selection and unchanged physics

`src/hq_jump_config.h` reads existing fields only:

| Phase | Existing state |
|---|---|
| Takeoff | airborne, vz≥1362 (first2 normal update ticks) |
| Ascent | vz>296 after takeoff |
| Apex | −296≤vz≤296 while airborne |
| Descent | vz<−296 |
| Kick | existing non-bat airborne attack counters3..15 |
| Landing | existing positive landing counter, no competing attack |

Kick overrides the jump phase through the original active strike, then returns to
appropriate apex/descent. Hurt, defeat, torch and all bat states retain priority.
No opposite-arm windup, extra attack, combo or recovery penalty was added.
Takeoff renders in the existing first airborne updates: there is no anticipation
delay before launch. The shadow call and scaling function are untouched; its root
stays on the ground while sprite height follows the original `height/256` offset.

`src/game.c`, game.h, input, combat configuration, audio and source assets are
SHA-locked unchanged. The normal flight still launches at1510 fixed units/tick,
subtracts74 gravity each update, lasts42 simulation ticks through ground contact,
and peaks at16170/256 =63.1640625px. Horizontal/depth steering, jump interruptions,
landing restrictions, damage, scoring and co-op remain identical to Stage A.
Six landing counters are confirmed as6,5,4,3,2,1, then0 for both players.

## Exact memory

| Resource | Stage A | Stage B | Delta |
|---|---:|---:|---:|
| VDP1 texture bytes |454,400|456,224|+1,824|
| Free of458,488 |4,088|2,264|−1,824|
| Resident texture payloads |235|236|+1|
| Shared view definitions |9|14|+5|
| Total Jo definitions of255 |244|250|+6|
| CRAM palette banks |8|8|0|

Skip nine obsolete jump/kick resident textures:22,784 bytes.
Load ten new shared-upper/lower pieces:24,608 bytes. Each TGA's dimensions and
32-byte-aligned cost are listed in `assets/hq-jump/manifest.json` and checked
against actual runtime allocation. No approved idle/walk/run/jab/bat/torch/enemy
texture was removed or downgraded. All legacy jump files remain available in the ISO.
The new bank uses the existing256-entry padded HQ palette (raw0 transparency,
indices≤253; Jo adds1). No palette uploads beyond the existing banks are needed.
New renderer state is56 bytes (10 piece IDs, two upper and two compressed-lower IDs).
View metadata consumes already-reserved Jo tables. There are five definitions and
2,264 texture bytes left: future large movesets must not assume free capacity.
VDP2, sound RAM and the audio pipeline remain unchanged; music/SFX are verified
byte-for-byte and never regenerated by this build helper or CI.

## Validation and actual captures

Native build, ISO/source/palette/budget validation and the complete host gameplay
suite run. New bank tests exercise phase boundaries, both fighters/facings, all
phase submissions, stable alias metadata, draw purity and preserved fallback
priorities. Native image tests verify exact heads, grounded boot pixels, seven
visually distinct poses, connected body components and indexed reconstruction.
Existing jump, aerial bat, torch, jab-repeat, dash, combat, co-op and audio tests run.

The controller-only Yabause/libretro HLE test compares the new BIN/CUE to the
published Stage A BIN/CUE:705 complete post-menu gameplay states match, as do input,
dash, bat and jab-state streams. No RAM writes or modified save-state loads are used.
It verifies712,712 visible HQ sprite pixels, all six phases for both actors in both
facings, both42-tick normal flights and the original6-tick landings. Aerial bat
control regions also match (1,099,577 compared screen pixels). Texture VRAM stays
constant throughout play; no texture uploads occur mid-animation.

The preceding real-input torch, repeated-jab and running-bat regression scenarios
were replayed against this build. Their reports accompany the jump report under
`docs/hq-jump-captures/`. Torch art/charge/damage, independent12-tick deliberate
jabs, one-hit running-bat KO and the existing momentum slide remain unchanged.

Actual full-jump, aerial-kick, jump→attack→landing and aerial-bat GIFs for each
fighter are crops from emulator frames, at1× and nearest4×. Transition assertions
verify a real kick followed by landing and guard in the shown source interval.
They show movement relative to the stationary ground shadow. Files named
`docs/hq-jump-captures/*actual*` are real captures; those under `assets/hq-jump/`
are decoded native art sheets or explicitly named offline composite trajectory
references. The latter are not used as evidence of real state transitions.

## Remaining limitations

The aerial bat deliberately retains its original legacy complete artwork; only
normal jump and primary aerial kick receive the HQ design here. There is no
unapproved bat redesign or attempt to fit HQ legs under an incompatible old torso.
Takeoff/landing are restrained piece-offset studies, not separately hand-drawn
full frames; secondary hair/clothing motion is limited. Upper-air poses share two
new balancing upper-body textures to fit memory without touching approved banks.
The existing HUD still overlays upper-lane jumping heads at the top of the screen;
that pre-existing display priority is preserved and masked explicitly in pixel tests.
Crowd occlusion is also excluded from per-sprite pixel comparisons; exact phase and
facing coverage is listed in the report. This does not certify every possible
animation transition or physical Saturn performance. No hardware, SAROO, WebRetro
browser, or audio listening test is claimed. Final artistic approval remains yours.
