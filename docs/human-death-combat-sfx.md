# Level1 human death and shared combat impacts

Experimental branch: `audio/level1-human-death-combat-sfx`.
Parent approved executable: `38ed9a690f9349f490b5280992fcef882b32aaaf`
(`the-one-wristbreaker-slides-pause-definitive`). No tags are changed.

## Runtime routing

Human enemy death (melee or fire) selects FX song/program8. Nonlethal cross
punch or unarmed aerial kick against a human enemy selects the existing FX
song/program6. Both attacks reference that single original PCM allocation.
Ordinary jab hits retain song0; jab initiation retains song5. Player death
retains song6. Bat, ordinary jump, ignition/hiss, environmental/inorganic
impacts and explosions retain their original songs and PCM.

A lethal cross/kick selects song8 alone: the existing death-over-impact policy
is preserved. Existing collision masks, four-tick impact suppression, per-player
ports5/6, volume112, priority31, acknowledged stop and one-real-VBlank release
replacement guard are unchanged. Damage, health, collision, attack buffering,
animations, hit-stop and knockback are unchanged. Audio classification flags
are added only at the existing confirmed enemy hit/death sites.

## Source and conversion

The supplied ARGH.wav is actually stereo, 44100Hz PCM16,49095 frames
(1.113265s). Channel peaks19492/19493; arithmetic mono peak19492.5
(-4.51165dBFS). One exact-zero leading frame and no exact-zero trailing frames;
no silence is removed. The user approved11025Hz signed PCM8 mono after the
memory check. Importer explicitly averages the two channels and bandlimited
resamples; no gain, normalization, compression, fades, trimming or time stretch.
The source WAV stays private. Public builds consume committed runtime banks.

Converted sample:12274 bytes/frames,11025Hz,8-bit mono. Native base-note84
with note60 gives11025Hz playback; one-shot, no loop. New tone inherits the
old death layer's envelope, TL, routing and velocity behavior. Native capture
shows the complete12274-frame sample reaching its natural end.

Preserved old sample:20912 frames,41824 bytes,44100Hz PCM16; its waveform,
length, native playback pitch, envelope and sequence remain byte-exact.
Old PCM SHA256: `47f5e17f0f874572e4390a87b6414ddfa6b05c34dddce54093081fe5c1d0ecdd`.
New PCM SHA256: `6d461e766bdd1adadc74d4030b535ee66992be00718be8c157edb7ae6ff95889`.

## Memory

All original8 FX voices and8 FX songs are preserved; program8/song8 is added.
Shared old sample occurs once. PCM alignment/bank metadata relocate the old
sample from256814 to256896; new sample starts332188. Level1 sound RAM high
water is516744/524288, leaving7544 contiguous bytes (previously19908).
Original music PCM/SEQ payloads are unchanged and relocated as intact banks.
Level2 files and loader/audio code are byte-identical to the approved baseline;
its separate map still has17628 bytes free. No unrelated PCM is degraded.

## Validation

- Current collision tests: both players; jab/cross/kick; lethal/nonlethal;
  misses; per-target duplicate prevention; fire deaths; separate player death;
  unchanged inorganic destruction.
- Current transport tests: actual music.c with SDK acknowledgments mocked;
  correct old/new program routing, lethal precedence, retry/stop guard,
  duplicate suppression, two-player isolation and pause.
-24000-frame full-state input replay against approved game.c produces identical
  state hash `f2d0c25a19bde4b6` after removing only the new audio flags.
- Current pause gameplay test:14000 frozen ticks with held attack/movement.
- Existing approved regression suite is run in a protected baseline snapshot;
  changed collision and transport implementations are tested separately above.
-16500-frame real-driver capture:6243 music note-ons, complete4907-note
  Drop Zone loop and repeat prefix;4970 music note-ons in long pause window;
  no forced music off, cross-control music steal or clipped output samples.
  Peak observed non-release envelope occupancy17/32 (short release tails
  excluded; cached envelope output is not a reliable live-slot count).
  Eighteen new-death and eighteen shared-old-sample starts. All18 new sample
  runs reach their natural PCM end. Mixed PCM peak22162/32768.
-8000-frame in-game combat capture:23 new-death and19 shared-old-sample starts.
-6000-frame in-game pause/transition capture enters Level2 successfully.
  All1460 captured Level2 music note-ons match approved ordered keys/sample
  addresses. Stage entry is2 frontend frames later; normalized note-on times
  differ by at most1 frontend frame. Captured mixed waveforms are not claimed
  bit-identical. All Level2 source/assets are verified byte-identical.

These are emulator and host tests, not hardware approval. The known pre-existing
intermittent Level2 startup E108 remains unresolved; it is not investigated or
claimed fixed. A successful transition does not establish universal cold-start
success.

## Rebuild

`bash tools/build-source-complete.sh` builds the complete approved profile
with the existing pinned SDK556d081146211b6a1cfa6591d70f9487d406758b,
MF_PRESERVE_AUDIO=1 and native compiler. Then `make check` and `make test`.
GitHub Actions: workflow **Manual Saturn playtest build**, workflow ref this
experimental branch, profile **level1-human-death-combat-sfx**, source_ref the
exact executable source SHA listed in the delivery manifest. Existing artifact
retention remains1 day. Local native builds are distinguished from Actions runs.
