# Level 2 duplicate Shot audio

Starting point: `captshred/Mullet-Force-Saturn-Public`, branch
`fix/level1-bat-command-buffer`, exact approved commit
`bb7b6b61af79ccddd9994a9623456d3f10ad6613`. Work is isolated on
`fix/duplicate-shot-sfx`; no baseline branch or tag is changed.

## Existing Explosion behavior

`MF_WS_EXPLOSION_MIN_SPACING` in `src/wingsuit_audio.h` is **5**.
`main.c` supplies the VBlank counter through the Level 2 runtime to
`mf_ws_audio_step`. Thus this is five VBlanks (about 83 ms at 60 Hz),
not sound-driver timer ticks or milliseconds. `advance_explosions` records
`explosion_next = now + 5` after a successful Note On. Four independent
voices keep their natural tails. An eight-event bounded FIFO count spaces
simultaneous explosions at ticks 100/105/110; it does **not** discard duplicate
explosion events. This proven scheduler is preserved byte for byte.

## Change

Only the Level 2 Shot sound is filtered. P1/P2 bits feed one pending sound
identity. At audio dispatch, requests less than five VBlanks after its last
successful Note On are discarded. Exactly five VBlanks permits another sound.
Rejected MIDI submission does not open a window. Unsigned elapsed-time
arithmetic supports counter wrap, and loading resets history.

Existing two Shot controls rotate through free voices. Neither active voice
is stopped or restarted to serve a new request. If both are occupied, one
coalesced pending sound waits for natural retirement (existing 34-VBlank
lease); repeated requests cannot accumulate a backlog. Consequently very fast
fire can produce fewer/delayed audio attacks while both tails occupy the two
voices. Projectiles and all gameplay continue at their original rate. Audible
rapid-fire feel still needs play-testing.

No generalized filter was added: changing Level 1 SFX, Hit, Explosion or Flame
would broaden risk beyond the requested polish. Their timing and music
sequencing remain unchanged. No sample, gain, pitch, routing, SCSP allocation,
or channel is changed. State adds two unsigned words (8 bytes on SH-2), no
heap allocation. SCSP high-water remains 485812 bytes, with 38476 bytes free;
the existing 29-principal/32-physical-slot budget remains unchanged.

## Validation

- `bash tools/setup.sh`: exact pinned Jo Engine SDK installed.
- `make test`: historical regressions plus current recovered transport and
  gameplay tests, including approved Level 1 FF+A command buffering.
- `python3 tools/test-recovered-audio.py`: UBSan; separate P1/P2 request calls,
  coalesced simultaneous projectiles, alternating solo fire, exact window
  boundaries, rapid repeated requests, occupied voices, SDK rejection/retry,
  clock wrap and reload. Explosions retain 100/105/110 spacing and natural tails.
  Shots, explosions and Hit run together with dual sustained Flames and music;
  handoff/release, music start count and mixer isolation remain checked.
- Seven mutation checks reject missing/wrong Shot windows, duplicate queueing,
  and existing startup regressions.
- `bash tools/build-source-complete.sh`: approved complete native profile with
  the pinned SH-2 compiler. A locally extracted Debian genisoimage package was
  used for packaging; no repository/compiler/container pin was changed.
- `make check`: complete preservation chain, original assets and native disc.
  The new delta lock layers over the approved baseline; older locks stay intact.

Level 1 punch/bat/impact and music regressions passed. This is host/mock,
structural and native-build validation, not listening or emulator/hardware
validation. No Saturn emulator is installed in this environment.
