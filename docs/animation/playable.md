# Playable high-detail movement test

Baseline e7e41a0, branch character-animation-upgrade. No artwork changes.
Current timing test: playable high-detail walk at 75% playback speed; movement
and idle breathing unchanged.

Cold-boot the matching mullet-force.cue/BIN in the **playable-animation** artifact.
Start leaves the gallery for the title; press Start again to play. Physical port2
Start joins Chuck. The playable build enables high-detail idle/walk automatically.
Down from gallery still opens the unchanged animation review; B opens parallax.
C in gameplay shows diagnostics including selected poses and total VDP1 bytes.
All original controls, pause and simulation timing remain intact.

The separate **animation-polish** artifact is the original-gameplay-renderer
control: gallery/preview are the same, but gameplay uses the original sprites.
No debug button combination intercepts attacks, jumps, movement or pause.

## Allocation and renderer contract

MF_PLAYABLE_ANIMATION=1 requires MF_ANIMATION_PREVIEW=1, which requires the
VDP2 street and gallery. Default=0 retains the original gameplay renderer.
The gameplay renderer borrows the preview loader's existing resource IDs and
palette bank 7, rather than loading another bank. Both artifacts keep the entire
comparison/gallery set resident. **VDP1 427,104  / 458,488 bytes; free 31,384**.
Indexed texture/palette bytes and three-piece crop mappings match e7e41a0 exactly.
176 sprite slots, eight 512-byte palette banks, no new VDP2 allocations.
No per-tick/frame CD reads, texture uploads, heap allocation or animation cache.

The game remains authoritative for movement and six-pose cadence:
4+((player.walk%40)*3)/20 selects the corrected walking bank at 75% playback
speed: a 40-tick loop instead of 30, with 7/7/6/7/7/6-tick frame holds. Direction changes do not
restart it. Clamping at a world edge still animates according to the existing
moving flag, exactly as the original renderer did. Independent idle clocks
advance only on actual simulation ticks, freeze during pause/hitstop and reset
to the approved idle starting pose on stopping or returning from an action.
The actual approved idle bank contains FOUR poses (Buck 24/16/24/16 ticks;
Chuck 30/18/24/18), despite the request's description of three. All are preserved.

Inactive/defeated, hurt, attack, jump/takeoff, landing and torch states use the
complete existing renderer. Existing bat upper/lower, torch/flames, airborne
legs, effects, invulnerability flashing and shadows remain unchanged. The
high-detail renderer uses the same screen root (world x−camera, ground y),
logical sole y=92, ground-based depth and hardware mirroring of padded pieces.
The previously validated SGL unit-scale raster convention (+1,+1) is retained
for both banks. All three new pieces use the same actor depth, preserving depth
ordering with enemies, drums and the other player.

## Review limitations

Only idle and walk have high-detail art. Original attack/jump/hurt/landing poses
can change silhouette/size and guard posture abruptly, but keep the same logical
root. Stopping selects idle immediately; gallery-only guard bridges do not delay
input or the gameplay pose. Discrete frame holds and existing edge-walking
behavior can still show foot sliding. No per-pixel foot IK or speed changes are
attempted. The accepted second wide contact is untouched. No Corporate Punk
assets, enemy changes, generated artwork or additional frames are included.

Review: both players and both facings; all six poses/6→1; diagonal movement;
start/stop and direction reversal; pause/hitstop; attacking, jumping, landing,
bat and torch transitions; camera/depth and overlap with enemies/drums.
Physical Saturn and this candidate's WebRetro testing require device/user tests.

## 75% walk playback timing test

Only the playable high-detail walk selector is slowed. Game walk counters,
movement, physics, combat timing, hitboxes, idle breathing and source artwork
are unchanged. The gallery and original-renderer control retain their prior
cadence as references. Revert the timing-test commit to restore full playback.
The tests pin all six holds over two full loops, including the wrap, independent
fighters, counter arithmetic, and unchanged idle/fallback/simulation behavior.
Earlier measurements below describe the original playable integration; current
timing-test results are in walk-speed-validation.json.

## Automated validation

All nine native build/asset configurations pass: VDP1 with/without gallery,
VDP2 without gallery, gallery, parallax, animation, animation+parallax, playable
with/without parallax. Original movement/combat/co-op/bat/air-bat/torch, input,
audio and graphics tests pass. Focused presentation tests cover independent
clocks, six-frame order, axis/facing changes, fallback into/out of actions,
unchanged simulation/root data, shared resource IDs, mirror crop origins and
no additional loading. Preview and playable ASan/UBSan checks pass.

Combined playable resident image/BSS ends at **0x06098034**, compared with
e7e41a0’s 0x06097CF4: **832 bytes** additional code/metadata/state/alignment.
Only 16 bytes are persistent gameplay presentation state (two idle clocks and
two prior modes); no CPU animation frame bank is added. At most two additional
VDP1 draw commands are needed when both players use three pieces instead of
the original two. This is not a physical Saturn performance measurement.
VDP2 remains 123,008 layer bytes / 385,152 reserved, no extra palettes or sound RAM.

The optional runtime test uses an existing libretro Yabause core and its standard
save-state API to **read** game/clock data and hash the resident texture area.
It never changes game state or injects custom game hooks. Both builds receive
the same actual two-controller input sequence. Exact gameplay-state comparison
checks simulation independence; native PNG/RGB565 comparisons check roots,
facings and animation selection through the SGL display pipeline. Occluded
pixels/UI panels are excluded and counted explicitly, rather than treated as
verified character pixels. Original action regions are compared directly
against the control build. Physical Saturn and new WebRetro tests are pending.

Local libretro Yabause completed 1,050 frames per build. **450,339
high-detail character pixels** (all four idle poses/six walk poses for both
fighters; both facings) match the approved source with zero mismatches.
**828,471 pixels** in original fallback regions also
match the control, covering punch, jump, kick, bat, torch, hurt and landing.
The complete game struct matches the original renderer on every one of
**720 compared frames**. A resident VDP1 texture-area
FNV-1a hash stays constant through movement/combat/pause in both runs.
See playable-validation.json and playable-captures/*.png for measured evidence.
This validates this input sequence and local core; visual feel, foot sliding
and physical hardware performance still need human/device testing.
