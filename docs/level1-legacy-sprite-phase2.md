# Phase 2: remaining legacy registrations

Branch: `optimization/level1-legacy-sprite-phase2`.
Exact parent: owner-approved Phase 1 `ea6e3e8bc59340226218366573bb9337e9dd0cff`.
Its parent is `15387a314a51bffbe3e65152e45958ed5f3416c5`, still the target of
`the-one-ai3-baseline`. Phase 1 remains available on its original branch.
The delivery message identifies the exact commit containing this report.

## Retired registrations (83)

Every name below includes the `.TGA` extension. Only production registrations
are skipped; all original files remain committed and staged on disc.
The exact expanded list and per-group budgets are in
[`assets/legacy-sprite-phase2.json`](../assets/legacy-sprite-phase2.json).

| Group | Exact names/ranges, inclusive | Definitions | Bytes |
|---|---|---:|---:|
| Player fallback | BU00, BU02–BU07, BU09–BU10; CH00–CH07, CH09–CH10; NL00–NL10 | 30 | 70688 |
| Bat overlay | RBV01–RBV09 | 9 | 7360 |
| Combat | COMBAT/CA08–CA27, COMBAT/CA36–CA50, COMBAT/DT0–DT1, COMBAT/CA53–CA59 | 44 | 29920 |
| Additional Phase 2 total | | 83 | 107968 |

| Profile | Definitions | Texture bytes | Free bytes |
|---|---:|---:|---:|
| Original AI 3.0 | 255 | 452800 | 5688 |
| Approved Phase 1 | 237 | 386848 | 71640 |
| Phase 2 | **154** | **278880** | **179608** |

Cumulative recovery: **101 definitions / 173920 bytes**. No duplicate consolidation,
HUD panel reduction, bank architecture, enemy-count or gameplay changes.
There are 140 payload registrations and the same 14 crop/tail views.

## Dependency and ID safety

`MF_LEGACY_SPRITE_PHASE2` defaults off; only the production stage-default wrapper
enables it, together with Phase 1. Compile-time guards require all the approved
HQ, fast-bat, running/carry, sequence and jab replacement paths. Historical
profiles retain the exact original loading path. Removed handles are explicitly
invalid; retained handles still use allocator returns, with no numeric remapping.

Source reachability was rechecked against the old read-only inventory and the
approved renderer. HQ death/hurt/jump/combat/movement/torch helpers consume all
legitimate production states before legacy BU/CH/NL fallback branches. Fast
running bat uses the existing carry and the horizontal contact key; ordinary jab
uses key 0, horizontal contact key 1, cross uses COMBO plus shared lower, and
recovery uses movement pieces. Thus only CA00–CA07 / CA28–CA35 and RBV00 are
needed from these banks. Slow/planted sequence keys remain for historical profiles.
No active animation tables, renderer or gameplay functions were changed.

Actual approved Phase 1 render instrumentation also asserts that **none of the
83 candidates is drawn** in the exercised states. The optimized renderer rejects
invalid IDs in the mock, and decoded crop views must resolve wholly inside
retained texture storage. The allocation audit checks exact retained order,
dimensions, formats, registration palettes, bounds, nonoverlap and physical end.
The allocator's tail metadata/sentinels and all 14 views remain intact.
RBV00, both retained combat ranges, GB/GC/AB/AC/RN/RD and all HQ/COMBO banks remain.

## Changed files

- `src/main.c`: conditional BU/CH/NL registrations only.
- `src/animation_preview.c`: conditional RBV/COMBAT registrations, preflight and
  exact byte accounting only; all animation drawing/update code unchanged.
- `src/arcade_fx_config.h`: default-off guarded flag and group-specific budgets.
- `tools/build-source-complete.sh`, `tools/build-native.sh`: production flag and
  build provenance/manifest accounting.
- `tools/audit-sprite-memory.py`: Phase 1 counterfactual and exact Phase 2 assertions.
- `Makefile`, `tools/validate-legacy-sprite-phase2.py`: immutable baseline regression
  chain and Phase 2 scope gate. Archived test builds exclude staged current source
  headers so the archived profile is compiled against its own original headers.
- `tools/test-legacy-sprite-phase2.py`: actual allocation and renderer comparison.
- `tools/test-legacy-sprite-runtime.py`: optional deterministic Yabause comparison.
- New manifest and this report.

All other Phase 1 files are compared byte-for-byte by the preservation gate.
This includes AI 3.0, player inputs/FF+A, collision, gameplay timing constants,
stage progression, audio scheduler/music/samples, flame sustain, E108 notification
repair, Level 2 loader/graphics/gameplay, and the simultaneous enemy limit of two.
Main's entire renderer/update body is identical. Animation renderer/update bodies
are identical after removing accounting-only subtractions from loader checks.

## Validation

- Native `bash tools/build-stage.sh --native`: passed with pinned SDK
  `556d081146211b6a1cfa6591d70f9487d406758b`; matching local BIN/CUE generated.
  Existing baseline compiler warnings remain; no compiler pin/build flags changed.
- `make check`: passed, including disc/export validation and original preservation
  chain, archived Phase 1 tests and current Phase 2 allocation/semantic tests.
- `make test`: passed, including both actors, combos and FF+A buffering, AI 3.0,
  flame/audio scheduling, parallax/stage clear, wingsuit controls/shooting/focus,
  renderer tests, actual loader/WDEATH/readiness and restart cases. The inherited
  runtime suite also passed 16 fresh host processes; these are mocked tests.
- Actual current allocation audit: exact table above. Phase 1 counterfactual:
  237/386848. Historical profiles (cleanup off) retain 255/452800, FX-off
  255/453344 and FX-off/combo-off 253/446304.
- Host semantic comparison: **7198 cases / 140391 draw commands**, actual Phase 1
  versus Phase 2, Phase 2 disabled, and historical profiles. Exact decoded pixel
  hashes (including all cropped aliases), rendered palettes, dimensions, positions,
  scale, flip, depth and ordering match. Both actors/facings, idle/walk/run,
  jump/landing/kick, all combo phases, fast bat phases, hurt/death, torch,
  enemy states, impacts/explosions, HUD, gallery/review and stage clear exercised
  under undefined-behavior sanitizer. No candidate draw consumers were found.
- `git diff --check`: passed.

### Palette-state difference

The first semantic test detected that fallback palette banks **2 and 3** no longer
receive the retired BU/CH/NL uploads. Instrumentation proves neither bank is used
by any indexed draw in the approved profile. All palettes actually used for
indexed rendering are compared exactly and match. The unused banks remain
allocated in their original positions, so later palette IDs and CRAM dependencies
are preserved. No rendered palette or palette asset changed. Historical profiles
continue populating both banks as before. This state difference is explicitly
reported rather than silently ignored by a blanket palette comparison.

### Deterministic emulator evidence

Yabause libretro `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, HLE BIOS,
software/interpreter, one thread, no cartridge, fresh save directories. Both
programs ran 2400 frontend frames using physical controller inputs. Two cold runs
per build were performed: an initial wall-clock schedule and the final Level 2
stage-local schedule. Both pairs reached Level 2 gameplay with zero errors.

The final comparison used the existing approved **X development stage skip** at
frame 1500, followed by the unmodified settle/clear sequence, VBlank drain, sprite
teardown, real Level 2 registration, WDEATH initialization and driver readiness.
No emulator RAM writes, safety-check bypass, game patch, delay or timeout changes.
This is not a natural 40-KO completion test.

- Level 1/stage-clear: **600 full simulation snapshots** and **30 images** at
  matching wall frames, all identical.
- Level 2: **555 full simulation snapshots** and **545 pixel images** at matching
  gameplay ticks, all identical. Controller script covers two players, movement,
  banking, shots and held focus/beam input. Final sprite ID is 27 in both builds:
  the same 28-definition Level 2 bank was successfully installed.
- Every captured runtime error value was zero; both reached loader phase 3.
- A real loading-duration difference was observed: Phase 2's drain/load completed
  at frontend frame **1720**, versus **1721** for Phase 1; Level 2 gameplay began
  at **1843**, versus **1844**. The title/readiness interval remained the same.
  The first wall-clock schedule consequently produced a one-tick Level 2 offset.
  Final comparison drives inputs relative to the actual Level 2 tick and confirms
  identical gameplay/rendering. With that schedule, raw wall-frame comparison
  still has 558 state and 556 image differences due to this load-phase offset;
  the equal-tick comparison has zero. No artificial delay was added to align loads.
  No gameplay speed/timing constant changed.

The optional script emits raw frame captures, read-only save-state traces and
`comparison.json`, including the raw wall-frame mismatches. Reproduce with a
locally built core and preserved Phase 1 BIN/CUE + SH COFF `game.elf`:

```sh
python3 tools/test-legacy-sprite-runtime.py \
  --core /path/to/yabause_libretro.so \
  --include /path/to/libretro-common/include \
  --phase1-cue /path/to/phase1/mullet-force.cue \
  --phase1-program /path/to/phase1/game.elf \
  --phase2-cue build/mullet-force.cue --phase2-program build/game.elf \
  --out /tmp/phase2-fresh-comparison
```

The tool extracts per-build addresses from the real COFF symbol tables and
records full game/wingsuit structs; it does not assume stable addresses/IDs.

## Limits

No real Saturn testing or audible listening comparison was performed. The HLE
emulator tests are not proof of hardware behavior or an intermittent-error cure.
No new E108 repair was attempted: the approved repair is byte-identical. Owner
playtest should confirm music/SFX/flame sustain and a natural stage completion on
the target setup. Phase 1 remains the approved fallback. No Phase 3 work began.

## Playtest build

No workflow dispatch tool is available, and local `gh` reports an invalid GH_TOKEN.
No downloadable Actions artifact is claimed. On GitHub open **Manual Saturn
playtest build** (`.github/workflows/build.yml`), then **Run workflow**:

- Workflow branch: `optimization/level1-legacy-sprite-phase2`.
- `profile`: `stage-default`.
- `source_ref`: the full pushed commit SHA in the delivery message.

Wait for native build, `make check` and `make test` to succeed. Download
`mullet-force-stage-default-<resolved-full-SHA>` from that run, and keep the BIN/CUE
together (existing artifact retention is one day). For a local build, run
`bash tools/setup.sh`, install README prerequisites, then
`bash tools/build-stage.sh --native`, `make check`, `make test`.
