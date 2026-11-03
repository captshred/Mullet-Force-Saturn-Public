# Chuck frame-3 patch and HQ player defeat

Branch `chuck-run-final-fix-player-death`, based on validated `99ac5d48ea5e69fdfae7bee00edaeb462d0f8880`. No merges or writes to prior branches.

Build: `bash tools/build-player-death.sh --native` (or omit `--native` for the pinned Docker toolchain). Isolated behind `MF_PLAYER_DEATH=1`, requiring the complete approved HQ-hurt profile. Disable it to reproduce the previous hurt/run-cleanup bank. Previous artwork and disc payloads are retained.

## Chuck shoulder correction

Frame 3 (index 2) contained a frame-specific upright sleeve/skin remnant baked into the previously cleaned source. It crossed RN18/RN19 and the corresponding CA51/CA52 bat-preparation crops; there is no extra draw call, walking overlay or duplicated texture upload. The replacement uses 118 pixels from Chuck's existing pose-1 shoulder in the native x53–63 / y23–37 region. No generated running art or concept-sheet running pixels are used. The remaining narrow blue outer edge matches the adjacent approved vest armhole, rather than the obsolete upright strip.

`chuck-run-2-final.png`, RD0/1 and DT0/1 are new derivatives, replacing the old RC/CT payload names only in this build. Headers, dimensions, palettes and all bytes outside the recorded mask are identical. Bat-hand anchors, rear glove, free fist, all legs and the other three running poses are untouched. All Buck run PNGs and RN textures are SHA-256 locked unchanged. The carried bat and attack mappings/timing are unchanged.

## Defeat presentation

The existing game has automatic player recovery after 120 simulation ticks, not a persistent corpse or a separate new game-over state. No state, timer, health, damage or recovery code was changed. The renderer selects:

| Defeat elapsed ticks | Pose | Textures |
|---|---|---|
| 0–7 | Severe recoil | Approved hurt phase 0, exact existing pieces |
| 8–23 | Hunched stagger | Approved hurt phase 2, exact existing pieces |
| 24–119 | One-knee collapse, held until recovery | Exact hurt-phase-2 upper translated down 14px, one new lower per fighter |

There is no fourth corpse pose. The one-knee pose is the final readable defeat frame. Hit-stop still freezes the original timer. Only zero-HP active players with a positive defeat counter select these poses; living hurt art, its 4/4/4 cadence and existing invulnerability visibility rules are unchanged.

Native canvas is 128×96, root (64,92); soles/rear knee share ground y92. No runtime scaling. The new lowers use the existing indexed GB palette with raw-index-zero transparency and widths divisible by eight. Upper identity, sunglasses, expression, hair and jacket/vest pixels are reused exactly. Generated kneeling anatomy was used only as a lower-body guide, then registered, masked and quantized at native resolution. Source guides and reproducible conversion are retained.

For the pre-existing edge case of dying in the air, simulation height freezes during defeat. A presentation-only offset interpolates that height to ground over the first 24 defeat ticks; no physics is changed. Natural airborne lethal hits have not been separately captured; grounded defeats are the tested case.

## Exact memory

| Allocation | Previous approved build | New build | Change |
|---|---:|---:|---:|
| VDP1 texture bytes | 448,672 | 446,304 | −2,368 |
| Free in actual 458,488-byte pool | 9,816 | 12,184 | +2,368 |
| Sprite definitions, limit 255 | 254 | 253 | −1 |
| Payload textures | 240 | 239 | −1 |
| Existing zero-payload views | 14 | 14 | 0 |
| Additional CRAM banks | 0 | 0 | 0 |

Stop uploading obsolete BU13 / CH13 (2,368 bytes each) and NL13 (1,600 bytes) only in the new profile: 6,336 bytes / three definitions replaced by PD0 72×26 (1,888 aligned bytes) and PD1 80×26 (2,080): 3,968 bytes / two definitions. No approved animation is removed. PH textures are unchanged. RD/DT substitutions cost zero additional bytes or definitions. Startup loads only; no per-frame CD reads, streaming or duplicate uploads. Loader capacity guards reject overflow. Runtime counters confirm the table, unchanged CRAM and stable texture VRAM throughout each capture. VDP2 and sound allocation remain unchanged; sound-RAM high-water is 420,000 / 524,288.

## Validation

`make test`, `make check`, native SH-2 BIN/CUE build, immutable-source checks, exact ISO payload checks, indexed conversion/reconstruction, 120-tick selector tests, two-player/facing tests, idempotent uploads and capacity rejection pass. All approved hurt sources and original Buck run payloads remain byte-for-byte unchanged. The new source-normalization lock permits only the explicit optional presentation/load blocks; gameplay, enemy, input, audio, jump, torch, jab and bat source/assets retain their checksums.

Five controller-only native Yabause/libretro scenarios compare against the downloaded previous approved BIN/CUE: two-player run/bat and both fighters' natural defeats facing both directions. No emulator RAM writes or injected damage. All 16 actor/run-frame/facing combinations and 17 carry-to-swing samples pass. Natural enemy hits reduce HP to zero; all three visual phases and automatic 120-tick recovery are observed. Every gameplay, dash, jab and running-bat snapshot matches the control. Exact opaque enemy masks exclude genuine occlusion from pixel checks; offscreen/HUD/nearer actor pixels are excluded. See individual JSON reports and real gameplay GIFs in `player-death-captures/`.

Aggregate: 9,925 identical gameplay snapshots, 1,171,906 matching native sprite pixels, 46,054,825 unchanged pixels outside authorized character regions.

Custom bat-whoosh and CONNECT activity is observed in actual SCSP traces. Recorded output has zero clipped samples. Source WAVs, disc sound payloads, driver and music are unchanged; no new sounds or listening/hardware claim. Audio validation records peaks and voice starts.

## Review files and limits

`assets/player-death/` contains native and 4× nearest-neighbor death contacts/GIFs, offline hurt-to-death transitions, corrected Chuck run in both directions, before/after frame-3 diagnostics and bat-hand contacts. These offline previews are clearly named `offline`. `docs/player-death-captures/` contains actual full-scene controller-driven captures, including normal recovery. Static art remains subject to visual approval; the limited three-pose collapse is intentionally economical rather than a fully in-betweened fall.

Native Yabause HLE BIOS/software rendering is tested. WebRetro Yabause, physical Saturn, optical drive/SAROO and real-hardware performance are not tested here. The initial mirrored P2 capture left the fighter off-camera; the final controller-only scenario moves P1 along to keep P2 in view. No game/camera code was altered to obtain the captures.
