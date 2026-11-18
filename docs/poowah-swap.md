# POOWAH human death sample swap

Exact working parent executable: `653b5f4206e58e9aa8e4c540ce08fa89f9db595a`.
Its delivery commit is `517c7f790f1b11f4abddf9908b83cb5acfbf5c5b`, with
BIN SHA256 `2b224b53a2f1cc90020c85913c5f4df4fd7cfe97ce929c953b8f44932422c23b`.
This retains the complete working protected-death implementation and approved
+15% SFX velocities. No older definitive baseline was substituted.

POOWAH is mono44100Hz PCM16,33679 frames/0.763696145s. Full-rate PCM requires
67358 bytes;22050Hz PCM16 needs33680 bytes. Neither fits the available replacement
space.11025Hz PCM16 fits, so8-bit conversion is unnecessary. Other Level1 FX
programs0..7 are PCM16. The established ffmpeg bandlimited conversion preserves
mono and16-bit precision, converts to Saturn big-endian PCM16, and uses no gain,
normalization, trimming, fades, compression or time stretch. Source WAV is private.

Runtime:8420 frames/16840 bytes, nominal0.763718821s (resampling frame rounding).
Program/song8, control7, velocity110, SFX volume112, priority31, centered pan,
root compensation84 and envelope/TL remain as before. Only the PCM8 flag becomes
PCM16 and sample LEA becomes8420. The old10725-byte UGH PCM is removed from the
active bank. The original pre-ARGH death PCM remains41824 bytes, once, shared by
cross/jump-kick hits with its existing velocity127.

Protection code in music.c, music.h and the main-loop handoff guard is byte-for-
byte unchanged. Duration metadata is recomputed: minimum46 real VBlanks (was59),
song8 gate782 native ticks (was982), advisory lifetime50 ticks (was63). Existing
SDK PLAY->STOP detection, full-duration floor, scoped post-completion retirement,
one-real-VBlank guard, request suppression and overlapping-death coalescing all
remain intact. There is no hardcoded UGH duration left in the active metadata.
The existing50ms sequence allowance and retirement guard are preserved.

All eight other FX song payloads are copied as exact bytes, with no velocity
calculation or boost pass. All their PCM, instrument settings, addresses, gates,
controllers, pan, priority and playback code remain unchanged. Velocities stay127;
POOWAH stays110. Both music SEQ/TON payloads and every Level2 source/audio file
remain byte-exact. Level1 music banks are relocated intact to fit the replacement.
No gameplay, graphics, AI, cleanup or protection mechanism is redesigned.

Level1 sound-RAM high-water:521304/524288 bytes;2984 bytes free. FX bank199796
bytes. FX sequence368 bytes. Protected sample address332184; sample8420frames,
PCM16; Stage SEQ349028 and Stage TON389156. Alignment and interpolation guard
bytes are included. No unrelated samples are removed or degraded.

Native verification:16000-frame real-driver capture,19/19 POOWAH plays reach
natural PCM end under competing events and pause; complete4907-note Drop Zone
loop plus prefix (5890 music starts), no reordered/missing notes, forced music
cuts or clipped output.8000-frame game/transition capture completes all3 death
plays and2847 ordered Wristbreaker music notes. Measured active SCSP slot peaks
at VBlank sampling:15 in driver capture,23 during transition. These use native
ECNT, not stale driver EG flags. Native mixed peaks18431 and19611/32768.

Current transport/collision/pause tests and the complete protected working-build
regressions pass. Strict validation rejects changes to any baseline file outside
the necessary sample/bank/duration metadata, build validation entry points and
runtime manifests. It also locks every byte of songs0..7 and the original tone
prefix except program8's PCM format/length fields.

These are emulator/host checks; hardware approval is pending. Known intermittent
Level2 E108 remains unresolved and was not investigated or claimed fixed. No
merge, new definitive tag or changes to previous THE ONE tags are made.

Rebuild: `bash tools/build-source-complete.sh`, `make check`, `make test`.
Actions: **Manual Saturn playtest build**; workflow branch
`audio/level1-poowah-death-swap`; reuse existing profile
`level1-ugh-protected-sfx`; source_ref is the exact executable SHA in the delivery
manifest. This profile consumes the committed POOWAH runtime bank; it does not
regenerate UGH. SDK/compiler pins and existing1-day retention are unchanged.
Delivery is a local native build, with no Actions run claimed.
