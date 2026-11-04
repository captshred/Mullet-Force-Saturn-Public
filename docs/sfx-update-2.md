# SFX Update 2

Based on supplied checkout 55725797cf9bc3321967518203e43c911d596847.
Scope: audio events, native SEQ/TON/MAP, allocation header, regression expectations,
and a manual build option. Gameplay, art, animation, backgrounds and music are
unchanged relative to that checkout.

The shared `hit_sound` dispatcher runs after actual damage for player melee,
enemy melee, direct torch and burn damage. Surviving organic targets use NONKILL;
zero-health organic targets use the original CONNECT. Inorganic destruction uses
EXPLODE, once at the existing HP-to-zero transition. Existing hit masks prevent
collision repeats. Nonlethal object damage uses NONKILL.

Buck and Chuck retain combat ports 5/6; incoming damage uses the victim's port,
interrupting an abandoned attack. The former enemy-impact port 3 now owns EXPLODE.
Destruction stops its attacker's whoosh; an organic kill and destruction on the
same tick can play CONNECT and EXPLODE independently. Simultaneous destruction
requests coalesce on the shared port, matching the game's event-bit architecture.
The acknowledged StopSeq plus one real VBlank release guard is preserved, including
rejected-command retries and pause handling. Music port 0 is unchanged. Bat events
remain at actual activation, including run+A after double-forward, once per swing;
a busy port uses the existing one-VBlank handoff, with no gameplay delay.

## Samples and memory

`tools/update-sfx2.py /private/path/MF\ SFX2.zip` imports the three WAVs with ffmpeg.
Source WAVs remain private, consistent with this public repository's asset rules.
Only converted runtime payloads and provenance hashes are committed. New samples
use mono, bandlimited 44.1-to-22.05 kHz conversion, big-endian PCM16, silent-padding
trim, edge fades, and peak normalization (40%, 38%, 40% respectively for NONKILL,
NEWBAT, EXPLODE). A root key of 72 with note 60 selects half the SCSP unity clock;
there is no pitch or duration doubling. Sample peaks are below PCM16 saturation.
This does not establish clipping-free behavior of the complete hardware mix.

| Resource | Before | After |
|---|---:|---:|
| FX.TON | 170,564 | 182,912 bytes |
| FX.SEQ | 328 | 328 bytes |
| Sound RAM high-water | 420,000 | 432,308 / 524,288 bytes |
| Contiguous free tail | 104,288 | 91,980 bytes |

Total high-water increases 12,308 bytes. The 40-byte old allocation gap is reclaimed.
Voices 0/2 replace obsolete whoosh/enemy-impact PCM; voice 7 replaces old bat PCM.
No new sample copies, ports or layers are allocated. Original CONNECT, jab, jump,
ignition and hiss voice settings/PCM are hash-checked after relocating sample
addresses. Original STAGE.SEQ/TON are byte-identical. The conservative prior
32-slot budget does not grow; hardware stress testing is still needed.

## Validation and delivery limitations

- `make test`: full C suite passes, including SFX2 damage-result tests and native
  command transport mocks. Both players, lethal/nonlethal punches and bats, enemy
  hits/deaths, missed attacks, destruction and duplicate collisions are covered.
- Existing controller-input tests cover actual double-forward/run+A activation,
  held A, jab combos and animation/damage boundaries.
- `tools/validate-sfx2.py`: PCM/provenance hashes, tuning, sample limits, one-shot
  gates, map/header layout, original-voice preservation and RAM bounds pass.
- `tools/check-public.py`, street and parallax asset validators pass.
- A 16,000-tick deterministic gameplay comparison against the supplied checkout,
  with combo/fast-bat/dash enabled, is byte-identical after clearing audio events.
- Native build and full `make check` cannot complete in this environment: the
  configured proxy refuses connections, so setup cannot fetch the pinned SDK;
  there is no built BIN for disc validation. No emulator, listening or hardware
  verification is claimed. No GitHub Actions run is dispatched.

## Manually generate BIN/CUE

On GitHub, open **Actions → Manual Saturn playtest build → Run workflow**. Select
branch `sfx/update-2`, profile `sfx-update-2`, and leave `commit_sha` blank (or enter
that branch's full current SHA). This checks out the workflow's exact commit,
builds the existing complete punch-combo profile, and runs `make check` and
`make test`. Download the artifact within one day. Keep its matching
`mullet-force.bin` and `mullet-force.cue` together; open the CUE.

Local equivalent on x86-64 Linux:

```sh
bash tools/bootstrap.sh
bash tools/build-punch-combo.sh --native
make check
make test
```

The output pair is `build/mullet-force.bin` and `build/mullet-force.cue`.
