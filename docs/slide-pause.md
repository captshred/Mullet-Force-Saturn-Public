# Wristbreaker slide phrasing and Level1 pause music — experimental

Approved executable baseline: `d97b5a9e77f418d16f22e408690f038f727e1828`, approved branch `audio/level2-wristbreaker-full-refinement`. Its later delivery commit is packaging only. This work starts at the exact executable source on `fix/wristbreaker-slides-level1-pause-music`. No merge or definitive tag changes.

## Slide correction

203 native note trajectories at102 chord onsets, lanes4/5. Their original960-tick gates have240 ticks of initial hold and240 ticks of movement, followed by held destination pitch. The initial240-tick hold remains; every existing movement step is redistributed by `new_tick = onset+240+2*(old_tick-onset-240)`. Movement now ends at onset+720, before the unchanged note-off at onset+960. At206BPM/960PPQN this is72.8155ms hold,145.631ms movement, ending218.4465ms after attack. Existing discrete native bend values and destinations are preserved, with an explicit neutral anchor at the slide start. No global bend slowing or new guitar voices.

Affected measures (1-based native4/4 bars): 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 39, 41, 42, 60, 61, 62, 63, 64, 65, 66, 68, 69, 70, 71, 72, 73, 74, 76, 77, 78, 79, 80, 81, 82, 97, 99, 100, 117, 118, 119, 120, 121, 122, 123, 125, 126, 127, 128, 129, 130, 131, 133, 134, 135, 136, 137, 138, 139.

Every affected channel, absolute onset/off tick, original curve and measure offset is listed in `docs/slide-pause-report.json`. Repeated verse power-chord families include the transposed repetitions. Short octave pickup slides in measures27/93 and all unrelated lead/bass/harmony bends remain unchanged. The fast trajectories were already in the approved native arrangement; the custom-instrument integration had preserved them. Original GP conversion intent cannot be inferred beyond that native data.

No subsequent low-string attack on lanes1/2 falls within these new movement windows. A retained A3 harmony at tick383520 in measure100 overlaps one slide in time but uses independent lane1, so its pitch remains neutral and unchanged. There is no shared-lane overlap. All note-on/off times, pitches, velocities, programs, pan, tempo/header and loop boundaries remain exact. No samples, tone definitions, mix or SFX settings change.

## Level1 pause

The original `mf_music_update` sent `SND_PauseSeq` / `SND_ContSeq` to ports0..6 except hiss4. That included music control0. The loop now begins at1; the acknowledgement mask changes0x6f→0x6e. Hiss retirement, SFX pause/resume, rejection retries, pending-event cancellation and lease handling stay exact. Music starts once and keeps advancing independently of gameplay pause. There is no music stop, continue, reinitialization or gain command on pause/unpause.

All gameplay, graphics, Level1 SEQ/TON/MAP and Level2 audio/startup/scheduler source remain frozen. Level2 pause logic is unchanged. The only other runtime edits are Level2 WMUSIC.SEQ pitch-control timestamps, the two bank maps and three generated size/address constants.

## Memory and fidelity

WMUSIC.SEQ52064→52532 bytes (+468). Music tone/FIRE addresses shift by468; every PCM/tone byte is identical. Sound-RAM high-water506660/524288; free17628. Driver/work/DSP/PCM reservations stay unchanged. No new samples, voices or persistent audio buffers.

`tools/validate-slide-pause.py` freezes every other approved tracked file, independently checks every retained note and unaffected pitch curve, checks the exact pause-control delta, validates current ISO payloads/source fingerprint, and runs the original approved regressions in isolated baseline snapshots. A production transport test covers held events for14000 paused updates and pause-ack retry; a production gameplay test freezes the entire settled game state for14000 ticks under held attack/movement and checks unpause resumes ticks.

## Native observations

Pinned Yabause8926b0c6c347f8c5c755911ddb0ac695420ffbf8/HLE BIOS. Read-only note/owner/PCM/video observations, no emulated RAM writes. Full numeric records: `docs/slide-pause-playback.json`.

- Long game pause:5375 music note-ons while paused,0 new SFX note-ons, correct complete-song ordering through a loop and repeat.13900 consecutive paused world images have identical hashes. No clipping or global music key-offs. Early pause, sustained notes, combat, held attack, unpause and rapid toggles exercised.
- Separate real-driver pause image: explosion begins before pause during the sustained opening guitar;5547 music note-ons during the stable pause window,0 new SFX ons despite held event requests, complete music loop preserved. It is a test image, not the delivered game.
- Short post-pause Level1→Level2 transition succeeds; native Level2 music starts at frame3348, with0 Level1 note-ons afterward. The normal40-KO/stage-clear logic is covered by the unchanged production regressions; native transition captures use the existing developer shortcut.
- Level2 full-loop combat:6816 ordered music note-ons;0 missing/reordered ons,0 global interruptions,0 cross-control music steals,0 clipped samples. Separate saturated native stress:31/32 slots, peak29858/32768,0 clipped samples and0 truncated ordinary drum tails. No voice demand is added by the corrections.

## Existing E108 and other baseline limitations

E108 is a longstanding intermittent issue, personally confirmed by the owner and deferred to a separate task. A late handoff after a full-loop pause hit E108 twice in this HLE test; the approved executable without pause also failed at the late handoff. The approved executable with music paused, and the corrected build after shorter pauses, successfully loaded Level2. These occurrences remain recorded. **E108 is not fixed; not all cold-start/handoff tests pass.** No conclusion of a significant frequency change follows from these few controlled captures. Startup/stage-transition source is byte-identical.

Existing HLE cached-envelope SFX-loss warnings and the approved build's extreme-overload SFX retrigger edge remain as documented in the Wristbreaker baseline. No diagnostic is silenced or unrelated scheduling policy changed. Native results are not hardware validation. Owner listening/hardware approval remains pending.

## Build and reproduce

`bash tools/setup.sh`, `bash tools/build-source-complete.sh`, `make check`, `make test`. SDK/compiler pin and Docker base unchanged. Public builds use committed runtime assets, never private GP/MIDI/WAV masters. `bash tools/run-slide-pause-playback.sh /path/to/approved-D97/mullet-force.cue` reproduces native comparisons and records E108 outcomes. Test-driver images and raw audio stay in ignored build directories. No Actions run is claimed for the local delivery.

## Delivery identity

Executable source `38ed9a690f9349f490b5280992fcef882b32aaaf`. Later packaging commit changes docs and ZIP only. ZIP `downloads/mullet-force-wristbreaker-slides-level1-pause-music.zip`, SHA256 `8d7dbe8eef629ab06f0f6b41c193446ee6e6af557328dc8ec4125b978223fd94`. Final-source6000-frame pause/transition PCM exactly matches the tested candidate. Native build, make check, make test and cold source-checkout validation pass. E108 remains unresolved and not all cold-start/handoff cases pass; owner hardware approval pending.
