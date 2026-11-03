# Corporate Punk HQ combat presentation

Baseline: `bba999c0621f0d6f16aa13a2f776cc7dd25105a0`, `hq-build-custom-sfx-integration`. New branch: `corporate-punk-hq-combat-test`. No merges. The baseline includes the approved jump anatomy, HQ torch, responsive jabs, bat/dash mechanics, and restored custom WAVs.

## Inspection and existing behavior

The current approved enemy master is **92px**, on a 96×96 canvas with root (48,92). Its three idle and three walk poses use ten globally shared textures totaling **11,744 bytes**. Idle holds remain 24/12/18 ticks; walking still uses `walk/7%3`. Those six PNGs, ten textures, geometry, palette and lighting are unchanged. The later master is intentionally taller than the early 84/88px design discussions; it was not resized for this milestone.

The renderer previously handled only idle/walk with the HQ bank. Every other state fell back to legacy EN textures:

| Existing state | Old artwork | New presentation |
|---|---|---|
| Absent | none | none |
| Idle | HQ idle 0–2 | exact original breathing cycle |
| Walk | HQ walk 0–2 | exact original walking cycle |
| Windup | EN06 | ready → restrained coil using original pieces |
| Active | EN07 | HQ horizontal punch; original head/legs retained |
| Recovery | EN08 | retracted coil → original ready |
| Hurt | EN09 | connected head/shoulder recoil, compressed knees, planted shoes |
| Dying | EN10/11 | shared hurt → falling backward → grounded knockout |

There is no independent knockback state. Hurt and dying already move using `e->vx`, decay 7/8 and 3/4 respectively and preserve their existing world clamps. No new state or physics was added.

The source remains unchanged: HP 6, enemy damage 12, windup 24 ticks, active 6 collision checks, normal recovery 36 ticks (+12 for enemy 1), hurt timer 18, hurt recovery 24, defeat counter 30, respawn 480. Enemy attack range remains near/far 8/40px, height 36–64 and existing depth tolerance. All hitboxes, AI, target locks, scoring, player attacks and torch damage are byte-identical to the baseline.

## Artwork and assembly

Four essential native indexed resources were added. The targeted pose guide is retained under `source/` for provenance. It was registered to the native grid, cleaned and mapped into the *existing exact* CP palette. Boot silhouettes and ankle connections were repaired, the guide's overly long horizontal corpse torso/leg spans shortened locally, and the straight arm shortened locally to match the existing reach. No character-wide scale transformation is used at runtime.

Windup shifts the original head and torso together by one native pixel while retaining planted lower pieces; this is a restrained coil, not an additional texture. The new punch upper body occupies the original 30-row torso band; the actual approved head, mohawk, face, pelvis, trousers and shoes are shared. Neck, shoulder and waist seams are checked through assembled native previews. Recovery reuses these pieces.

Hurt, fall and ground change most of the silhouette, so each uses one compact cropped texture. The charcoal suit, white shirt, red tie, green mohawk, cyan back rim and restrained magenta rim remain recognizable. These are native review candidates, not final user-approved art.

The timing mapper keeps the strike visible on the first recovery tick because the original code performs its *last active collision check* on that transition tick. This is a visual mapping only. The six collision checks, damage and AI recovery timing are untouched. Subsequent recovery retracts naturally to ready.

Dying uses `timer>25` hurt, `timer>12` fall, otherwise ground. This fits the existing 30-count timer. A real post-step trace begins at timer 29 because the hit and the first decrement occur in the same simulation tick; it then reaches absent after the same 29 remaining advances as the baseline. There is no added death dwell or delayed respawn. The falling pose is intentionally airborne; the final corpse's opaque bottom meets the unchanged ground anchor. Mirroring reflects pieces about the original root, not the center of the wider review canvas.

## Exact memory budget

The baseline was measured from actual emulated Jo allocation counters: **457,888 bytes / 458,488**, **254/255 definitions**.

All twelve EN00–11 legacy textures are obsolete in this new profile because every current enemy state is covered. Their **56,960 bytes and twelve definitions** stop loading. Their files and original branches remain intact, including in the disc, and the fallback profile still loads them. No player, combat fallback, gallery or audio asset was removed.

| New texture | Dimensions | Aligned VDP1 bytes |
|---|---:|---:|
| CQ00: strike torso/arm | 72×30 | 2,176 |
| CQ01: hurt/knockback | 72×94 | 6,784 |
| CQ02: falling | 112×74 | 8,288 |
| CQ03: grounded | 112×36 | 4,032 |
| Total new payloads | | **21,280** |

**Final measured allocation: 422,208 bytes; 36,280 free; 246/255 definitions.** Net recovery: **35,680 bytes and eight definitions**. There are 232 resident payloads plus 14 existing zero-payload views. The active enemy art totals 33,024 bytes including the original HQ idle/walk bank. Every current enemy instance shares these same fourteen enemy textures. Spawning another Punk does not duplicate payloads or palettes.

No new palette bank or CRAM allocation. The original normal/burn palette banks and full CRAM snapshot match the baseline. Eight-pixel texture widths, 32-byte allocator padding, transparent raw index zero and the existing loader's +1 indexed convention are retained. No runtime asset streaming, texture replacement, per-frame CD reads or full animation cache.

Combat uses up to four draw commands per enemy (the same as approved idle/walk); full reaction/fall/ground use one. This is not a physical-hardware performance measurement.

## Preserved audio and gameplay

`source/preserved-sha256.json` locks original artwork, player rendering/gameplay/input, complete audio payloads, WAV sources, music configuration and playback code to the baseline. Historical hash locks are updated only for authorized enemy presentation files and nested manifests; the audit is `source/preservation-update.json`. Delimited new loader/accounting blocks are normalized when checking the previous jump milestone.

No audio generation or conversion ran. Jab, CONNECT, bat whoosh, ignition, sustained hiss, native driver, music and sound RAM map remain byte-for-byte unchanged. No animation function emits sound events. Enemy attack event routing remains exactly as in the approved custom-SFX baseline. Sound RAM high-water remains 420,000/524,288 bytes.

The ordinary running-bat one-hit KO is observed at capture frame 823 (HP 6→0 with running-bat active). A separate real torch scenario reaches burn and defeat and observes the original ignition/hiss plus CONNECT. Two-player tests include a dedicated P2 jab scenario with confirmed P2 CONNECT events, not just a second visible player.

## Validation and previews

Build with `bash tools/build-corporate-hq-combat.sh --native`; Docker equivalent omits `--native`. The helper enables the full latest HQ/SFX configuration and `MF_CP_HQ_COMBAT=1`. Fallback: `MF_CP_HQ_COMBAT=0 bash tools/build-custom-combat.sh --native`. The feature switch defaults off in historical profiles. All previous CI profiles remain and a separate HQ enemy job publishes the new build.

Native build, `make check`, `make test`, source/WAV/music locks, old gameplay regressions and new enemy-bank tests pass. The new bank test covers both actors, every implemented state/timer and both directions, verifies shared one-time uploads and ensures presentation never mutates `mf_game`. Source reconstruction checks verify original idle/walk pixels and the shared attack head/legs exactly, indexed payload bounds and palette equality.

`assets/corporate-punk-hq-combat/` has native and nearest-neighbor 4× idle, walk, attack, hurt, knockback and death offline GIFs, original-versus-HQ sheets, individual poses and both-facing sheets. **Offline previews do not claim actual input-driven gameplay**; the knockback offline GIF shows the hurt pose without simulating motion.

`docs/corporate-punk-hq-captures/` contains **actual native Yabause controller-driven captures**, reports and GIFs. The automated controller uses read-only snapshots to steer real button inputs; it never writes emulated RAM or injects game events. The main demonstration lets the Punk approach and attack before answering with jabs, then shows defeat and despawn. The longer story includes the unchanged respawn. Mirror and P2 scenarios exercise right-facing enemies and actual Chuck attacks. JSON coverage distinguishes observed states from unoccluded native-pixel checks. HUD, nearer actors, props, hit sparks and the existing player attack depth offsets are masked in pixel comparisons.

Each 2,400-frame scenario compares 1,705 active-period snapshots and input/jab/dash/bat traces against the downloaded approved baseline. Actual allocation counters, full CRAM equality and stable VDP1 hashes confirm that rendering, combat, respawn and co-op reuse stay within budget. Native PNG captures are lossless; GIFs reduce full-scene colors to GIF's 256-color limit. Enlarged GIFs use nearest-neighbor blocks.

The downloadable build includes native/enlarged short combat previews. The much larger 4× full-story GIF remains in this branch's capture directory; it is excluded from the build ZIP to keep the download compact.

## Remaining limitations

No WebRetro, physical Saturn, SAROO or subjective audio audition is claimed. Native Yabause HLE/software testing cannot establish real Saturn worst-case fill rate or SCSP scheduling. The single falling and grounded poses are a deliberately small, readable defeat sequence within the existing short timer, without a new bounce or vertical trajectory. Far limbs can be naturally occluded by the torso. Idle/walk were preserved rather than reauthored. Native visual approval and hardware playtesting remain outstanding.

Final runtime totals: three enemy scenarios each matched 1,705 active-period gameplay snapshots (5,115 total) and collectively checked 2,000,467 unoccluded native pixels. The original player jump scenario also passes with unchanged gameplay, all six jump phases for both players and facing directions, 42-tick flights and the same landing counters. Its broad aerial-bat screen-region comparison was updated to exclude deliberately changed enemy rectangles; the player-only sprite/pixel checks and immutable art locks remain strict. Initially that legacy comparison reported enemy redraws as a regression; no game code or player artwork was changed to satisfy it.

Hit reactions use the existing enemy facing/mirroring exactly, including the baseline's rear-hit facing policy; no new directional variants or changes to knockback direction were introduced. Mirrored scenarios validate normal impacts from either side. The final reports include exact per-pose/per-actor/per-facing coverage, so fully occluded regions are not claimed as verified pixels.
