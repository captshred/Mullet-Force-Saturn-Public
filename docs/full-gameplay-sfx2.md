# Complete approved gameplay plus SFX Update 2

Branch: `integration/full-gameplay-sfx2`.
Authoritative gameplay parent: **60b7916ae519626a6b094ef04e0b4fa812900127**
(`art/city-gameplay-parallax`). Audio source:
**ebe24424d42e575482aa07eae334ab524cc1a0ab** (`sfx/update-2`).

The previous audio branch used an older gameplay foundation. This integration
starts from the approved gameplay commit and ports only audio changes and their
test expectations. It does not merge the older branch or copy its artwork, level,
main loop, animation implementation, background code or build pipeline.

## History and preserved features

The inspected gameplay ancestry is:

| Commit | Approved change |
| --- | --- |
| a4f31e1 | Public jab-jab-cross baseline and existing complete HQ gameplay assets |
| c15eec3 | Unified second-forward+A bat recognition, captured run pose, sprite audit |
| b1abb86 | Build/export documentation; preserves the bat correction |
| d664f26 | Native neon city stage, isolated palette animation, bounded VDP2 cells |
| c0d42d1 | Scoped lamp cleanup and three same-size health-selected trash-can frames |
| 26096f2 | Approved city skyline on NBG2 during active gameplay |
| 60b7916 | Fractional-scroll skyline border clipping correction |

All city art, props, sprite files, level presentation, source animation code,
input implementation and background code remain byte-identical to 60b7916.
`assets/full-gameplay-sfx2/preservation.json` locks 1,018 unchanged base files by
Git blob hash and records the authorized exceptions. It also pins exact audio
payloads to the completed SFX commit. The original game source is frozen under
`tests/full_gameplay_sfx2_baseline/` for gameplay comparison.

The complete selected wrapper chain retains:

- Approved city storefront/street, lamp cleanup and trash-can health frames.
- NBG2 skyline at camera/4 independently of NBG1 foreground at full camera speed;
  original windows, priority, alignment and fractional-border correction.
- Original neon VBlank callback, static skyline palette and existing palette banks.
- Updated Buck and Chuck sprites, Chuck denim/waist cleanup, existing idle/walk,
  dash/run, jab-jab-cross, horizontal bat, HQ jump/kick, hurt/death and torch poses.
- Existing enemies, Corporate Punk lighting/HQ combat, AI, damage, collisions,
  environmental destruction/respawn, hit-stop and cooperative play.
- Original PCM music and other effects not superseded by SFX2.

No additional animations, debris, enemy behavior or mechanics are introduced.

## Reconciled audio

The shared dispatcher runs after actual damage, including enemy attacks, torch
and burn damage. Organic survivors use NONKILL; organic zero-health targets use
the original CONNECT. Bat activation uses NEWBAT once at the existing activation
point. Destroyed inorganic props use EXPLODE once at their health transition.
Original per-target collision masks remain authoritative. Same-tick destruction
requests coalesce on the world port, consistent with the existing event model.

Player combat ports 5/6 retain acknowledged stop/release handoffs. Incoming hits
use the victim's port and bypass the outgoing-hit cooldown. World port 3 now owns
EXPLODE, allowing an enemy kill and object destruction to sound independently.
Torch, jump and music routing, gains and priorities are retained. Music remains
priority 31; effects remain priority 8. A busy sound port retains its existing
one-real-VBlank release interval; gameplay activation is never delayed.

The already committed mono PCM16 22.05 kHz samples are reused exactly. No original
WAV archive is required to build, and no new source recording is published.
Original CONNECT, jab, jump, ignition and hiss PCM/voice settings are validated;
STAGE.SEQ and STAGE.TON remain byte-identical to the gameplay parent.

## Memory

| Resource | Usage | Remaining |
| --- | ---: | ---: |
| VDP1 texture budget | 453,344 / 458,488 bytes | 5,144 bytes |
| Sprite definitions | 255 / 255 | 0 definitions |
| VDP2 allocated plus SDK-reserved banks | 434,176 / 524,288 bytes | 90,112 bytes |
| VDP2 A0 foreground cells | 106,496 / 131,072 bytes | 24,576 bytes |
| VDP2 B0 maps and padded skyline | 65,536 / 131,072 bytes | 65,536 bytes |
| SCSP high-water | 432,308 / 524,288 bytes | 91,980 bytes |

VDP1 includes 241 payloads and 14 sharing views. VDP2 A1/B1 remain protected to the
SDK (262,144 bytes total); skyline cells are 32,768 padded bytes, with a 16,384-byte
skyline map and the 16,384-byte foreground map. Graphics allocations are unchanged.
SCSP rises from 420,000 bytes by 12,308 bytes; FX.TON is 182,912 bytes and FX.SEQ
328 bytes. The prior conservative 32-slot SCSP bound does not increase. These are
allocation checks, not hardware cycle scheduling or stress-test measurements.

## Validation performed

Passed locally:

- 16,000 ticks of full-profile game state match 60b7916 exactly after clearing only
  audio event bits. All physics, HP, AI, score, attack, co-op and animation state
  bytes are included, including the newer unified bat behavior.
- SFX result tests for both fighters, enemy lethal/nonlethal attacks, missed and
  duplicate collisions, destruction once, and default/full-profile bat damage.
- Actual native transport mocks: sample routing, incoming-hit cooldown bypass,
  stop rejection/retry, real-VBlank release guard, pause and mixed kill/destruction.
- Available host regressions via
  `make -o test-live-parallax -o test-city-cleanup test`; the skipped targets are
  separately identified below, rather than counted as passed.
- Actual live parallax C loader/draw across all 321 camera values, bank boundaries,
  quarter-speed fixed point, border clipping and no runtime uploads.
- Original neon asset validator and neon VBlank callback over 2,048 co-op updates.
- Skyline hashes and pixel reconstruction against the approved neon source; the
  cleanup mask excludes the skyline rows entirely.
- Audio bank/sample/tuning/gate/map/RAM checks, public runtime locks, original
  street/parallax checks and wrapper-chain feature-flag checks.
- Actual boot-loader host allocation audit with the complete selected sprite
  profile: 255 definitions, 453,344 bytes. Sprite assets were staged for this mock
  audit only; no compiler or disc packager was run for that staging step.
- Preservation checks for all available files; original Git-index blob references
  independently confirm the two sparse files listed below.

Blocked locally:

- The network proxy refuses connections, preventing setup from downloading the
  pinned Jo Engine/compiler. The correct gameplay-parallax native build was
  attempted; no BIN/CUE could be produced locally.
- The connected file reader corrupts two binary cleanup files during text
  decoding: `assets/city-cleanup/CICELL.BIN` and `CIPIX.BIN`. They are intentionally
  sparse locally. Their original Git blob references are retained unchanged in
  the integration tree. No replacement, approximation or older file is committed.
- Full `make test` reaches the live skyline asset validator and stops on the
  missing cleanup pixel file. The live parallax C test itself passes. The cleanup
  target and complete cleanup pixel/disc checks remain blocked locally.
- Full `make check` and unified ISO checks require a complete checkout and native
  build. The strict build/CI validator does not use the local `--allow-sparse`
  diagnostic option. A normal GitHub checkout contains the genuine base blobs.

Three other neon files affected by transfer decoding were reconstructed in a
scratch directory using the existing converter and committed RGB555 source; each
matched its original Git blob hash exactly before use. They are unchanged in the
integration commit. No visual asset is regenerated or changed by the delivered
build wrapper.

No emulator, subjective listening or physical Saturn result is claimed. No
GitHub Actions workflow is dispatched automatically.

## Manual complete playable build

The new **full-gameplay-sfx2** profile runs
`tools/build-full-gameplay-sfx2.sh --native`, which validates preservation and
calls the original `tools/build-gameplay-parallax.sh --native`. That enables the
complete cleanup/neon/gameplay chain. The CI disc validator requires the live,
cleanup, neon, punch-combo and preserved-audio flags and verifies the actual ISO
contains the approved skyline, city, cans, combo textures, SFX2 and original music.

After reviewing this branch, manually dispatch:

```sh
gh workflow run build.yml \
  --repo captshred/Mullet-Force-Saturn-Public \
  --ref integration/full-gameplay-sfx2 \
  -f profile=full-gameplay-sfx2
```

Alternatively choose this branch and profile under **Actions → Manual Saturn
playtest build → Run workflow**. If the UI shows only the default branch's older
profile choices, use the CLI command above. Leave `commit_sha` blank, or supply
the exact current integration SHA. The workflow checks out that exact commit.
It remains `workflow_dispatch` only; pushing the branch cannot start it.

Download `mullet-force-full-gameplay-sfx2-<commit>` within one day. The artifact
contains the matching BIN/CUE, build identity, license files and checksums.
Keep `mullet-force.bin` and `mullet-force.cue` together and open the CUE. The disc
uses MODE1/2048. Build/check failure prevents playable artifact upload.

Local equivalent on a complete x86-64 Linux checkout with working network:

```sh
bash tools/bootstrap.sh
bash tools/build-full-gameplay-sfx2.sh --native
make check
make test
python3 tools/validate-full-gameplay-sfx2.py --disc
```

Output files are `build/mullet-force.bin` and `build/mullet-force.cue`.
