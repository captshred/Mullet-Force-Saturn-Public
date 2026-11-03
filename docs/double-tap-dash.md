# Double-tap dash movement prototype

Parent: validated Corporate Punk soft-lighting commit094c21e25f4a0f2d85a72054229b115822b316fc. Branch:double-tap-dash-test. No merges. All approved graphics/palettes and legacy combat assets remain unchanged.

## Controls and priority

Tap Left, release horizontal input for at least one sampled60Hz tick, then press Left again within12 ticks (200ms) of the first press; hold the second press to continue. Right works identically. The12-tick boundary is inclusive;13 expires. Both a real edge and the held direction are required; repeated edge flags during a continuous hold cannot trigger. Both players have independent state, and separate game copies do not share detector state. Opposite directions cannot complete a pair; ambiguous Left+Right clears intent.

Release horizontal input or reverse to cancel immediately. Reversal can prime a fresh pair in the new direction, but never instantly reverses a dash. Vertical steering is supported with the original diagonal normalization and depth factor. Pure vertical input ends a dash and uses ordinary walking speed.

A/B action edges and buffered action edges cancel dash before movement. The unchanged gesture/torch/attack logic still chooses punch, bat or jump. In particular forward-forward+A on the second tap immediately performs the old planted bat, with no intervening boosted movement. A shortly after dash activation can still select bat within its original window. The old bat tap window remains15 ticks and its A window remains unchanged, so a13–15-tick pair may arm bat without dash. Dash does not change facing-relative bat recognition, add automatic attacks, bonuses, invincibility, stamina or cooldown.

Hurt, attacks, airborne/landing, charging/firing/holstering torch, inactive/dead/disconnected players and menus cannot arm dash. They clear pending taps and require a fresh horizontal-neutral sample when eligible again, preventing stale held directions on recovery/landing/resume. Spawn/join state resets only the relevant player's detector. Existing hit-stop freezes an already held dash and its animation; release/actions still cancel it. New taps during hit-stop are discarded instead of buffered into automatic movement. Pause clears dash. Existing walk/air steering/combat movement permissions and torch behavior are preserved.

## Tuning and exact speed

`src/dash_config.h` contains the12-tick window, speed numerator/denominator, and animation ratio. Preset B(default when enabled) uses17/10; A uses15/10. The existing walking velocity remains390/256 pixels per tick (1.5234375px/tick,91.40625px/s). B is663/256 (2.58984375px/tick,155.390625px/s); A is585/256 (2.28515625px/tick,137.109375px/s). Only eligible grounded dash movement uses this integer ratio, before the original181/256 diagonal normalization and3/4 depth movement factor. Diagonal ratios have ordinary integer rounding. Simulation remains60Hz; no floating point is introduced.

The existing three approved walking poses are a temporary visual placeholder. Normal walk remains exactly10/10/10 ticks. During dash a separate phase advances7 units per tick against5 units per normal tick, giving exactly1.4x average phase speed without integer frame-hold rounding drift. The150-unit cycle produces the same three poses at roughly7.14 ticks each. Idle breathing and original attack/jump/hurt/bat/torch fallbacks are untouched. No new sprite, pose or texture is loaded.

Dash uses the existing world clamps x26–614/y168–229, shared camera tether and camera0–320. The parent has no physical body collision against players/enemies/drums and no wall collision map; this prototype preserves that rule, rather than inventing dash-only blocking. Enemy attack/hurt collision and damage remain active during dash. There is no new collision immunity or extra reach.

## Build and memory

Primary test: `MF_DASH_ENABLED=1 MF_DASH_PRESET=B` alongside the approved `MF_CORPORATE_LIGHTING=1 MF_CORPORATE_REFINED=1 MF_CORPORATE_PUNK=1 MF_WALK_KNEE_LIFT=1 MF_ORIGINAL_THREE_WALK=1 MF_ORIGINAL_WALK_SLOW=1 MF_PLAYABLE_ANIMATION=1 MF_ANIMATION_PREVIEW=1 MF_SPRITE_GALLERY=1 MF_VDP2_STREET=1 MF_PARALLAX_DEMO=1 make native`. Change only `MF_DASH_PRESET=A` for the slower option. CI publishes separate clearly labeled A/B BIN/CUE artifacts. Disable `MF_DASH_ENABLED` for the original movement configuration; it defaults0 for inherited builds, and the enabled preset defaultsB. Builder validates the approved graphics configuration.

Two7-word dash-state records add56 bytes of per-game work RAM. They are appended after the original game state so all original player/combat offsets stay intact. No heap use exists in movement, no per-frame CD reads, no new renderer submissions and no VDP1/CRAM allocation. Expected approved boot allocation remains362848 bytes /95640 free /135 slots (458488-byte texture budget), shared enemy/player textures as before. Optional old gallery expansion remains438848 allocated/19640 free/186 slots. Eight palette banks remain4096 bytes. These allocation figures are checked in actual runtime memory when emulator results are reported.

## Validation scope

Focused tests cover both players/facings, inclusive/expired windows, release/held-edge/chord guards, diagonals, independent games, reversal/release, jump/kick/landing, same-tick/delayed bat priority, original bat window, punch/torch, damage, hit-stop, menu/pause/resume/disconnect/respawn and original world/tether bounds, for both presets. A separate animation test checks exact rational phase and unchanged normal walk/idle/fallback IDs. Existing gameplay tests and additional dash-enabled bat/air-bat/combat/co-op/torch regressions are run. Runtime tracing preserves the original state prefix and captures the new dash suffix separately; old validated control builds remain readable.

Emulator results and limitations are recorded with the review artifacts. No physical Saturn or WebRetro compatibility/performance claim is made without actual testing. Proper running art and dash attacks remain deferred; the walk reuse and its phase transition are intentionally temporary.


## Completed local results

Both preset-native builds and their disc/asset/music checks pass. All existing tests pass with dash disabled; the focused A/B, rational-animation tests and the existing bat/air-bat/combat/co-op/torch suites also pass with dash enabled. All approved asset directories have zero changes against094c21e.

Each controller-driven local Yabause run covered800 frames for the new build and the approved lighting control. The57 pre-dash gameplay-state prefixes were byte-identical, and28 ordinary movement samples remained390/256 pixels per tick. Preset B measured663/256 on169 eligible movement samples and matched204593 native player pixels; preset A measured585/256 on169 samples and matched205733 pixels. Both saw all three walk poses during dash for both players, in both facings, with zero pixel mismatches. Runtime bat, jump, landing and slow-tap checks passed. Original graphics texture bytes hash identically to the approved lighting control and remain stable during gameplay. Actual loaded allocation is362848 bytes/135 slots in both presets.

JSON reports and actual captures are in docs/dash-captures. The core SHA and HLE/software/interpreter/read-only method are recorded; no game RAM writes were used. Physical Saturn and WebRetro playtests remain outstanding. These tests prove input/physics/pixel behavior under the tested scenarios, not final dash game feel or hardware frame pacing.
