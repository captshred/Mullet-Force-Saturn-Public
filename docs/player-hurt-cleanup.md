# Chuck run cleanup and HQ player hurt review

Branch: `chuck-run-cleanup-player-hurt`, from validated `53861e0a9591697e0ca41dcc4ea0e9d3fae1f101` (`corporate-punk-hq-combat-test`). No merges or protected-branch changes.

## Exact run correction

Inspection found **baked pixels**, not a second draw call or walking overlay. Chuck's third pose retained a large obsolete forward-swinging arm in addition to the correct rear bat arm and free hand. The pixels span RN18 (top) and RN19 (middle). The same upper is also packed into the running-bat preparation bank at CA51/52, exclusively used by Chuck's phase-2 preparation pose.

Only **386 native pixel coordinates** in that obsolete arm region change. The newly exposed vest and small forearm join are restored from the authoritative existing Chuck poses 1/2. No running concept-sheet sprites, generated replacement Chuck, entire pose redraw or leg edit was used. The original native PNGs/TGAs remain immutable; the opt-in build loads RC0/1 in place of RN18/19 and CT0/1 in place of CA51/52. These have **identical dimensions, palette headers and aligned memory cost** to the originals. Every raw pixel outside the edit mask is unchanged. The corrected derivative is `assets/player-hurt/chuck-run-2-clean.png`.

Chuck's other three running poses, all legs, head, hair and sunglasses remain unchanged. His free hand and the existing rear glove/grip remain in place. All four `rbv_hands` anchors, carry texture, bat length/angle and animation mappings remain unchanged. The same rear hand holds the bat in all four frames, including phases 3/4 and mirrored playback. The prep-bank correction prevents the same arm returning when A starts the swing. Buck's entire run art, shared carry weapon, swing weapon data and all Buck preparation resources remain byte-for-byte unchanged.

The pink diagnostic is review-only and never copied to the disc. Native/4× sheets and run GIFs compare the real before/after sources, not the unapproved running concept.

## HQ hurt sequence

Only the supplied concept's bottom hurt art direction informed the new reactions. An internal edit guide starts from the approved actual 88px native idle masters: Buck's silver jacket/blond mullet and Chuck's sleeveless vest/auburn mullet/blue glasses. The guide is reference material; exports are cleaned, registered native indexed artwork. Shared palette conversion uses nearest-color mapping with binary alpha, no dithering or runtime scaling.

Existing player hurt is `p->hurt=12`, independent of defeat. The new pure selector maps:

| Existing hurt counter | Art | Simulation ticks |
|---|---|---:|
| 12–9 | initial backward head/shoulder recoil | 4 |
| 8–5 | pained face, clutching ribs/abdomen, knee compression | 4 |
| 4–1 | hunched/gimpy recovery | 4 |
| 0 | original gameplay/guard path | unchanged |

Normal hit-stop freezes this counter exactly as before. Pose 3 does not kneel, touch the floor or become a death frame. Root remains **(64,92)** on a **128×96** canvas, with registered soles at y92. Natural hair/recoil or hunch changes the opaque bounding height without changing native scale. Sunglasses remain; native mouth shape, jaw angle and posture carry the small facial reaction.

The initial recoil has its own clean, complete standing lower body. Runtime testing caught that the original idle middle strip includes legs down to y80 and part of the guard hand; merely reusing the boot strip left missing legs, and a wholesale lower-band copy retained a detached hand fragment. These were corrected in the actual native source and assembly. Pain/recovery share one lower body per fighter, including the same hanging wrist/hand; upper and lower seams reconstruct the reviewed PNGs exactly.

For readability, the new hurt poses remain visible throughout the existing 12-tick hurt interval. **Invulnerability remains exactly 60 ticks and hit detection is unchanged**; the original blink resumes on the same remaining invulnerability clock after hurt. No extra recovery dwell, physics/input changes, new combat state, defeat pose, sound event or animation-driven damage was added. Players with health 0 bypass the new path and retain the approved defeat behavior.

## Memory and loading

Measured baseline: **422,208 / 458,488 bytes**, **246/255 definitions**.

- Four run/preparation replacements cost **zero additional bytes or definitions**.
- Six upper reactions and four lower pieces: **31,584 aligned bytes, ten shared textures**. Pain/recovery lower pieces are reused per fighter.
- Obsolete BU08/CH08 uploads: **5,120 bytes and two definitions replaced**. Their legacy hurt and jab-windup uses are fully covered by HQ hurt and the already-approved HQ jab renderer in this required full profile. Files remain in source/on disc; feature-off builds load them normally. No normal lower, attack, bat, jump, defeat, torch, player or enemy bank was discarded.
- **Final measured: 448,672 bytes used; 9,816 free; 254/255 definitions** (240 payloads + 14 existing views). Net increase: **26,464 bytes / eight definitions**. One definition remains free.
- Exact existing gallery palette; **zero new palette/CRAM banks**. Hardware mirroring and 8-pixel widths/32-byte allocator alignment retained. Sound RAM remains **420,000/524,288 bytes**.

Jo's root directory entry budget was exceeded by the initial flat layout (257 entries). Hurt textures now live in `HQHURT/`; only the two RC files are added at root and two CT files under the existing `COMBAT/`. The root is within the 256-entry budget. No music conversion, audio regeneration, per-frame CD reads, texture streaming or animation cache. All new textures load once at startup.

## Validation and captures

`make check` / `make test` and the full native build pass. New bank tests cover exact four-tick phases, both fighters/facings, death exclusion, one-time uploads, capacity failure and Chuck-only resource routing. Source locks preserve all original artwork/configuration and all simulation/audio files. Every Buck run file and original carry/hand metadata is checked byte-for-byte. Original run and preparation bytes outside the localized mask are checked directly.

Three controller-driven Yabause scenarios compare **2,115 active-period gameplay snapshots** plus dash/jab/running-bat traces with the downloaded approved baseline. Native pixel checks cover both hurt cycles and **all sixteen actor × four-run-frame × facing combinations**, plus seventeen carried-run-to-swing samples. Across the scenarios, **418,913 native sprite pixels** match their expected source assemblies and **69,538,538 pixels outside the intended changed regions** match the baseline. Full CRAM matches the baseline; runtime allocation counters and stable texture VRAM hashes confirm budget and no gameplay uploads.

The initial run test incorrectly expected the complete running stride during bat preparation; the existing approved prep intentionally uses a planted lower body. The test now reconstructs that actual preparation assembly and verifies it, without changing the approved attack sequence or physics. P2 is moved forward using real controller input for a clear damage capture rather than hiding behind P1. No emulated RAM writes or injected damage events.

Actual SCSP samples confirm Jab, CONNECT and bat voices. Captured peaks: Buck 6,021, Chuck 5,679, run 5,791 / 32,767; **zero clipped samples**. Complete music/SFX WAVs, payloads, sequencer, gain/configuration and playback code are locked to the baseline. No duplicate sound event comes from the new animation.

`assets/player-hurt/` contains native/enlarged offline run/hurt GIFs, hand-consistency sheets and the close-up arm diagnostic. `docs/player-hurt-captures/` contains actual gameplay PNGs/GIFs and per-scenario coverage/audio reports. Offline hurt GIFs add guard pauses for review; actual hurt remains 12 simulation ticks. GIF timing/color quantization is a preview limitation; PNGs and native indexed source are authoritative.

## Build and limits

`bash tools/build-player-hurt.sh --native` produces the full test configuration. Docker equivalent omits `--native`. The dedicated CI job enables `MF_PLAYER_HURT=1`; historical profiles default off. The new profile requires the completed HQ jump, enemy, jab and sequencing configuration so no removed legacy upper can be referenced. Fallback: `MF_PLAYER_HURT=0 bash tools/build-corporate-hq-combat.sh --native`.

No WebRetro, physical Saturn or subjective audio-audition claim. Yabause uses the existing native libretro HLE/software core. The 12-tick cycle is deliberately quick; sunglasses limit facial detail to a few mouth/jaw pixels and posture. There are no new player death frames or gameplay timing changes. Visual approval and physical hardware performance testing remain outstanding.
