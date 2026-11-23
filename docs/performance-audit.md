# Mullet Force Phase 1 performance audit

The production configuration requests **one frame per VBlank at 320 × 240 NTSC**, nominally 60 FPS with about 16.7 ms per field. A pinned Yabause HLE replay reproduced gameplay pacing gaps during background streaming and the Bruce bank install. The replay measured 227 gap events and 304 missed VBlank opportunities during gameplay. **Real-Saturn performance is unverified.** No physical Saturn or capture feed was available for this run.

- Approved base `9ab6f908f6b736bea924fe223050be1a6c32b712`
- Diagnostic sources `85788c90d4d7e0d6ece8612dd2c39be71d5d0e18` on `performance-audit`
- Jo Engine SDK `556d081146211b6a1cfa6591d70f9487d406758b`
- Yabause libretro `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, interpreter, HLE BIOS, one rendering thread

## Frame loop and measurements

`make/saturn.mk` selects SGL, NTSC and the 2D build. The pinned SDK defaults `JO_FRAMERATE` to 1 and passes it as the third argument of `slInitSystem`. Jo's `jo_core_run` runs registered callbacks, then calls `slSynch()`. The SGL VBlank callback chain polls peripherals and increments the game's clock. Input edges are sampled once per VBlank. Gameplay takes elapsed VBlank ticks, applies the existing six-tick catch-up cap, and draws once per callback. Bank transitions use the existing freeze, drain and resync path. The replay observed one callback per VBlank outside stalls and zero callbacks that started in the same VBlank as the preceding callback.

The audit reads the master SH-2 free-running timer at its existing prescaler. It extends the 16-bit timer at the VBlank hook and checks that hook intervals match the configured clock. Yabause reported 60.000 FPS, an FRT divider of 32 and 13,996–13,997 timer counts per gameplay field. These translate to about 16.68 ms using the SDK NTSC clock estimate of 26.847 MHz. A timer fault indicates a suspect interval. Timing across an interrupt-masked interval that exceeds the counter wrap can undercount elapsed time. IRQ time and blocking calls are included in callback elapsed time.

- **Pacing** counts VBlank opportunities between callback starts. A gap of two means one missed callback opportunity. The callback before the gap is the one that consumed the time. The counter is separate from displayed buffer swaps and from simulation catch-up.
- **CPU** measures the game callback through the end of submission, before diagnostic text formatting and `slSynch()`. Logic includes AI and animation updates. AI covers street enemy and Bruce updates. Render includes VDP2 streaming. Audio covers the Level 1 music and SFX dispatcher. Bank time contains the existing VDP1 fence, suffix install and validation. The nested measurements overlap.
- **Graphics completion** uses read-only VDP1 EDSR observations at callback entry, exit and the SGL VBlank hook. The current-end flag (CEF) reflects completion status at that sample point. A clear flag can also reflect the start of a new list. The callback gap includes engine work, synchronization and idle time. Neither callback time nor the sampled status yields VDP1 raster duration or the exact frame-change deadline. The pinned emulator sets CEF within its synchronous draw path. All gameplay VBlank samples in this replay had CEF set, so that result cannot establish Saturn VDP1 headroom.
- **Graphics transfers** count VDP2 pattern and name-table bytes written by the background ring and installed VDP1 texture payload bytes at a suffix swap. The tile-upload probe times the pattern stores. The streaming probe also includes tile lookup, cache management, ring maintenance and prefetch work. Bruce install combines synchronous reads, TGA processing, VDP1 uploads and validation, so the individual share of CD latency or DMA is unknown. Per-field primitive counts come from the emulator's VDP1 command dispatcher, including any commands that the renderer clips.

## Controller replay results

5,200 emulated fields from cold boot. The first two P1 Start presses exited the gallery and started gameplay, then P2 joined. Both pads charged the torch and used intermittent attack holds while moving through the city, downhill, the vehicle encounter and the arcade lot. The frontend read work RAM without game-state injection. It kept the overlay off for the timing run and used a separate run for the overlay check.

Rows overlap. CPU columns show median and maximum per completed callback. Missed VBlanks are attributed to the preceding callback.

| Scenario | Callbacks | CPU median / max | Missed VBlanks | Peak VDP1 primitives per sampled field |
|---|---:|---:|---:|---:|
| Opening two-player combat, before the traversal | 318 | 1.90 / 2.13 ms | 0 | 36 |
| Maximum population, all three street slots occupied | 2,153 | 2.21 / 149.36 ms | 220 | 44 |
| Flamethrower active, across stationary and scrolling scenes | 1,371 | 2.18 / 104.68 ms | 77 | 43 |
| Downhill ring updates, outside the active car pass | 93 | 23.63 / 112.74 ms | 90 | 39 |
| Vehicle ambush, active car | 350 | 2.02 / 2.21 ms | 0 | 38 |
| Bruce active, including scrolling into the lot | 881 | 1.72 / 27.99 ms | 12 | 21 |
| Bruce active without pattern, map or decode work | 812 | 1.71 / 1.86 ms | 0 | 21 |
| Bruce suffix installation | 1 | 754.34 / 754.34 ms | 45 | 12 |

The worst regular gameplay callback was at camera X 1360. It spent 147.05 ms in streaming, including 128.57 ms in decoding 30 blocks and 0.56 ms writing 1,984 pattern bytes. The next callback started nine VBlanks later. The worst downhill ring update took 110.60 ms in streaming. The peak pattern-store time across the replay was 0.73 ms, and the largest writes per callback were 2,432 pattern bytes and 86 name-table bytes.

CPU-side rendering outside streaming peaked at 2.13 ms. Logic, its nested AI section, and audio peaked at 1.19 ms, 0.65 ms and 0.18 ms respectively. No pacing gap followed a callback that lacked both substantial streaming and bank installation work. The largest observed primitive count was 44. The vehicle and stationary Bruce samples had zero missed opportunities at their respective command counts. These results attribute the reproduced misses to CPU-side work in the emulator. Saturn VDP1 raster fill, bus contention and SCU DMA timing still need hardware measurement.

## Three measured bottlenecks and next changes to evaluate

| Priority | Verified in this emulator run | Candidate optimization and risk |
|---|---|---|
| 1 | **Background block decompression on the frame path.** Streaming preceded 226 of the 227 gap events. Decode alone exceeded a field in 12 callbacks and reached 128.57 ms. The current two-block prefetch limit applies to speculative work. A demand miss can synchronously decode many additional blocks. | Improve ahead-of-camera block ordering and make the existing CPU cache prefetch useful at tile-column deadlines, including direction reversals. Keep the live map and art, and verify both scan-out windows and all memory limits. High expected benefit to recurring stalls, medium risk. |
| 2 | **Ring and cache work outside decoding and pattern stores.** The residual reached 17.93 ms and accounted for 3.17 s across the 226 streaming callbacks that preceded gaps, compared with 2.11 s of decode and 0.11 s of pattern stores. This is an aggregate that includes map traversal, cache replacement/copies, prefetch queue work and probe overhead. | Time ring marking, cache copies, eviction search and prefetch construction separately before narrowing the change. Reuse work over the unchanged portion of the visible ring and its guard wherever the existing residency invariants permit it. High expected benefit if the same costs appear on hardware, medium risk. |
| 3 | **Synchronous Bruce bank install.** The single swap installed 162,240 texture bytes, spent 752.45 ms inside install and was followed by 45 missed opportunities. The existing draw-complete fence took about 0.006 ms in this replay. The three drain intervals were intentional and each remained one VBlank. | Isolate CD fetch, decode, VRAM copy and validation first. If CD dominates, evaluate a sequential asset pack or bounded prefetch using existing staging memory while preserving the visible front buffer, palette ownership and suffix fence. High benefit at the handoff, higher implementation risk and lower frequency. |

No optimization was applied. The data does not support prioritizing AI, audio or a reduction in rendering quality.

## Build and validation

Build from the diagnostic source commit with the pinned SDK and normal stage profile.

```sh
MF_PERFORMANCE_AUDIT=1 bash tools/build-stage.sh --native
make check
make test
bash tools/run-performance-audit-emulator.sh 5200 walk
bash tools/run-performance-audit-emulator.sh 1650 overlay build/performance-overlay.csv
```

Open `mullet-force.cue` with its matching BIN. The game starts with the overlay hidden. Press **P1 Y** after starting gameplay to show or hide it. It refreshes every 30 VBlanks, with peak section times and mean/peak callback time in tenths of a millisecond. `GAP` is the latest callback spacing, `MISS` is the cumulative missed count, and `CEF0` counts samples with VDP1 current-end clear in the last refresh window. `MAP` is combined background-streaming time. Use the overlay run for observation and the hidden-overlay run for comparative timing. Disable the build flag for the production build.

The distributed executable was built from the diagnostic working tree before the source commit was made. Its displayed commit string is the approved parent, its branch is `performance-audit`, and its source manifest verifies against the committed diagnostic content. The bundle includes its BIN/CUE, timing CSVs and checksums. For the emulator CSV, select each new, nonzero `sequence` with `publishing=0`. Use `gap` from the following callback for attribution. VDP1 command counts are per emulator field, even on rows where the last callback repeats.

- The diagnostic and default native stage builds passed. The default link lacked the diagnostic sample symbol. `make check` and `make test` passed. All 433 non-executable files on the diagnostic disc were byte-identical to the approved baseline.
- The diagnostic link end is `0x060b5534`, an increase of 3,152 bytes against the approved build. It is 43,724 bytes below the `0x060c0000` SGL sort-work boundary. The probes use static work RAM and do not allocate from the heap or use VDP1 texture, VDP2 graphics, or SCSP sample memory. The overlay uses Jo's existing text plane.
- Compared with a separate approved baseline HLE run using the same input schedule, the diagnostic reproduced identical per-field VDP1 list and primitive counts across 5,200 fields. The bottom text-band pixel hash matched in 5,175 fields. The other 25 differed during traversal, so exact field-by-field visual equivalence was not established. The sampled text band differed only from field 1294 through 1462 during the overlay A/B run, matching the two toggle inputs.
- The FRT run published no timer faults, and the replay reached all six requested scenarios. The latest diagnostic source fingerprint passed `sha256sum -c build/SOURCE-SHA256SUMS.txt`.

## Saturn validation pending

Use the matching diagnostic disc on an NTSC Saturn and record the console revision, boot medium or ODE, and a 60 Hz capture. Repeat three passes with the overlay hidden for pacing and with it shown for measurements. Record the first stable counter value and the ending counter, and log the peak CPU, DRAW, MAP and BANK readings. Capture stationary two-player attacks with three enemies, simultaneous torches, downhill traversal both ways, the vehicle warning through the end of the pass, and the full Bruce entrance and fight. Repeat the approach and backtrack to measure both bank directions. Record PAL separately if tested, since 50 Hz is a different timing budget.

For exact VDP1 duration, correlate draw trigger and draw-end events with VBlank and buffer change on hardware. Take those readings alongside CPU scope timing. The sampled EDSR flags can point to where to measure, but cannot time the rasterizer or disambiguate the current and previous command lists on their own. Phase 2 prioritization depends on which emulator findings reproduce on the console.
