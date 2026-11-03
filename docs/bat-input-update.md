> Historical ground-bat/input update. [The current aerial-bat update](aerial-bat-update.md)
> corrects swing direction, updates Chuck's face, and adds fresh airborne combos.

# Physical port 2 fix and baseball bat move

Baseline: d5f70c997cb1d90ce6ebf1866e1d1d5296f0cf99.

## Complete input trace and root cause

The previous adapter incorrectly treated the jo_is_pad2 helper's logical slot 1
as physical connector 2. The previous input mock repeated this assumption and
therefore passed despite the mapping bug. This update replaces that mock-only
layout check with a fixture that executes the pinned SDK's actual poll function.

SDK remains 556d081146211b6a1cfa6591d70f9487d406758b; no SDK patch or alternate
peripheral driver is used. In jo_engine/core.c, jo_core_init calls slInitSystem,
and registers jo_get_inputs_vblank with jo_core_add_vblank_callback. The normal
SGL peripheral initialization and VBlank polling remain enabled even on the title
screen or while Chuck is inactive. The game samples both controllers on every
new VBlank; render-only callbacks cannot consume the same push snapshot twice.

In jo_engine/input.c's SGL branch, jo_get_inputs_vblank copies six 24-byte
PerDigital entries from Smpc_Peripheral into Jo slots 0..5, advances by another
54 Uint32 words, then copies the next six into Jo slots 6..11. Consequently
Smpc_Peripheral[0] -> Jo input 0 and Smpc_Peripheral[15] -> Jo input 6. The pinned
Samples/demo - multitap/main.c explicitly documents slots 0..5 on physical
connector 1 and slots 6..11 on connector 2. Headers' jo_is_pad2_* helpers refer
to logical slot 1 and must not be used for physical connector assignment here.

src/input.c now explicitly maps game physical-port arguments 0/1 to SDK slots
0/6. It records the raw device ID, active-low data and active-low push masks,
checks connection, and accepts regular digital pads and Nights/3D pads in their
D-pad mode. Mice, unknown devices and disconnected entries cannot produce game
buttons. jo_is_input_key_pressed reads active-low data; jo_is_input_key_down
reads active-low push. No low-level initialization or synthetic Start fallback
is added. Physical connectors remain assigned to Buck/Chuck respectively.

P2 Start is processed before the started/paused/hit-stop early returns and
before any per-player active checks. It can now start the session and join
Chuck even from the title, without any P1 button. Joining an existing session
changes neither the existing pause state nor score/barrels/enemies/Buck.
Chuck spawns near Buck within the current visible viewport, with a small depth
offset and the existing 120-tick protection. The first protected frames are
shown continuously so join is immediately visible rather than starting hidden
on an invulnerability blink. Active Chuck renders from his own state and palette.
P2 Start never toggles pause. P1 Start still owns pause/resume. An absent P2 is
ignored; single-player remains valid. A missing P1 does not prevent P2 joining.

C on P1 toggles diagnostics, hidden initially: both physical port labels, mapped
SDK slots, device IDs/types, supported connection flags, raw data/push masks,
translated held/edge masks, all twelve slot IDs, and Chuck's active/position/bat
state. These are the actual most recent input samples, not forced debug input.

## Move and timing

Both players: tap the currently facing direction twice, then A. A may accompany
the second press. Release forward between taps. First tap must already be
forward; turning with a backward press does not also count as the first tap.
The direction must stay consistent; opposite/both-direction inputs, facing
changes, jumping, hurt, defeat or another active move cancel the gesture.

src/combat_config.h configures the fixed 60 Hz windows: 250ms between taps
(15 ticks) and 180ms after tap two (rounded up to 11 ticks, about 183ms), with
inclusive endpoints. Each player independently tracks direction, tap window,
A window and previous directional held state. SDK direction edges plus held
transition validation prevent a hold/repeated render snapshot from counting as
two taps. The recognized gesture is consumed on activation; held A cannot
retrigger it. Grounded bat takes priority over punch; airborne A remains kick.
Inputs during restrained hit-stop can buffer A, while gesture windows continue
on the input tick clock. Pause freezes gameplay/input windows as before.

The bat uses seven newly authored upper-body/weapon poses for EACH costume:
draw, coil, accelerate, contact, sweep, follow-through, recovery. Torso and
shoulder rotation drive separately posed elbows and two hands on one handle
axis. Buck retains silver sleeves; Chuck retains bare arms/black denim. The
wood bat has a knob, wrapped handle, tapered barrel, restrained active trail,
and a coherent shoulder-to-forward-to-downward arc; it disappears on recovery.
This is not a bat pasted on a punch frame. Feet stay planted on the existing
native anchor, with a shared lower-body texture. This saves texture memory
without scaling or discarding opaque detail. Upper/lower anchors mirror together.
The contact sheet is reconstructed from the actual exported textures and shows
both characters in both directions; it is not an emulator capture.

Damage only occurs on attack ticks 12..17. Bat damage 2 versus punch 1; reach
78 versus punch 52 pixels (1.5x); knockback 1350 versus 850 fixed-point units.
Recovery ends at tick 36 versus punch tick 24. Ground axes remain locked during
the swing. Existing facing, depth, vertical overlap and per-player target masks
apply. One swing can hit all three barrels and both enemies once each, without
friendly fire. Simultaneous killing blows award enemy defeat score once. Impact
spark/hit-stop and the established quieter, three-port rate-limited SFX remain
in use. No music gain, sequence, bank or native transport change is made.

## Validation and limitations

Host tests execute the real pinned SGL polling body with synthetic connector
buffers, then the actual adapter and join logic. Fixtures cover physical port 2
at peripheral index 15/Jo slot 6, a misleading slot-1 Start, absent/unsupported
controllers, supported 3D pad ID, active-low held/edge masks, title/inactive join,
and no P1 input. Gameplay tests cover both-facing/both-player combos, window
boundaries/expiry, simultaneous second tap+A, held/repeated edges, opposite
inputs, air kicks, ordinary punches, planted stance, all seven bat poses,
hit-stop buffering, depth/facing rejection, active-only damage, stronger recoil,
five targets hit once, and simultaneous bats/one defeat score. Legacy co-op,
barrels, recovery, enemy and native-music transport tests remain in the suite.

Native build and ISO checks validate exact exported payloads, source identity,
all palettes/anchors, both mirrored bat assemblies, no drawing-bound clipping,
and hardware memory regions. Texture use including HUD is 448048/458488 bytes
(67 TGA textures plus two runtime HUD textures; four CRAM palettes). The bat
layers add draw commands, not sound ports. Sound RAM and voice budgets are
unchanged from the preceding co-op build: 283748/524288 bytes reserved/payload;
22 conservative music+release slots plus 3 SFX + 3 retiring tails =28/32.

No Saturn emulator executable or BIOS is available in this workspace. No
actual two-controller emulator test, audio audition or hardware test was
performed. The synthetic peripheral fixture proves code mapping and logic;
it does not simulate the physical SMPC, emulator device configuration, display
output or SCSP playback. Use C diagnostics for a subsequent device playtest.
The compiled artifact uses the existing MODE1/2048 BIN/CUE packaging unchanged.
