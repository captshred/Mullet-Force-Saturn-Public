# Level 2 turret build: driver-ready false timeout

Branch: `fix/level2-turret-load-e008`.
Failing parent: `c69713001222729012649aeea1e4f1fd98c5b19b`.
Last visually confirmed working parent: `812ecb6a8a22bc0de8ab698e6da4e8158a4d803e`.

## Diagnosis and evidence

The reported E008 text corresponds to this source's **E108** path. During the
Level 2 title, `mf_ws_runtime_frame()` calls `mf_ws_audio_step()` and rejects a
negative `mf_ws_audio_ready()` result. It displays `WDEATH BANK` plus the specific
diagnostic from the audio startup state machine. `startup_timeout()` produces
`DRIVER READY / EXPECT 1 GOT 0` while waiting in `BOOT_CPU`. This is an
asynchronous readiness failure after bank upload, not a missing-file diagnostic.

WDEATH is the existing stage-local sound bank: MAP describes the bank's native
SCSP addresses, SEQ is its retained native sequence resource, and TON holds the
explosion, player shot, Flame Attack and Flame Loop programs/PCM. Level 2 releases
the Level 1 sound bank at transition and must install and acknowledge this bank
before gameplay. The fix retains all three exact files and all audio parameters.

The old readiness condition required **both** an empty command queue and a
change in sound-RAM word **0x 8838**, sampled after submitting the startup
commands. The comment described that word as a timer heartbeat. The pinned
68000 driver proves that this is not a monotonic progress signal:

| Driver offset | Actual behavior |
|---|---|
|0x 17a 0|`ADDQ.W #1,0x1838(A6)` increments an interval counter; A6=0x 7000 gives RAM0x 8838|
|0x 1bd 4|Command dispatcher increments its history cursor by 16|
|0x 1bd 8|Stores cursor in private word 0x 883a|
|0x 1bdc|Publishes the same cursor in exported status word 0x 041a|
|0x 1be 0|Copies interval 0x 8838 into the command-history record|
|0x 1be 4|**Resets interval 0x 8838 to zero on command consumption**|

The old test can therefore reject a live driver whose requests have completed:
its sampled interval may equal its initial zero after dispatch. This is a
phase-dependent false negative. It is not evidence that the WDEATH file is bad
or that the 68000 never ran. The old host `pump()` always incremented the timer
and cleared requests without modeling the command dispatcher's timer reset,
which is why the previous 247 PASS reports did not cover this condition.

A new test reproduces the exact reported diagnostic with a consumer that really
drains requests and publishes progress, sampled immediately after dispatch:

```
old: ready=-1 cause=DRIVER READY expected=1 actual=0 timer=0 cursor=1984
fixed: ready=1 cause=SFX READY ... timer=0 cursor=800
```

The fixed test also compares the full MAP/SEQ/TON bytes in modeled sound RAM
against the actual runtime files. A second positive case consumes boot requests
inside `mf_ws_audio_load()` itself, testing the snapshot ordering. Negative cases
retain rejection of a stopped consumer and of cursor movement with an undrained
request. Existing map-ack, readiness watchdog, MIDI setup and failure tests remain.

## Small production fix

Only `src/wingsuit_audio.c` changes at runtime:

1. Capture exported command-history cursor 0x 041a **before** submitting the
   existing DSP Stop, CDDA Level and Total Volume requests.
2. In `BOOT_CPU`, require that cursor to have changed **and** all eight request
   slots to be empty.
3. Continue the existing map acknowledgement and all sound-control preparation
   before reporting startup success. The 120-tick watchdog remains unchanged.

The early snapshot matters: a healthy 68000 can finish requests before the
loader returns. Sampling after submission would introduce another false timeout.
No delay, validation bypass, placeholder, driver replacement, audio disable,
asset modification or capacity change is involved. Cursor progress is positive
consumer-owned evidence; zeroed queues alone do not establish readiness.

## Comparison of the two reported commits

The turret commit did not edit `wingsuit_audio.c`, its header/data definitions,
`music.c`, the sound driver or the WDEATH bytes. Its new static textures and
extra gameplay state alter executable layout and loading work, exposing a
readiness test that depends on an unrelated interval sample. This investigation
does **not** claim an observed WebRetro trace linking one particular DMA cycle
to the interval sample: the reproducible defect is the invalid readiness
predicate, and target verification remains outstanding.

Native builds of both reported commits contain the same complete 26610-byte
pinned driver, including its final SEGA boot signature. SHA-256:
`68890ee4a49fd0c341bc3f0a48643e4db4b175df0b0d7dacfeb88306340052b6`.
In the locally reproduced images its source moved from 0x 060322ec to 0x 06032ba 8;
both copies match the driver exactly. No source-driver corruption was found.
BSS ends moved from 0x 060a 1ac 4 to 0x 060a 3a 14, below the existing SGL work area at
0x 060c 0000. The turret's VDP1 allocation and arrays remain within their declared
bounds. These are native layout checks, not proof that every target memory
access has been observed; no target memory-corruption trace was available.

## Regression coverage and preservation

`tools/audit-level2-driver-ready.py` SHA-pins the real SDK driver and executes its
five actual command-history instructions at 0x 1bd 4..0x 1be 8, including the128-record ring wrap.
It verifies the timer reset and exported cursor, rather than assuming their
semantics. This is a narrow instruction interpreter, not a Saturn/SCSP emulator.

`tools/test-level2-driver-ready.py` runs the actual C loader and startup machine
under UBSan with the corrected driver model. It also rebuilds two deliberate
mutations and requires them to fail: restoring timer 0x 8838 reproduces the exact
reported diagnostic; moving the cursor snapshot after submission rejects the
eager-consumer case. The test runs automatically through `make test`.

`level2-ready-lock.json` adds exact source-only exceptions to the existing
preservation chain. All previous lock files stay unchanged. New checks freeze
all turret/drone gameplay, sprite data, city/palette, camera/parallax, Level 1,
HUD/transitions, music, audio payloads/parameters, manifest and Actions workflow.

Resource limits remain exactly those of the turret implementation:

| Resource | Unchanged usage |
|---|---:|
|Aerial / turret slots|8 /2|
|Player / drone / turret bullet slots|32 /16 /4|
|Gameplay state|1,880 bytes|
|VDP1 texture bytes /definitions /command bound|33,792 /28 /81|
|VDP2 payload /reservation /unreserved headroom|65,792 /434,176 /90,112 bytes|
|CRAM payload|32 bytes|
|SCSP high-water /free|307,260 /217,028 bytes|
|Level 2 CD files /payload|26 /252,292 bytes|

The fix reuses the existing `boot_counter`; no extra runtime state or resource
pool is allocated. Native code placement may shift as it normally does after a
code edit. Drone dispersal, all five families, Chrome Eye paths, green turret
art, roof anchoring, target selection, bullets, durability and spawning are
byte-identical to the turret commit.

Reproduce after the pinned SDK/host dependencies are installed:

```
python3 tools/test-level2-driver-ready.py
bash tools/build-stage.sh --native
make check
make test
python3 tools/validate-level2-ready.py
python3 tools/validate-wingsuit.py --disc
python3 tools/check-preserved-audio.py
```

On this rootless host, use `PATH=/workspace/mf-host-tools/usr/bin:$PATH` for the
native build/check. The matching output files are `build/mullet-force.bin` and
`build/mullet-force.cue`.

Final automated results: native stage build produced matching BIN/CUE;
`make check` and `make test` passed (252 PASS reports). Focused readiness tests,
both negative mutations, exact ready/turret/night preservation, disc validation
and preserved-audio checks passed. Compilation retains the existing parent
`jo_print` const-qualifier warning; unrelated HUD/SDK code was not modified.

## Runtime limit and manual Actions verification

No compatible Saturn emulator/BIOS was available here. No actual disc transition,
WebRetro picture, audio audibility or hardware frame rate was verified. Native
compilation, instruction checks and host regressions establish the reproduced
failure mechanism and its correction; they do not prove WebRetro compatibility
or directly demonstrate restored on-target Level 2 gameplay.

Actions → **Manual Saturn playtest build → Run workflow**: use workflow from
`main`, profile **stage-default**, source_ref **fix/level 2-turret-load-e 008** or
the delivered full SHA. No workflow is dispatched automatically. Download and
keep BIN/CUE together; boot the CUE in WebRetro. Verify the real Stage Clear
handoff (or existing development X skip), completed Level 2 title/readiness,
working shot/Flame/explosion audio, all five drone families, Chrome Eye chains,
and both roof turrets through camera extremes and a 512-row repeat. The source
continues to display a specific failure if a consumer or map really is invalid.
