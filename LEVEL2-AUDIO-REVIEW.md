# Level 2 audio engine review

## Causes

The complete music was encoded and loaded. Music shared control 0 with player 1's flame; flame preparation applied its gain 80 to the music. The unchanged musical channel volumes and velocities added attenuation. In native Yabause's legacy integer mixer, the second guitar and bass rounded to zero PCM output at those levels. This also reproduces in music-only playback, so those missing parts are not attributed to voice stealing.

Separately, completed one-shot samples retained held MIDI keys and exhausted globally reusable driver records. When FREE0 was reached, music could replace player 1's flame on the shared control. A controlled pre-fix run lost that loop while the attack remained active; player 2's separate control survived. Actual sounding usage peaked at only 17 of 32 slots. FREE0 does not mean 32 audible voices; REPL identifies unexpected reassignment. The cached EG-based STOP label is not sufficient proof of stopped PCM in this HLE emulator.

## Correction

Music now owns control 0 at gain 127. Both flames retain gain 80 on independent channels 0/1 of control 1. Shots retain controls 2/3 and gain 96; explosions retain controls 4..7 and gain 100. The native probe verifies every SFX sample register and gain is unchanged. Ended one-shots receive one Note Off after the existing conservative 34/49-VBlank leases, returning their held-key records for reuse. Rejected retirement retries without truncating PCM or stealing another voice. FIFO orders retirement before a new note on the same channel. There is no periodic flame restart, limiter, compression, new sample, arbitrary delay or readiness bypass.

The music control gains approximately 17.6 dB. All native sequence, tone-bank and map bytes remain unchanged, including all notes, slides, velocities, channel balances and timing. The prior E008 cursor, notification, map acknowledgment and watchdog checks remain intact.

## Validation

Native compilation, make check, make test, original readiness/notification regressions, and new gain/ownership/key-retirement mutation tests passed privately. Actual native libretro/Yabause 0.9.15 HLE playback was captured at 44.1 kHz stereo with read-only slot/PCM attribution and native Note On receipts. The isolated-music case freezes simulation after normal entry; sustained stress prevents player damage and schedules SFX through the actual transport. The ordinary-gameplay case has no diagnostic RAM writes. No disc or driver instruction patches are used.

| Scenario | Result |
|---|---|
| Full composition | All 4,403 native Note On assignments match the unchanged sequence's channel/pitch/velocity counts; whole-score loop restarts |
| Music only | Both guitars and bass produce nonzero PCM; matched RMS increases 34.11 to 563.71, about 24.36 dB including restored parts |
| One flame | 2,338 steady frames, 134 phase wraps, one ignition, no missing frame |
| Two flames | Same per player; independent sustained voices |
| Both flames with heavy SFX | 5,938 steady frames each, one loop start each, zero missing frames; at least 15 reusable records; peak 17 sounding slots |
| Release/restart | Seven activations per player; no late release or missing steady frame |
| Ordinary gameplay and separate cold entries | Startup, music and SFX continue without E008 or clipping |

The same heavy pre-fix test has 5,703 missing player-1 loop frames and FREE0. Music-only stem RMS changes: guitar 1 27.87 to 291.06, guitar 2 0 to 155.30, bass 0 to 117.61 (emulator mixer units). Full-song peak is 2,124/32,768. Heavy mixed peak is 18,938/32,768 with zero clipped samples, about 4.76 dB measured headroom. A conservative score-aware coherent bound, including all SFX at full envelope and 100 ms full-level music tails, is 0.9551 full scale. These measurements do not establish subjective listening or hardware approval, or guarantee headroom for future added content.

## Preservation and resources

Level 1 source, audio, balance and gameplay are untouched. Level 2 gameplay, camera, enemies and graphics are untouched. Original attack/loop samples, pitch, envelopes and attack-to-loop timing are unchanged. Updated 24x24 explosion artwork and the explosion gain reduction to 59.566% (-4.5 dB) remain.

Physical capacity stays at 32 voices, with no fixed hardware reservation. The conservative score/SFX allowance remains 18 music voices plus 10 SFX voices, 28/32. Sound RAM high-water remains 447,588 bytes, 76,700 free. No PCM, bank, VRAM or voice allocation is added. VDP1 remains 28 definitions, 33,792 texture bytes and 81 maximum commands; CRAM remains 32 bytes.

Native compilation and regressions ran privately. The existing Actions workflow verifies and packages the matching BIN/CUE, runtime checksums and focused results. Authoring assets, private source identifiers, inventories and private history are excluded from public report/package metadata. The playable image is unchanged by metadata sanitization. Source identity is supplied separately to the user.

Load mullet-force.cue. The review is unmerged; the approved baseline is unmodified. User WebRetro visual/audible approval is pending.
