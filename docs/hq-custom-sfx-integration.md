# Custom SFX restored to the approved HQ anatomy build

Branch: `hq-build-custom-sfx-integration`. Base: `76f3002a21b6dfa33d7d8cb9aa6ecfd19550d7e0` (`hq-jump-anatomy-fix`, user-approved). Selective audio source: `b45528b727b332c99c2555922761a538f2de9221` (`custom-combat-sfx`). No merge or rollback. That sound commit shares ancestor 8c339ac with the HQ anatomy work, explaining why its separate sound changes were absent from the anatomy branch.

## Restored files and fidelity

Original WAVs are copied byte-for-byte from the approved sound commit:

| Source in assets/sfx/custom-combat | SHA-256 |
|---|---|
| Jab_1.wav | 3e0e0ca178667c6a28b29826e25df6586a2cfbf2506869ec9bb0d4085a4888dd |
| CONNECT_1.wav | 5954bdf862ae18da373bc868e1b795f6db56c29dfad45ae4bfb5246a57e1da18 |
| bat woosh_1.wav | 881a3b58254d2da8073b26a0aa0acc6bb7827311b7a4365fa18c2d60d33e110b |

The approved FX.TON/FX.SEQ/CUSTOM.MAP and sound allocation header are reused. The deterministic converter `custom_sfx.py` independently reconstructs all three sample payloads for validation: PCM16 44.1kHz, stereo averaged to mono, near-silent padding trimmed, original edge fades and gains preserved. No substitution, resampling or music conversion occurred. `validate-hq-custom-sfx.py` parses the actual BIN filesystem and requires exact FX, map and stage payload bytes.

STAGE.SEQ SHA-256: `0858a4a9af303a853ba6aac2df5aa98ec119fbb6d0d22ce8cf4a8cec5fb08eff`.
STAGE.TON SHA-256: `35b0552bde242eef8e49fbd16ae2fff991aa4058d34490d0de32eb77258f25b8`.
MIDI, config.json, music PCM, sequencer conversion tools and music volume/priority remain byte-identical to the HQ parent. The build uses MF_PRESERVE_AUDIO=1 and does not execute music conversion. Music RAM addresses move upward only to accommodate the restored larger FX bank; no music payload or playback gain changes.

1,241 artwork/music/reference files are SHA-locked to the HQ parent. Jump anatomy art, sprite assembly, player/enemy art and all animation timing/configuration are unchanged. Historical source locks were selectively rebased for authorized event/audio edits using the historical validators' normalization rules; `hq-integration-lock-update.json` records each change. Immutable artwork and music hashes remain unchanged. The frozen gameplay baseline has exactly the same simulation source as the HQ anatomy parent.

## Event mapping and priority

- Each valid ground jab initiation, including buffered deliberate repeats, emits its actor's Jab event once. Frame playback and holding the button do not retrigger it.
- Standing, running and aerial bat initiation emit that actor's bat whoosh once. Carrying the bat does not emit a swing sound.
- Confirmed player damage to enemies/drums emits CONNECT, including aerial kicks. Existing per-attack hit masks prevent duplicate damage/impact events. Multi-target same-tick hits coalesce.
- The approved custom implementation also attributes direct torch and periodic burn CONNECT events to the responsible player. Ignition and continuous flame remain their original separate sounds; they are neither replaced nor silenced.
- Fixed ports: music 0; shared ignition 1; original jump 2; enemy-inflicted impact 3; shared hiss 4; Buck combat 5; Chuck combat 6.
- Same-tick hit beats whoosh. Otherwise stop only that actor's active combat sound, retry a rejected StopSeq, and wait one actual VBlank before CONNECT. Other player's port, music and torch are independent. Handoff adds the approved one-frame (~16.7ms at 60Hz) release interval, not a gameplay/input delay. New misses on a free port start immediately.
- Per-actor CONNECT requests within four VBlanks coalesce; a new valid attack resets this audio guard. Pause cancels stale pending replacements; port commands are retried. Rapid jabs retain their existing 12-tick repeat interval and buffer rules.

## Memory

VDP1 unchanged: **457,888 / 458,488 bytes**, **600 free**, **254/255 definitions**. No textures or artwork changed.

Sound RAM: FX.TON 170,564 bytes (was 46,980); FX.SEQ 328 (was 208); original STAGE.TON 70,676 and STAGE.SEQ 29,528 bytes. Sound RAM high-water **420,000 / 524,288**, leaving **104,288 contiguous tail bytes** (plus 40 gaps). Conservative SCSP allocation bound remains the approved custom system's 22 music/release slots + 6 fixed SFX ports + 4 legacy tails = 32. No new mixer, streaming or sound driver. This bound has no conservative spare slot; physical-hardware stress testing remains outstanding.

## Validation and reproduction

Use `make custom-native` for the full HQ build; `make check` and `make test`. Native build, actual ISO checks, original-music and WAV-derived PCM comparisons, artwork locks, original gameplay suite, independent transport/pause/retry tests passed. A deterministic 16,000-input-tick test matches all baseline gameplay bytes after excluding added audio tags/ownership bookkeeping. Dedicated event tests exercise both players, single/held/repeated jabs, confirmed multi-target damage, actual running-bat input, planted/aerial bat gestures and aerial kick CONNECT.

Controller-driven Yabause libretro captures are in `hq-custom-sfx-captures/`; no emulated RAM writes or injected gameplay events. JSON files list sample starts, native sound-slot activity, overlap frames and output clipping. Six combat scenarios (missed/rapid single/co-op jabs, single/co-op jab hits, single/co-op bats) observed all restored native sample voices. Single-attacker hit scenarios had zero sampled whoosh/CONNECT overlap. Cross-player overlap is allowed, so global overlap in co-op is reported rather than suppressed. Maximum observed combat output peak 8,266/32,767, zero PCM rail samples, at most 11 active non-silent envelopes in these scenarios. WAV excerpts are actual stereo emulator output, frames 760–1249, retaining stage music. Runtime tooling: `tools/test-custom-sfx-runtime.py --help`; native SCSP decoding is pinned to the existing Yabause core state layout.

Subjective listening, WebRetro and physical Saturn testing are not claimed. Slot observation samples emulator frames, not every audio sample; overlap results apply to tested scenarios. Hardware scheduling and worst-case voice stress require further playtesting. The user should audition the included captures and playable build.

The seventh runtime scenario confirms original ignition and sustained hiss voices alongside the stage music and custom combat events. Its detailed peak/voice results and listening excerpt are included as `torch.json` and `torch-combat-capture.wav`.
