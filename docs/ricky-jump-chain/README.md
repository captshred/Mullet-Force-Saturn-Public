# Ricky jump-chain — art and gameplay review candidate

Branch: `feature/ricky-jump-chain-attack`. Starting approved Phase 1 build: `cc10880983bbb761461d7e13cb2cd06a36c55ee1`. No merge or THE ONE tag update. Artwork and hardware/gameplay approval remain pending.

## Review the actual sprites and combat

- [Both native jump poses before/after, also enlarged](art-before-after.png)
- [Production launch → airborne chain → landing animation](jump-sequence.gif)
- [Three phase screenshots](jump-phases.png): [launch](launch.png), [airborne](airborne.png), [landing](landing.png)
- [Punch, standing-chain and jump-chain excerpts from one normal production run](normal-combat-excerpts.gif)
- [Production run counts and capture frames](report.json)

The gameplay previews are selected from a fresh production Yabause HLE boot using only two-player patrol, A and B inputs. The AI naturally selects every attack. There are no NPC state writes, attack-selection overrides, debug teleports, forced healing, or forced jump fixtures in these captures. The combined normal-combat GIF contains three separate excerpts, not an uninterrupted sequence. The selected complete moving jump appears at frames 10494/10512/10534. User hardware/playtesting is still required; HLE checks do not establish hardware performance or subjective balance.

## Artwork and allocation

The authoritative `Ricky_HQ_Animation_Sheet.png` changes only the original two jump source rectangles. The image-generated redesign is fitted into the original pose canvases and converted by `tools/prepare-ricky-art.py`; it is actual indexed sprite artwork, never a gameplay overlay. The source-alpha mask in `art/ricky/jump-chain` is authoring/conversion data and is not loaded by the game. The approved baseline SHA recovers the entire previous source sheet; the two previous TGAs are also retained there for direct comparison.

Sprite IDs 168/169 remain pose indices 16/17. Launch/landing is 48×61 at anchor (22,61); airborne is 64×76 at anchor (28,100). The chain has a compact forward hook so it fits without expanding either allocation. The airborne chain is approximately 18–29 pixels forward of the root; collision reach stays within that visible extent. All other 23 TGAs, shared palette bytes, generated dimensions/anchors and sprite definition counts are byte-exact against Phase 1. The approved red flash still selects base CRAM 2 or warm-red CRAM 3; the RGB555 transform is untouched. Native conversion is deterministic and exercised in make test. Bootstrap explicitly installs NumPy/SciPy for that existing conversion pipeline; the SDK/compiler pins are unchanged.

| Resource | Candidate | Delta |
|---|---:|---:|
| Ricky | 25 definitions; 114,048 texture bytes | 0 |
| Total VDP1 textures | 177 definitions; 371,072 bytes | 0 |
| Protected Buck/Chuck reserve | 49,152 bytes | 0 |
| VDP1 free / discretionary after reserve | 87,416 / 38,264 bytes | 0 |
| VDP2 including protected SDK reservation | 434,176 bytes | 0 |
| Palette allocation and colors | Existing banks; Ricky base 2 / burn 3 | 0 |
| SCSP high-water / free | 485,812 / 38,476 bytes | 0 |
| Per-game persistent CPU state | Two 32-byte Ricky records | +64 bytes |

The normal executable code size changes; the CPU delta above describes added persistent state, not a claim of a 64-byte total binary increase. No new audio sample or channel allocation is introduced; the existing swoosh event is reused. See [sprite-memory.csv](sprite-memory.csv).

## Attack behavior and tuning

All tuning constants are in `src/ricky_config.h`: 75–125 pixel trigger range, 12 windup ticks, 24 flight updates, five active ticks (zero-based flight ticks 18–22), 18 landing recovery ticks, 1 HP, and a 150-tick cooldown. The early flight and final landing update cannot deal chain damage. The visible 64-pixel sprite limits reach to 29 pixels, rather than borrowing the standing chain's 82-pixel collision box. Per-player hit bits prevent adjacent active frames from causing repeated damage.

Facing is committed during windup. At launch, the target's position is captured into bounded horizontal/depth travel; flight then interpolates those endpoints without further target reads. Additional parabolic lift peaks at 12 pixels over the airborne artwork's existing 24-pixel foot elevation. Moving behind Ricky during windup can make him leap in place and miss; he does not reverse the committed facing. Depth-lane dodges, high player jumps and existing invulnerability avoid the hit. Punch/bat/kick windup interruptions, flame contact cancellation, ordinary hurt/death and punishable landing recovery use the existing systems. Interrupted attacks retain their cooldown and cannot resume from a queued flight.

Ricky's walking speed stays at 240 fixed-point units. Standing-chain selection expands from 76 to 82 pixels and lane tolerance from 9 to 12 pixels, reducing repositioning. Punch and standing chain alternate where both are valid (28–36 pixels); jump gets priority when ready in its medium-range opportunity, with an alternative standing chain when the ranges overlap and jump was last. Original punch/standing-chain windup, active damage and recovery timings are preserved. Corporate punk controllers and shared damage/movement/torch functions are protected by source comparisons against the approved Phase 1 build.

## Frequency evidence

A deterministic input-only simulation uses four seeds × 60,000 ticks, or 66.67 simulated minutes. Both players patrol, punch/hold A and jump, with real damage, deaths/recovery, original NPC spawning/class proportions and no forced NPC attacks. The same bot setup runs against the approved baseline:

| Ricky commitments | Approved Phase 1 | Candidate |
|---|---:|---:|
| Punch | 381 | 645 |
| Standing chain | 922 | 724 |
| Jump chain | 0 | 346 |
| Total | 1,303 | 1,715 |

That is about 19.5 → 25.7 commitments per simulated minute across both enemy slots (+31.6%). New attacks are 37.6% punches, 42.2% standing chains, 20.2% jumps. This is bot evidence, not a human difficulty rating: changed combat outcomes also change subsequent encounters. [Candidate statistics](frequency.json), [baseline statistics](frequency-before.json).

The separate 18,000-frame production emulator run records 47 punches, 50 standing chains and 27 jump-chains, reaches 39 KOs without ending Level 1, and supplies the previews. No scripted forcing of enemy selection is used.

## Validation

Passed native stage-default, make check, make test and UBSan current-source combat/world/jump regressions. Coverage includes both players/facings and all camera checkpoints, single-hit latches with invulnerability reset between adjacent collision frames, both players in one strike, visible active timing, depth/height/facing/invulnerability misses, captured trajectory, windup and landing counterplay, all flight-stage flame interruptions/release, death and slot reuse, cooldown retention, and attack variety. Renderer tests assert actual IDs 168/169, fixed anchors, horizontal flipping, elevated shadow and independent warm-red palettes in both slots.

The complete Phase 1 world tests still pass: 1,280 pixels, endpoint, checkpoint floors 0/320/640, 75 KOs without clear, co-op tether/catch-up, offscreen spawning/class mix, retirement, ring-map bounds and explicit Level 2 handoff. Backgrounds, player attacks (including 3 HP bat and charging through damage), flame cadence/contact stun, audio and Level 2 are protected against the approved parent. Historical suites run from their immutable approved source trees rather than loosening their old locks for a new intentional Ricky change.

Current-source sprite conversion round-trip, host suffix reload/failure paths and palette checks pass. [Native Yabause bank reloads](bank-reloads.json): eight real swaps/nine generations, unchanged peak 371,072 bytes, no lost prefix/palette data, followed by 711 live Level 2 ticks. [Repeated cold starts](cold-starts.json): no state or image mismatches over 600 Level 1 state samples / 30 images and 555 aligned Level 2 ticks / 545 images through the physical development X skip.

## Exact Manual Saturn playtest build settings

Workflow: **Manual Saturn playtest build** (`.github/workflows/build.yml`). Use workflow from branch `feature/ricky-jump-chain-attack`. Set `profile` to `stage-default`. Set `source_ref` to the final full pushed commit SHA reported for this branch. Artifact: `mullet-force-stage-default-<resolved SHA>`, retained one day. Use the matching BIN/CUE together.
