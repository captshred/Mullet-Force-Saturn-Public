# Asset index — approved v0.1 profile

This index supersedes the historical descriptions in `assets/README.md` and old
milestone reports. No asset was deleted during consolidation. **Obsolete for one
profile does not mean safe to remove:** fallback builds, shared parts, source
recipes and immutable validators still depend on older material.

Approved source: `v0.1-playable-baseline`, `921ed1ddf78a1334684833a7c49633e404366817`.
Full build: `bash tools/build-run-waist-seam.sh --native`.
For current disc truth, inspect `tools/build-native.sh`, active manifests,
`src/main.c`, `src/animation_preview.c`, `src/player_animation.c` and
`src/corporate_animation.c`. Review PNGs establish appearance; indexed TGA payloads
plus runtime mappings establish what actually renders.

## Authoritative active sources and overrides

| Use | Current source / packed data | Important dependency or precedence |
|---|---|---|
| Hero design masters | `assets/animation-study/masters/buck-master.png`, `chuck-master.png` | HQ visual identity references; do not directly replace a whole sheet by shrinking them |
| Approved 88px gallery masters and shared hero palette | `assets/gallery/`, `GB*.TGA` (Buck), `GC*.TGA` (Chuck), `manifest.json` | Three-piece idle, shared by gallery and character bank; GB0 carries the common palette |
| Idle breathing and reusable hero parts | `assets/animation-polish/` | Approved idle/reusable pieces coexist with older six-pose walks; the six-pose walk is not current gameplay |
| Three-pose walk | `assets/original-three-walk/` | Early approved poses, Timing B: 10 ticks/frame at 60Hz |
| Final walk knee lift | `assets/knee-lift/`, especially `overrides/` | Applied after original walk; preserves approved frames 2/3 and idle |
| Running anatomical base | `assets/running/`, `RN*.TGA`, `src/running_data.h` | Four alternating poses; source canvas 128×96, root (64,92); retain original lower-body/stride references |
| Shared aluminum bat and grip registration | `assets/running-bat-visual/` | One shared carried bat; per-actor/per-frame hands and existing metal-cover pieces |
| Jab body/repeat presentation | `assets/jab-cohesion/`, `src/jab_visual.h` and `src/jab_repeat.h` | Artwork shares existing resources; timing/input remain in approved C/config files |
| Bat/jab packed combat bank | `assets/attack-sequence/`, `COMBAT/CA*.TGA` | Built on `assets/bat-momentum/`; current sequencing excludes the rejected extra follow-through. Some running-prep crops receive later waist overrides |
| HQ blowtorch | `assets/hq-torch/`, `HT*.TGA`, `src/hq_torch_data.h` | Existing palette groups and shared legs; preserve tool/flame registration |
| HQ jump/kick | `assets/hq-jump/`, `HJ*.TGA` | Current exported payloads include the anatomy corrections; `assets/hq-jump-anatomy/` holds before/reference comparisons and provenance |
| HQ hurt | `assets/player-hurt/`, `HQHURT/PH*.TGA` | Approved recoil/pain/recovery; three visual phases within existing 12-tick hurt interval |
| HQ defeat | `assets/player-death/`, `HQDEATH/PD*.TGA` | Reuses exact hurt uppers plus two kneeling lowers; original 120-tick automatic recovery remains |
| Earlier Chuck run corrections | `assets/player-hurt/RC*.TGA`, `CT*.TGA`, then `assets/player-death/RD*.TGA`, `DT*.TGA` | Successive scoped derivatives. They are not extra runtime arms or a separate enemy/player bank |
| Approved Chuck denim repair | `assets/chuck-denim-cleanup/` | Six equal-size disc substitutions. Preserve its 68 corrected native coordinates |
| **Final approved running waist pixels** | **`assets/run-waist-seam/`** | Last override: RN04, RN10, RN16, RN22 and COMBAT/CA21, CA27, CA49, CA55. 104 waist pixels; first/third poses and earlier denim repair preserved |
| Corporate Punk current appearance and idle/walk | `assets/corporate-punk-lighting/` | Current native master: 96×96/root (48,92), opaque height **92px**; use actual dimensions, not an older 84/88px concept label |
| Corporate Punk HQ combat | `assets/corporate-punk-hq-combat/`, `CQ*.TGA`, `src/corporate_hq_data.h` | Shares approved lighting idle/walk/parts; HQ strike, hurt, fall, ground; previews 144×112/root (64,108) |
| Original street pixels | `assets/cd/ST0.TGA` through `ST4.TGA` | Authoritative unchanged street source; five VDP1 fallback textures remain on disc/source |
| VDP2 street | `assets/vdp2/STCELLS.BIN`, `STMAP.BIN`, `STPAL.BIN` | `tools/build-street.py` losslessly tiles the street; palette bank 1; original five textures not resident in full VDP2 profile |
| Skyline / long-map technical preview | `assets/parallax/` | `tools/build-parallax.py`; 8,192px ring/chunk preview, skyline quarter-speed; temporary scenery, not final level art |
| Flames, embers, drums, shadows, impacts and HUD | `assets/cd/FL*.TGA`, `EM*.TGA`, `CHARGE.TGA`, `DR*.TGA`, `SHADOW.TGA`, `HIT.TGA`; runtime HUD in `src/main.c` | Still required. RGB555 and indexed groups have distinct allocation costs |
| Custom combat sound masters | `assets/sfx/custom-combat/Jab_1.wav`, `CONNECT_1.wav`, `bat woosh_1.wav` | Original supplied WAVs; source branch `custom-combat-sfx` is not an instruction to merge its old gameplay |
| Approved disc SFX | `assets/cd/FX.TON`, `FX.SEQ`, `CUSTOM.MAP` | Restored original custom sounds; immutable checks in `tools/validate-hq-custom-sfx.py` and integration report |
| Approved stage music | `assets/music/` MIDI/config and `assets/cd/STAGE.TON`, `STAGE.SEQ` | Existing PCM-backed SCSP instruments/native sequence. Keep committed payloads unchanged; no automatic music regeneration |

### Active copy order matters

The approved wrapper chain enables all required flags. `tools/build-native.sh`
first copies base assets, then current banks, then applies scoped overlays.
For the latest run pixels the relevant order is:

1. `assets/running/` and `assets/attack-sequence/` base run/prep pieces.
2. Hurt-era RC/CT replacements.
3. Defeat-era RD/DT replacements.
4. `assets/chuck-denim-cleanup/` replacements.
5. `assets/run-waist-seam/` final replacements.

Knee-lift overrides similarly follow the original walk bank. The final disc may
use an old filename with newer approved bytes. Never choose authority solely by
filename, modification date or a resource number shown in diagnostics. C19/C21
are pose labels for running frames 2/4, not textures CA19/CA21.

## Legacy material: retained intentionally

| Location / group | Status in the full profile | Why keep it |
|---|---|---|
| `assets/cd/BU*`, `CH*`, `NL*`, `BT*`, `CT*`, `LEGS`, `AL*` | Mixed: approved HQ presentation replaces many poses; other legacy pieces still load as shared parts or combat fallbacks | Do not delete the old bank as a group. Load/skip decisions are explicit in `src/main.c` |
| BU08/CH08 | No longer uploaded in HQ hurt profile | Replaced by HQ jab/hurt; original files remain needed by historical configurations and locks |
| BU13/CH13/NL13 | No longer uploaded in HQ defeat profile | Replaced by approved HQ kneeling defeat; retain original death fallback/source |
| BU11/12/14, CH11/12/14 and corresponding jump lowers | Skipped by HQ jump profile | Retained fallback and reference data; do not re-enable them over HQ jump |
| `assets/cd/EN00..EN11` | Present on disc but not resident with HQ enemy combat | Original enemy bank is intentionally replaced at load time; fallback builds and validators retain it |
| `assets/cd/TU*`, `TC*` | Older torch uppers excluded with HQ torch | Historical fallback; fire/ember/cue resources remain active |
| `assets/cd/ST0..ST4` | Source and VDP1 fallback; not resident when VDP2 street is enabled | Exact-pixel VDP2 conversion and control-build regression |
| `assets/animation-study/archive/`, old six-pose walks, `assets/swagger-walk/` | Superseded animation experiments | Pose/reference comparisons and locked provenance, not default gameplay |
| `assets/stride-fix/`, `assets/leg-artifact-fix/`, `before/` folders | Historical anatomy/source layers | Explain and reconstruct the approved alternating stride; not spare active frames to delete |
| `assets/corporate-punk/`, `corporate-punk-animation/`, `corporate-punk-refined/` | Earlier native designs/packing stages | Current lighting/combat sources and validators depend on their lineage |
| Old `assets/combat-animation/`, `assets/bat-momentum/` | Superseded or shared intermediate combat sources | Current attack bank and leg/preparation recipes refer back to them |
| Historical music/FM branches | Separate experiments, not current stage audio | Unique commits and exports must be archived/reviewed before any branch deletion |
| `assets/README.md`, older milestone budgets | Historical documentation | Describes that older build; consult the active full-profile manifest for current budget |

## Source recipes and checks

Scoped preparation/export scripts include `build-knee-lift.py`,
`build-run-waist-seam.py`, `build-chuck-denim-cleanup.py`,
`prepare-player-hurt.py` / `build-player-hurt.py`, `build-player-death.py`,
`build-hq-jump.py`, `build-hq-torch.py` and the Corporate Punk packers under
`tools/`. A recipe may rebuild a derivative from a retained guide/parent, so
editing a review PNG alone may not persist. Review its inputs before invoking it.

Do not automatically run `tools/draw-assets.py`, whole animation generators,
`tools/music.py` or FM conversion tools while editing one sprite. The normal
approved wrapper preserves audio. Refer to [ART_WORKFLOW.md](ART_WORKFLOW.md)
for candidate packaging and native/indexed review requirements.

Current full-profile VDP1 allocation: **446,304 used / 12,184 free / 253 definitions**.
There are 239 payloads and 14 views. Exact counts, source hashes and active bytes
are verified by `make check` and optional runtime comparators; older manifest
`boot_bytes` values are historical, not additive costs for the current game.
