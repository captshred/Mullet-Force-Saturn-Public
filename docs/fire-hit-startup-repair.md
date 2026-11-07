# Fire/Hit startup-order repair candidate

Parent/broken feature: 0f0ef24873a3e3c91b573d32fd26f725328c4353.
Owner-working reference: 6e5c8d9eb9b83e4cf3ebb278939b02b8787a0b1e.
No gameplay, scheduling, music, Flame, sample, map-file, gain or artwork bytes
change. Only initialization ordering, scoped deferred file reads, diagnostics,
tests and exact preservation metadata change.

## Confirmed evidence and limits

The owner proves the previous image fails in WebRetro at BOOT_CPU/DRIVER READY.
That gate requires a changed041a consumed-command cursor AND all eight request
blocks empty. The old EXPECT1/GOT0 report does not distinguish unchanged cursor
from a blocked request and contains no command ID. No failing WebRetro runtime
trace is available here. Therefore the exact stalled command/68K instruction
and a complete causal explanation of the WebRetro-only hang remain unconfirmed;
we do not present native playback as proof of WebRetro equivalence.

The exact executable-affecting delta was audited. The feature changed bootstrap
from56-byte WMUSIC.MAP to64-byte WFIRE.MAP and added a tone upload after
slInitSound, before its later explicit restart. Bank/PCM/control addresses are
valid and fit512KiB. Hit channel preparation occurs AFTER BOOT_CPU, so it cannot
itself be the initial DRIVER READY failure. An accidental Hit preparation block
inside timeout diagnostics was also removed; it was outside BOOT_CPU and is not
claimed as the reported failure's cause.

Pinned SDK instructions establish a startup-order hazard absent for Fire in the
parent: slInitSound internally issues SMPC SOUND ON6, waits for a map command,
then marks mapped areas transferred before returning. It is not sound-CPU-off
through subsequent caller uploads. Exposing a new bank in that initial map
before uploading its contents is unsafe ordering. Our earlier mocks did not
model those SGL internals; the native HLE smoke did not expose the owner's
failure. tools/audit-fire-hit-startup.py pins the exact SH-2 instruction windows.
This evidence supports isolating the new bank from the parent's bootstrap; it
does not prove precisely which WebRetro request stalled.

## Repair

1. Bootstrap with unchanged WMUSIC.MAP56, original WDEATH/WMUSIC uploads,
   SND/SGL initialization and initial command order. No Fire bank is mapped here.
2. Complete the parent's041a/queue/map/DSP/CDDA/total-volume acknowledgments.
3. Upload WFIRE.TON fully, including DMA wait, before publishing WFIRE.MAP64
   at the existing sound-map location0xa000. Deferred reads enter /ALEVEL2 and
   restore the parent directory; initial loader reads keep their original scope.
4. Capture041a BEFORE SND_ChgMap(0), including synchronous consumption. Require
   fresh cursor progress, empty request blocks AND all combined-map entries to
   match before setting ready and allowing control preparation/gameplay.

There is no second SND_Init, driver reset, arbitrary delay,8838 readiness test,
watchdog extension or readiness bypass. The120-VBlank watchdog is retained.
Fire-map failures retain their own FIRE UPLOAD/FIRE MAP/FIRE MAP ACK operation.
Timeout diagnostics now report the first queued request ID even at BOOT_CPU,
if one is present. Diagnostic paths never submit commands.

## Map ABI and resources

Working parent:56 bytes,28 words to SND_Init,60-byte backing buffer (four-byte
lookahead);56 bytes to slInitSound. Broken feature:64 bytes,32 words,68-byte
backing; those counts were internally correct, not a proven padding error.
Repair: restore56/28/60 for bootstrap; later copy exactly64 bytes from the
unchanged WFIRE.MAP and acknowledge it. The combined map is not passed through
a second initializer. Existing WDEATH/music entries and every mapped address
remain unchanged. The Fire bank remains at447588, PCM447676. Hit remains at
control2/channel8, old PCM180832. SCSP high-water/free remain485812/38476 bytes.
VDP1 remains33792 bytes/28 definitions/81 max commands; VDP2 remains65792 payload/
434176 reserved; CRAM32. No resource allocation increase.

Fire free-first/oldest retrigger, surviving-hit events, Hit restart, lethal/miss
silence and Explosion5-tick/eight-event scheduling remain byte-identical.
Music control0/gain127/start behavior and independent Flame channels remain.

## Regression coverage and approval

Current-source tests enforce56-byte bootstrap,28-word initialization and
lookahead, no early Fire upload/publication, resident tone before map publication,
deterministic outer request prefix8/12/128/130 then8/12/128/130 then Fire-map8,
synchronous consumption, stalled Fire-map rejection/retry,041a checks and
read-only timeout diagnostics. Mutations reject an early combined bootstrap,
8838 alias and late cursor snapshot. Fire/Hit/SFX stress, resource/native allocator,
current gameplay/UBSan and full historical reference regressions remain active.
All old locks are untouched; an additive startup-repair lock records the exact
intentional source delta and updated startup section hash.

Final delivery requires a committed, fresh detached checkout and full
verify-canonical-build.sh. Native smoke may confirm loading and correct Fire/Hit
assignments but DOES NOT establish WebRetro equivalence. Owner WebRetro testing
is required before calling this repaired/approved in that environment.

Manual Actions: workflow from main, profile stage-default, exact repair source
SHA from the delivery response. No Actions run or tag change is performed.
