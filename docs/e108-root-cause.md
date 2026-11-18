# Level 2 startup E108 investigation

The owner-approved baseline is annotated tag `the-one-poowah-final-audio-definitive` at executable source `7a55bae6b6428faec7300df7c82a2e4669f5063b`. The delivery ZIP at `43113df8b10979177694fe8d7aa8e502d4a5ca9e` has the tag's SHA-256 `c8d353635da37be004ac67d70a824b478b3e8e35c4fea71c056e5c515285cba9`. Its BIN matches `d32680c5686ea9f1850a0d86096090c1f3c865ca27f5d297f2be66d8688c5bd7`. A fresh pinned build reproduced the exact approved `/0.BIN` executable hash `a5f7ba4c4a7444c50b819355ad1af13005e3682fd89740774038e5a4b59be8cf`. The approval record explicitly defers E108.

## Error identity and reproducible failure

`src/wingsuit_runtime.c` assigns the game-local error 108 on synchronous audio load failure and asynchronous startup rejection or timeout. It prints the decimal value in the load-error screen. The same number can have distinct causes. `WDEATH BANK` is a startup umbrella label. Neither the Jo Engine error handler nor Sega's GFS code table gives the two strings this meaning. Historical E008 remains unidentified. The earlier E008 report has no complete screen or executable identity that distinguishes a different producer from a misread E108.

Held inputs are Saturn Start twice to leave the gallery and enter Level 1, P2 Start to join, and Saturn X to exercise the existing transition. The latest production world does not auto-clear after 40 KOs. `MF_LEVEL1_WORLD_FLOW` compiles out that trigger and the current world has no endpoint clear, so X is the supported route to the existing settling, clear, resource load and Level 2 startup. No production stage trigger was added for testing.

On Yabause `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, HLE BIOS, the exact approved BIN passes an early shortcut and fails reproducibly when X is pressed at frame 17000. Fresh launches with and without a long Level 1 pause failed at frame 17344. The failing 68000 was running with the request bit set and the queue gate already patched to NOP mode. Cursor 0x041a reached 0x0040 and stopped, while timer 0x8838 advanced to 0x041c. Pending queue IDs were `0c 80 82`. A read-only stack dump contains return addresses `0x1d9a`, `0x1cb4` and `0x10fa`, which place the sound CPU in the standalone StopDsp handler from the driver dispatcher. The frame-level PC repeatedly sampled the 0x5450–0x546c slot-envelope scan and the intervening timer interrupts. The prior lost-request-notification fix was already active.

Driver 2.10 publishes the history cursor before it finishes each handler. Command 0x0c enters 0x1d92, then calls 0x542e. The latter loops over 32 cached envelope words at `0x803a + 64*i`, waiting for their low nibbles to clear, with a 16-bit loop budget. The observed failure retained 18 cached low nibbles of value 2. A repeat with successful SMPC stop and the redundant restart removed produced the same DSP loop and E108 at frame 17343. Its emulator internals reported zero keyed slots and zero active envelopes. In the pinned legacy Yabause SCSP implementation, a slot can reach the inactive envelope counter and stop being updated while its last amplitude remains in `slot->env`, which the monitor still uses. This accounts for the stale envelope observations in the HLE reproduction. Hardware may have a different raw state.

The pinned driver's map change at 0x19ea calls 0x317a to key off all slots and clear their cached envelope words before it calls the same DSP stop routine at 0x542e. The standalone command omits that cache initialization. The test candidate retaining the map changes and removing only the two standalone stops from the checked-stop/no-restart candidate reached gameplay in the matched late scenario at frame 17345.

## Startup correction

- `mf_ws_runtime_begin` uses the SGL-documented INTBACK cancellation before the three existing VBlank drain barriers. A rejected cancellation fails visibly. `mf_ws_runtime_frame` restores normal peripheral polling after the synchronous load, including on load failure. `load_resources` requires a successful SGL stop command before clearing sound RAM.
- `mf_ws_audio_load` checks its own sound-off result and relies on the 68000 start and map acknowledgment already performed by `slInitSound`. A successful extra start was observed to reset command history and discard or alias the very requests being used to establish readiness. In a separate cancellation-only pilot, the queue drained and its cursor returned to the starting value 0x0030, so the watchdog reported E108 on an otherwise live driver.
- `mf_ws_audio_load` and `startup` leave the actual DSP shutdown to the acknowledged map changes. They retain the original watchdog, command notification, consumed-command and queue checks, exact map descriptors, CDDA and volume sequencing, staged Fire upload, and all existing note/scheduler code. No new delay or timeout is used.
- The on-device bounded trace already in THE ONE remains the diagnostic for failure. Test-only emulator probes read the 68000/SH-2 registers, work RAM, sound RAM and native SCSP state. They never patch running game state.

## Startup audit and memory

| Resource | Approved | Candidate |
|---|---:|---:|
| Level 1 VDP1 textures / definitions | 371,072 B / 177 | 371,072 B / 177 |
| Level 2 VDP1 textures / definitions | 33,792 B / 28 | 33,792 B / 28 |
| VDP1 texture capacity / definitions | 458,488 B / 255 | 458,488 B / 255 |
| VDP2 reserved | 434,176 / 524,288 B | 434,176 / 524,288 B |
| Level 2 VDP2 uploaded background | 65,792 B | 65,792 B |
| Level 1 SCSP high-water / free | 521,304 / 2,984 B | 521,304 / 2,984 B |
| Level 2 SCSP high-water / free | 506,660 / 17,628 B | 506,660 / 17,628 B |
| Fixed Jo work-RAM heap | 393,216 B | 393,216 B |
| Level 2 startup trace | 4,756 B | 4,756 B |

`jo_main` initializes Jo once. The transition reuses the engine and the VDP2 allocations. It drains VDP1 through real VBlanks, checks the draw-end bit, retires the sprite definitions, and restores explicit SGL sprite window, priority and automatic draw state. The background cache and enemy suffix retire before the Level 2 loader. The Level 2 loader transfers VDP2 cells/maps and 32 palette bytes while preserving the SDK text/font region. These operations preceded the reproduced E108, and the failing trace reached the final audio commands with the expected driver signature and no driver error word.

`/ALEVEL2` keeps stage files addressable through the pinned GFS directory bound. The app checks file existence and declared size, reads synchronously, restores the parent directory, and waits for SCSP DMA before freeing sources. The deferred Fire load repeats this directory scope and validates the new map only after the tone copy finishes. The current inherited graphics DMA contract and the Level 1 SND_Init map argument warrant separate review. The pinned movie/graphics DMA API can return before transfers to mapped VRAM finish, while several graphics paths release source buffers through Jo's original helpers. Also, Level 1 passes the MAP byte count to the library parameter that the pinned SDK interprets as words. Neither path was correlated with the reproduced sound-driver stall. This branch preserves both.

The shipped Level 2 map backing already covers the pinned SDK's four-byte aligned lookahead. The native map and runtime test guards verify work-RAM image and heap placement. Test targets preserve the approved audio payloads, gains, SFX priorities and combat/AI/rendering source. The existing host suite runs on the approved reference, with the candidate's actual runtime loader and audio transport tested separately. The emulator evidence does not establish timing on a physical Saturn.

## Reproduction and manual build

```sh
bash tools/setup.sh
bash tools/build-stage.sh --native
make check
make test
python3 tools/test-e108-cold-starts.py --out build/e108-cold --cold 50 \
  --start-frame 800 --skip-frame 890 --spread 50
python3 tools/test-e108-cold-starts.py --out build/e108-late --cold 1 \
  --skip-frame 17000 --spread 1 --timeout 420
```

Use a new output directory for every run. Each cold trial uses a fresh emulator process and save directory. The optional `--warm` suite uses the core's reset entry point. `--stress` keeps the game running under two-player inputs after Level 2 gameplay begins. The tests in `make test` additionally poison sound RAM across repeated host-model audio loads.

In GitHub Actions, select **Manual Saturn playtest build**, then **Run workflow**. Use workflow branch `fix/e108-root-cause`, profile `stage-default` and the full investigation source SHA as `source_ref`. Verify the resolved SHA in the run and `BUILD-INFO.txt`. Download `mullet-force-stage-default-<SHA>` within one day and open its matching CUE. No Actions dispatch is required to push this branch.

On Saturn, verify both fresh power-ons and console resets, Stage 2 loads soon after starting Level 1 and after sustained music and combat, and pads on both ports across the transition. If error 108 recurs, capture the full screen and A trace pages, model and loader, BIN hash, and cold/reset history. Capture any literal E008 separately with the full screen. See [SGL peripheral and wait-mode reference](https://docs.exodusemulator.com/Archives/SSDDV25/segahtml/sgl/sglr/hosoku/hosoku.htm), [Sega technical bulletin 51](https://antime.kapsi.fi/sega/files/ST-TECH-51.pdf), [Sega SCSP envelope reference](https://www.infochunk.com/saturn/segahtml_en/hard/scsp/hon/p04_22.htm), and [Jo Engine error API](https://jo-engine.org/doxygen/core_8h.html).
