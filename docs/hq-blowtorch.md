# Stage A — HQ blowtorch review

Verification clarification: the implementation commit subject used “hardware-tested”
in error. Testing was native Yabause/libretro only; no physical Saturn was tested.

Parent: `c50d7146f38a343d5f949aadb72690864ec373fb`, completed jab cohesion,
6-tick fresh-edge buffer, 12-tick deliberate jab repeat, shorter bat playback.
Branch: `hq-blowtorch-animation-test`. No merge or jump work.

Build: `bash tools/build-hq-torch.sh` (native tool prerequisites in README).
`MF_HQ_TORCH=1` opts into the visual replacement and requires the jab milestone.
`MF_HQ_TORCH=0` retains the complete preceding renderer/bank. Both builds keep
all original torch assets on disc and in source control. No gameplay-time I/O.
The helper explicitly preserves committed music/SFX; no music generator runs.

## Required initial comparison

`assets/hq-torch/initial-comparison-{1,4}x.png` shows all six legacy torch poses,
the actual current HQ idle and jab references, and the original four flames.
Legacy TU0..2 / TC0..2 are 48×55, 56×55, 40×60 indexed upper bodies. They used
old normal lower bodies in gameplay, not the approved HQ actors.
Their ground anchors are (18,87), (14,87), (17,87). FL0..3, EM0..1, CHARGE,
all legacy anchors, indexed palettes and files remain byte-identical.

Current HQ actors use 128×96 authoring canvases, root (64,92), visible height88.
The current playable idle is `animation-polish/{buck,chuck}-00.png` assembled
from shared gallery/polish pieces. Walk is original three-pose Timing B with
knee-lift overrides, not old gallery walk or corrected six-frame references.
Jab uses the approved attack-sequence bank plus the preceding coordinated offsets.

## Art and reused pieces

A six-pose arm/tool guide was edited from the approved HQ references, then worked
at native resolution. The guide's heads and legs are not used. Original heads,
hair, sunglasses and lower bodies remain exact indexed source pixels.
The replacement is confined to y24..47 torso/arms and the overlapping hand/tool
beside the pelvis through y55. The firing nozzle was cleaned and registered to
native (98,52), exactly root+(34,-40), matching the existing FL origin.
No new flame design, reach or combat geometry is used.

Buck keeps his silver jacket and gloves; Chuck uses his own bare arms and denim
vest. Equip holds the compact green cylinder closer, fire braces it forward,
and put-away lowers it. Existing native palettes quantize the edited body pixels
without dithering. Small trigger/nozzle highlights are deliberately pixel clusters.
The tool is compact; minute trigger/finger detail and smoothly articulated inbetweens
remain limited at 88px. This is a review pose upgrade, not final manual cleanup.

Six new upper-body textures use the existing HQ palette. Six small cylinder
masks use existing Corporate Punk green colors in the enemy palette, **not** a
new palette bank. The selected bank is the normal enemy palette, so fire-flash
selection cannot recolor the carried tool. All indexed TGAs use raw0 transparency,
256-entry padded palettes, raw indices≤253 and Jo's index+1 convention.

HQ head pieces and boot pieces reuse current IDs. For the middle lower-body
portion, eight persistent texture-definition views select rows48..79 from existing
idle/three-walk middle textures. They reference existing VDP1 pixels, with native
horizontal mirroring; there is no copied lower-body bank or dynamic texture cache.
Walking uses the unchanged Timing B 10-tick frame hold; torch movement remains slow.
Shoulders/head do not inherit a walking bob that could open the waist seam.

### Pinned SGL view registration

SGL resolves texture definitions after submission. An initial temporary-definition
experiment produced repeated torso pixels and was rejected by emulator pixel checks.
The delivered version uses stable definitions throughout rendering. Jo's supported
image registration receives a zero-payload 8×0 image, then the definition/picture
metadata is immediately replaced with a checked resident row range before any draw.
No zero-height definition is rendered, no DMA is requested, and no allocator source
files are changed. This relies on the inspected pinned Jo/SGL implementation.
A ninth metadata-only tail view points to the last real texture so Jo's next upload
cursor remains at the real bank end. No uploads occur during gameplay.
Unit tests check definition stability and renderer purity. Runtime pixel tests check
the actual deferred command path; both VRAM contents and gameplay remain stable.
The left-facing flame explicitly restores flip after the HQ helper resets draw state.

## Exact memory

| Resource | Previous jab build | HQ torch build | Change |
|---|---:|---:|---:|
| VDP1 texture bytes | 457,632 | 454,400 | −3,232 |
| Free of 458,488 | 856 | 4,088 | +3,232 |
| Resident texture payloads | 229 | 235 | +6 |
| Row/tail view definitions | 0 | 9 | +9 |
| Total Jo texture definitions | 229 | 244 | +15 |
| Palette banks | 8 | 8 | 0 |

Skip six obsolete resident TU/TC textures: **16,320 aligned bytes**.
Load twelve replacement upper/fuel pieces: **13,088 aligned bytes**.
The six legacy files remain in the ISO for fallback, but are not uploaded in HQ mode.
Nine metadata views consume **zero additional VDP1 texture bytes** and no new
texture payloads. Their metadata occupies already-reserved Jo tables (255 entries).
New renderer state is 84 bytes (12 IDs, 8 lower-view IDs, palette ID).
Per visible torch actor: head + lower view + boots + upper + fuel, plus original
flame when firing; no particles added. VDP2 and sound RAM are unchanged.
The remaining texture and definition margin is still small; no extra movesets fit
by assumption. No detail was removed from approved combat/enemy banks.

## Validation and previews

`make test` includes a new pinned-SGL bank fixture for both fighters, three tool
states, all30 walking ticks, both facings, no draw-time uploads, unchanged game
state and stable definitions. Existing torch tests retain the exact60-input-tick
charge, fresh-input safety, immediate release, interruption/priority, slow locked
strafe, independent co-op, direct/burn/barrel/score and shared sound-bus coverage.
All existing jab/bat/dash/jump/co-op/audio tests run unchanged.

Native build + `make check` validate exact ISO payloads, indexed conversion,
source fingerprint, old assets, unchanged audio, source locks and actual new budget.
The new packer is deterministic from the native PNGs and uses existing palettes.
`preserved-sha256.json` locks the prior gameplay, input, audio, sprites and relevant
configuration. No simulation or audio source was edited.

Real Yabause/libretro HLE controller captures compare to the published c50d714
BIN/CUE. They do not write game RAM or load edited saves. See
`docs/hq-torch-captures/torch-validation.json` for actual pixel/phase coverage,
charge activation and705 post-menu gameplay states; all prefix and dash/bat/jab
state streams match the control. Both actors fire together and strafe with locked
opposite facing; all three lower poses are checked against decoded source pixels.
The original equip state has no live dwell: tick60 transitions directly to fire.
Equip GIFs are therefore art composites, not invented extra gameplay time.

The previous real-input repeated-jab and dash/bat/KO scenarios were also replayed
against the new build; their reports are included. Actual captures are named
`docs/hq-torch-captures/actual-*`; all `assets/hq-torch/*.gif` files are generated
native composites. Those composites include equip, fire, put-away, strafe and
both-facing sheets in1× and nearest-neighbor4×.

Physical Saturn, SAROO and WebRetro/browser testing have not been performed here.
Native Yabause does not establish hardware frame rate or audio listening quality.
Runtime torch captures cover Buck right and Chuck left; complementary facings and
equip are covered by native/mocked validation, not claimed as captured gameplay.
Jump/aerial artwork remains the previous fallback for Stage B.
