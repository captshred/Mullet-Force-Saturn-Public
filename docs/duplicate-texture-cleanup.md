# Phase 3: safe duplicate texture consolidation

Branch: `optimization/level1-duplicate-texture-cleanup`.
Exact parent: `8d4292ae63893f9b6593f3992aefddf60de0e155`, the Phase 2 working
candidate, **not a newly approved THE ONE baseline**. The delivery message names
the full commit containing this report. Phase 2 remains untouched on its original
branch. No tags moved or created; `the-one-ai3-baseline` still points to
`15387a314a51bffbe3e65152e45958ed5f3416c5`. No merge or further phase work.

## Verified candidates

The original read-only inventory (`work/level1-expansion-audit` in the development
workspace) marked COMBAT/CA02 and CA30 as duplicate candidates. Both are safe to
consolidate; no candidates were rejected. Evidence is locked in
[`assets/duplicate-texture-cleanup.json`](../assets/duplicate-texture-cleanup.json)
and rechecked by the new regression test.

| Duplicate | Canonical allocation | Dimensions / format | Per-resource recovery |
|---|---|---|---:|
| COMBAT/CA02.TGA | GB2.TGA | 80 × 12, indexed8 | 1 definition / 960 bytes |
| COMBAT/CA30.TGA | GC2.TGA | 88 × 12, indexed8 | 1 definition / 1056 bytes |

The complete files match byte for byte in each pair, including header, orientation,
palette and source index stream. Actual pinned-loader decoded index hashes are:

- CA02/GB2: `c6ec9f45d49dc960aaae4acd3eb6ae9c024bbfd808f87e286e86b90e38301131`.
- CA30/GC2: `51a5e3a50ced4093b2449c5493a9355d74ee2ad2d47a8843e90ff58aafe27306`.

The identical raw 256-entry BGR palette in all four files hashes to
`0bc5370c89a51dc3d4c41505c3dcef0748362af8c4135d4badaa09c632e302aa`.
Both uploads use the same `gallery_palette` object (bank 7), passed from
`mf_gallery_load` into `mf_animation_load`; drawing selects this same bank.
The pinned indexed TGA loader adds one to each raw index; transparent argument 1
maps raw zero to VDP1 zero. The resulting transparent pixel counts are 656 and
754 respectively. Dimensions, format, palette, transparent index, pixel values,
metadata and residency lifetime all agree, not merely appearance or a hash.

## Registration, consumers and lifetime

Canonical GB2/GC2 registrations are `gallery_parts[0][2]` / `[1][2]` in
`src/gallery_data.h`, loaded by `src/gallery.c:mf_gallery_load`. Their handles
are `pieces[0][2]` / `[1][2]`, passed as `idle_ids` to `mf_animation_load` and
stored in `resource_ids[2]` / `[23]`. Gallery rendering, idle/movement pieces,
jab recovery and the approved animation review share these resource mappings.

Duplicates were registered by `src/animation_preview.c:mf_animation_load`,
`ca_resources[2]` / `[30]`, into `ca_ids[2]` / `[30]`. `seq_lower[actor]` in
`src/attack_sequence_data.h` references those resource slots. Active consumers
are `ca_draw_list` (cross lower and fast-bat contact lower) and
`jab_adjusted_draw` (jab lower). Both players and facings use the same handles;
all positions, anchors and layering remain in their unchanged piece tables and
helpers. No consumer requires the old numeric sprite IDs.

Phase 2 numeric IDs were CA02=86, CA30=94; canonical GB2=31, GC2=34. The new mapping
uses allocator-returned `idle_ids[actor][2]`, **not these numeric constants**.
It checks handle validity and dimensions, assigns `ca_ids`, and skips the duplicate
upload. It neither registers a new view nor rewinds `last_resource` to the earlier
canonical allocation: the allocator continues from the preceding real payload.

Neither duplicate nor canonical allocation owns any of the 14 crop/tail views.
Both inventories explicitly check this. Every retained view is resolved inside
retained storage by the renderer test. All 14 views and their tail sentinels remain.
There are no runtime writes, replacements, DMA uploads or metadata mutations to
these four sprite definitions/payloads after boot. The only metadata writes in
this renderer create separate HQ crop/tail definitions from other resources.
All shared textures stay resident until the existing synchronized Level 2 teardown
frees the Level 1 bank; Level 2 registers its own fresh handles before drawing.
The emulator transition exercises that real path.

Skipping these TGA uploads also skips their palette-write side effects; the bytes
are identical to the canonical palette and all later upload/draw behavior remains
unchanged. The test compares **all seven complete palette banks** between Phase 2
and Phase 3, including unused banks, with no palette filtering in that comparison.
Historical profiles retain their prior palette population and are compared to
matching historical baseline profiles separately.

## Exact allocation

| Build | Definitions | Allocated bytes | Free bytes |
|---|---:|---:|---:|
| Phase 2 | 154 | 278880 | 179608 |
| Phase 3 | **152** | **276864** | **181624** |
| Phase 3 recovery | **2** | **2016** | |

There are 138 payload allocations and the same 14 zero-payload views. Cumulative
recovery from the original AI 3.0 build is 103 definitions / 175936 bytes.
No HUD panel resizing, unrelated removal or approximate artwork was used.
All original source/runtime assets remain committed and staged.

## Scope and changed files

- `src/animation_preview.c`: two explicit handle mappings and exact preflight /
  post-load accounting. All drawing, animation selection and update code unchanged.
- `src/arcade_fx_config.h`: default-off `MF_DUPLICATE_TEXTURE_CLEANUP`, requiring
  the full Phase 2 profile, and budget adjustments.
- `tools/build-source-complete.sh`, `tools/build-native.sh`: production flag and
  provenance/manifest accounting. Historical wrappers leave the flag disabled.
- `tools/audit-sprite-memory.py`: Phase 2 counterfactual and duplicate assertions.
- `Makefile`, `tools/validate-duplicate-texture-cleanup.py`: original immutable
  regression chain plus narrow Phase 3 scope gate.
- `tools/test-duplicate-texture-cleanup.py`: exact file/decoded pixel/palette,
  mapping, allocation, view dependency and renderer comparisons.
- New manifest and this report.

The preservation gate checks every other Phase 2 file byte for byte, including
main/input/game/AI 3.0, natural 40-KO progression, enemy limit two, backgrounds,
parallax/neon/HUD, attacks/FF+A, audio files/scheduler, E108 notification repair,
Level 2 initialization, graphics and gameplay. No runtime source outside the two
listed files changed; renderer/update bodies and all piece tables remain identical.

## Validation results

- Native `stage-default`: passed, pinned SDK
  `556d081146211b6a1cfa6591d70f9487d406758b`; matching local BIN/CUE produced.
- `make check`: passed, including disc/export validation, immutable preservation
  chain, archived Phase 1/2 checks and actual current allocation/semantic checks.
- `make test`: passed, including inherited player/FF+A/combo/AI/stage-clear,
  parallax, audio/flame, loader/readiness/WDEATH, wingsuit and cold/warm mock cases.
- Actual allocation audit: exact table above; retained registration sequence,
  dimensions/format/palette, bounds/nonoverlap, source-file presence and physical
  allocation end checked. Phase 2 counterfactual restores exactly 154/278880;
  Phase 1 and historical profiles retain their previous budgets.
- Full semantic comparison: **7198 cases / 140391 draw commands**. Phase 3 versus
  the exact Phase 2 source, disabled-cleanup profile, and historical profiles.
  Exact decoded texture hashes, complete palette state, dimensions, position,
  scale, flip, depth, order and animation sequences match. Both players/facings,
  all approved attacks, fast-bat phases, jumping/landing, torch, hurt/death,
  enemy states, impacts, HUD/gallery/review and stage clear are exercised under
  undefined-behavior sanitizer. Explicit integration assertions prove
  `ca_ids[2]==resource_ids[2]` and `ca_ids[30]==resource_ids[23]`.
- `git diff --check`: passed.

### Deterministic emulator comparison and timing investigation

The unchanged `tools/test-legacy-sprite-runtime.py` compared exact Phase 2 BIN/CUE
and program against Phase 3. Its argument/result labels `phase1` and `phase2`
mean the reference and candidate here: **actual Phase 2 and Phase 3**.
Yabause libretro `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, software/interpreter,
one thread, no cartridge, HLE BIOS, fresh save directories, 2400 frontend frames.
Two independent paired cold runs, followed by an additional read-only timing pair,
reproduced successful transitions with zero runtime errors.

Each run joins both players, drives attacks/movement, then uses the existing
approved development **X stage skip at frame 1500**. The real settling/clear,
VDP1 synchronization/teardown, Level 2 registration, WDEATH initialization and
sound-readiness checks run without patches, RAM writes or bypasses. This is not
a natural 40-KO completion test.

- **600 full Level 1/stage-clear state snapshots / 30 images** match at equal
  wall frames, with zero differences.
- **555 Level 2 state snapshots / 545 images** match at equal gameplay ticks,
  with zero differences. Two-player wingsuit movement/banking, shots, held focus/
  beam input and background scroll run normally.
- Both end with Level 2 sprite ID 27 (the same 28-definition bank), loader phase 3,
  and zero errors, including no E108.

A repeated **one-frontend-frame startup difference remains documented**:
Phase 2 enters Level 2 gameplay at frame 1843, Phase 3 at 1844. Both first show
load phase 1 at 1622 and phase 2 at 1720. The first post-load title/audio step is
observed at 1721 versus 1722; both decrement title from 120 to 114 using the
unchanged six-VBlank elapsed cap. Read-only traces show:

| Observation | Phase 2 | Phase 3 |
|---|---|---|
| First post-load title step (frontend frame / title / previous VBlank) | 1721 / 114 / 1346 | 1722 / 114 / 1354 |
| First completed audio startup (frame / remaining title) | 1761 / 82 | 1762 / 82 |
| Last title frame (frame / remaining title) | 1842 / 1 | 1843 / 1 |
| Gameplay entry | 1843 | 1844 |

`startup_failed` remains zero; readiness completes with 82 title ticks remaining,
so the extra frame is **not a late driver-readiness failure**. The offset begins
at the first title/audio step after synchronous loading; its deeper emulator/CD/
CPU scheduling cause is not established. No code change was made to mask it.
The raw wall-frame comparison reports 557 differing state snapshots and 556
images because of the offset. Stage-local input and equal-gameplay-tick comparisons
match exactly. Gallery's diagnostic memory counter also intentionally changes
from 278880 to 276864; that is not altered artwork.

Reproduce with the existing optional runtime tool, supplying Phase 2 files as
`--phase1-cue` / `--phase1-program` and current files as `--phase2-cue` /
`--phase2-program`, a built core via `--core`, its libretro include directory via
`--include`, and a fresh `--out` directory. The tool extracts addresses from each
SH COFF program and retains raw traces, images and `comparison.json` including
wall-frame mismatches. Supplemental timing reads inspect only the actual program's
`title`, `previous`, `startup_done`, `startup_failed`, `boot_clock` and audio-ready
symbols; they do not write emulator memory.

## Remaining limits

No real hardware or audible listening comparison was performed. Natural 40-KO
progression is byte-identical and covered by inherited host regressions but was
not completed naturally in the emulator. The one-frame title-entry alignment
variance is reported above; intended hardware should be playtested. No new E108
repair or claim of a permanent intermittent-startup cure is made. Phase 2 remains
available for hardware testing; no approved THE ONE baseline was changed.

## GitHub Actions / local build

No workflow-dispatch tool is available; local `gh` authentication reports an
invalid GH_TOKEN. No downloadable Actions artifact is claimed.

Open **Manual Saturn playtest build** (`.github/workflows/build.yml`), Run workflow:

- Workflow branch: `optimization/level1-duplicate-texture-cleanup`.
- `profile`: `stage-default`.
- `source_ref`: the full pushed commit SHA in the delivery message.

After native build, `make check` and `make test` succeed, download
`mullet-force-stage-default-<resolved-full-SHA>`. Keep its BIN/CUE together;
existing retention is one day. Local build: `bash tools/setup.sh`, README host
prerequisites, `bash tools/build-stage.sh --native`, `make check`, `make test`.
Stop after Phase 3.
