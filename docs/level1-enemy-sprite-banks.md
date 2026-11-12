# Phase 5: Level 1 enemy suffix ownership

Branch: `architecture/level1-enemy-sprite-banks`.
Exact parent: `1dfe2197828890d9aae9131c95ede2ad9aaece6f` on
`optimization/level1-hud-panel-memory`. The owner approved that Phase 4 candidate's
1P Yabause playtest; complete Saturn hardware and 2P approval remain pending.
It is not a new THE ONE tag. `the-one-ai3-baseline` remains
`15387a314a51bffbe3e65152e45958ed5f3416c5`. No tags moved/created/deleted, no merge,
no new section transitions, art, actors, behaviors or subsequent phase work.
The delivery message identifies the full commit containing this report.

## Exact ownership and memory

| Owner | IDs | Definitions | VDP1 texture bytes |
|---|---|---:|---:|
| Persistent Level 1 prefix | 0–137 | **138** | **224000** |
| Corporate Punk suffix | 138–151 | **14** | **33024** |
| Resident total / high-water during tested swaps | 0–151 | **152** | **257024** |
| Free after install | | 103 definition slots | **201464 bytes** |

This is an ownership change, with no additional texture allocation or reduction.
The prefix contains all Buck/Chuck resources, their complete HQ/COMBO/running/
weapon banks, gallery/review pieces, HUD/bar, shared flames/embers/charge, barrels,
shadow, impact/explosion effects and all **14 crop/tail views**. Every view resolves
wholly inside a retained prefix payload. There are 124 actual prefix payloads.
The last prefix definition is the real indexed payload **COMBO/XC1.TGA**, 80x44,
3520 bytes at offset 286016; its end is **289536 = 0x10000 + 224000**.
It is a valid allocator tail, not a cropped view ending before other storage.

The suffix is exactly **CP00.TGA–CP09.TGA** (10 / 11744 bytes) and
**CQ00.TGA–CQ03.TGA** (4 / 21280 bytes). First CP00 occupies offset 289536;
last CQ03 ends at 322560. No shared player/weapon/effect texture was moved into
this suffix. All original files and animation tables remain unchanged. The
manifest is [`assets/enemy-sprite-banks.json`](../assets/enemy-sprite-banks.json).
`tools/audit-sprite-memory.py` gives the complete current order; `--phase4`
restores the original interleaved order for comparison.

### Persistent palette contract

Palette **4 is shared**, not enemy-owned: existing HQ player weapon rendering
selects it. Palette **5** contains the original derived burn colors. Banks 1/2/3/6/7
and font bank 0 retain their prior ownership and numbering. Both 4 and 5 survive
all enemy swaps. The original CP/CQ palette headers agree across all 14 resources.

Palette objects are created in the original order. The initial CP load is deferred
until all persistent sprites and views have loaded; it seeds palette 4 exactly
as before. Only then is palette 5 filled with the unchanged burn-color formula.
Player weapon initialization stores palette ID 4 but does not consume its colors
before loading finishes. At this point every palette is identical to Phase 4.
On a reload the installer receives **NULL** as its TGA default palette, preserving
palette 4 instead of rewriting it. Its fingerprint is checked before/after the
operation. Tests check every palette on the host and raw palette-4/5 CRAM bytes in
Yabause. No bank operation allocates or releases a palette.

## Pinned SDK investigation

Jo Engine remains pinned to `556d081146211b6a1cfa6591d70f9487d406758b`, unmodified.
The build still disables dual-CPU rendering and the RAM-cartridge module.
`jo_sprite_free_from(first)` sets last ID to `first-1`, retaining earlier metadata.
Its private address cursor surprisingly becomes the end of the **first freed
texture**. The next normal registration sees the nonzero cursor and recomputes
its address from the preceding retained definition, which is why a correct prefix
tail is essential. The manager validates that tail before/after release and uses
ordinary `jo_sprite_free_from(138)` plus normal TGA registration, with no custom
allocator, metadata rewrite, sentinel allocation or SDK patch.

A regression compiles the actual pinned `__jo_get_next_sprite_address`,
`__internal_jo_sprite_add` and `jo_sprite_free_from` bodies and verifies this
behavior through 256 repetitions and full teardown. The SDK filename hash lookup
searches only through its current last ID, so freed suffix entries are not visible;
new TGA registrations update the reused slots. Game renderers use returned handles,
not filename lookups or historical global numeric IDs.

## API and swap mechanism

`src/enemy_sprite_bank.h` defines the callback contract and read-only diagnostics.
The only implemented resource bank is `mf_corporate_bank_spec`.

1. **Boot:** after the prefix is complete and before the render callback is
   installed, `mf_enemy_bank_boot` checks 138 definitions / 224000 bytes, palette 4,
   capacity, all resulting CP handles/dimensions/formats/contiguous addresses and
   total footprint. It seals the persistent metadata and palette fingerprints.
2. **Prepare:** `mf_enemy_bank_prepare(spec,game,vblank)` accepts a static-lifetime
   descriptor only while READY, in started/unpaused Level 1, with **both enemy
   slots ABSENT**. Invalid state/capacity requests return false without changing
   a live bank. It rechecks ownership and fingerprints, invalidates every private
   enemy handle immediately and enters DRAIN. No existing actor stores a texture
   ID; the corporate renderer refuses unloaded generations and consumes the path
   without falling back to invalid legacy sprites.
3. **Core barriers:** the integration at the beginning of `main:update` freezes
   simulation/spawns, clears pending input and submits **no sprites** while the
   bank is unavailable. Existing music updates continue with no new game events.
   `mf_enemy_bank_service` counts three distinct observed VBlank callbacks, which
   pass through the normal core's `slSynch` barriers. A jump in the tick value is
   not treated as multiple barriers; repeated same-tick calls do not advance it.
4. **Hardware fence:** stop PTMR auto-restarts, require VDP1 EDSR completion bit 2
   using the same bounded hardware-poll approach as the approved Level 2 loader.
   No texture is freed on a busy timeout. This is synchronization, not an arbitrary
   sleep or an attempt to mask a sound-driver error.
5. **Replace:** release the old suffix, verify last ID 137 and the exact prefix end,
   append the new descriptor's bank, validate every handle/count/end, recheck
   prefix/palette integrity and increment generation. Old and new enemy banks are
   never resident together. Restore the approved SGL PTMR=2 automatic policy.
6. **Resume:** refresh the clock from the actual post-I/O VBlank and discard the
   section's pending edges; there is no simulation catch-up burst after loading.
   `mf_enemy_bank_current()` exposes the resident descriptor only when READY.
7. **Failure:** hardware-busy failure keeps old storage allocated; partial-load or
   invalid-handle failure invalidates all handles and rolls back the partial
   suffix. Rendering remains blocked, PTMR stays stopped after synchronization,
   and a text-only bank error latches until restart. Prefix data is never freed.
   There is no automatic retry loop or fallback drawing from stale IDs.
8. **Level 2:** `mf_enemy_bank_retire` invalidates CPU handles and disallows further
   requests, without freeing anything itself. The **unchanged Level 2 loader**
   retains its own three-frame drain, VDP1 completion check, full sprite teardown,
   WDEATH initialization and sound-driver handshake. Its source/audio fixes are
   byte-identical to Phase 4.

Normal gameplay installs once at boot and never requests a bank change. There is
no section trigger, extra runtime CD read, loading pause, AI/spawn change, enemy
limit change or ordinary-play re-registration. The source supports explicit safe
future requests; it does not silently add transitions to the existing stage.

### Accounting and RAM

Animation initialization budgets subtract the deferred 33024 bytes while building
the prefix. The public texture-byte query adds the current resident bank's bytes,
so normal HUD/gallery/preview diagnostics still show **257024**. An initial test
caught the preview reading prefix-only 224000; its diagnostic now uses that query.
No visual/text expectation was changed to conceal it.

The manager has 48 bytes of logical static bookkeeping on 32-bit Saturn (three
pointers, three unsigned fields and the six-field diagnostic record), plus a
4-byte corporate residency flag. The read-only descriptor is 24 bytes. There is
no new manager heap allocation or full-bank RAM cache. The original SDK's sequential
TGA decode buffers are reused/freed as before; heap peak was not separately profiled.
Linked production section deltas are recorded in the delivery validation; source
code and metadata growth must be distinguished from the unchanged VDP1 footprint.
Test-only saved-game snapshots and trace buffers are excluded from production.

## Validation and proof

- Native `stage-default`, pinned SDK: passed; production BIN/CUE generated.
- `make check` and `make test`: passed, including the complete immutable original
  regression chain and the current actual loader, renderer and lifecycle tests.
  Archived references compile against their own source headers, not staged current
  headers. The current audit uses source headers ahead of staged build copies.
- Allocation/ownership: 152 / 257024, prefix 138 / 224000, suffix 14 / 33024; every
  resource's dimensions/format/palette/payload retained. All views have exactly one
  prefix owner; no aliases point into the suffix. Historical disabled mode retains
  the old order/behavior. No placeholder allocations or 4MB cartridge dependency.
- Full renderer comparison: **7666 cases / 150855 draws**, actual Phase 4 versus
  banked and disabled profiles. Exact decoded textures, palettes, HUD geometry,
  draw positions/scale/flip/depth/order, text and clears match. Both players/facings,
  all approved attacks/FF+A, torch, hurt/death, enemy states, stage clear, gallery/
  preview and expanded HUD cases remain covered under UBSan. Only build identity
  metadata is held common in the host comparison; no pixel mismatch is waived.
- Lifecycle tests: **256 real manager/CP-loader reload cycles** on the host, with
  byte-for-byte prefix metadata/picture records, prefix pixels and all palettes
  unchanged. Tests cover active/dying enemies, gallery/not-started, pause,
  stage-clear, invalid capacity, same-VBlank calls and elapsed-tick jumps. Hardware
  busy failure never frees; a load failure after two resources rolls back; rejected
  handle validation rolls back a full replacement. No stale draws in unavailable,
  failed or retired states; generations/counters and peak allocation are checked.
- Separate actual pinned SDK allocator-body test: 256 repeated suffix releases/
  additions, cursor recomputation and full reset, without modifying SDK code.
- Normal production Yabause versus exact Phase 4: **zero wall-frame state/image
  mismatches**. 600 Level 1/stage-clear snapshots / 30 complete screens and
  555 Level 2 snapshots / 545 complete screens match. Both enter Level 2 at frame
  1844, end with the same 28-definition bank (last ID 27), and report zero errors.
- **Real native bank demonstration:** eight actual suffix frees/reinstalls in a
  dedicated test-only build using the current normal API and SDK/CD/GPU paths.
  It temporarily saves/removes fixture actors at each controlled boundary; those
  changes are never in production source. Normal pause/drain/install/resume logic
  is unmodified. Generation 1 plus eight replacements were independently observed.
  Every READY bank had 152 definitions, high-water **257024**, free **201464**.
  Raw persistent and enemy VRAM bytes and palette-4/5 CRAM bytes were identical in all nine
  generations. No leaked IDs, prefix overwrite, load error or E108 was observed.
  Then physical X used the existing stage shortcut and real Level 2 teardown /
  WDEATH/readiness succeeded, reaching gameplay with last ID 27. Audio samples were
  nonzero during drain/load waits and during Level 2; this proves continuing output,
  not an audible-quality or waveform-equivalence certification.
- `git diff --check`, Python and shell syntax: passed.

Yabause core: `8926b0c6c347f8c5c755911ddb0ac695420ffbf8`, HLE BIOS,
software/interpreter, one thread, no cartridge, fresh saves. Normal comparison uses
`tools/test-legacy-sprite-runtime.py` with Phase 4 via its legacy `--phase1-*`
arguments and current production via `--phase2-*`. Reproduce the real swap test:

```sh
python3 tools/test-enemy-bank-runtime.py \
  --core /path/to/yabause_libretro.so \
  --include /path/to/libretro-common/include \
  --out /tmp/fresh-enemy-bank-demo
```

The tool builds a separate TEST-ONLY native source copy, retains the program,
frames, read-only save-state telemetry, all nine prefix/enemy/palette dumps and
`comparison.json`. It never writes emulator RAM or changes production source/build.
Do not distribute that demonstration BIN/CUE as the normal playable candidate.
The production stage-default workflow contains no demo hook.

## Future section/bank integration

A future bank needs an immutable static-lifetime `mf_enemy_bank_spec`: unique
positive `kind`, exact aligned `definitions`/`bytes`, append-only install callback,
idempotent private-handle invalidation, and full mapping/count/address validation.
Its installer receives NULL during swaps: palette 4/5 and all persistent textures
must remain unchanged. The current corporate bank assumes its existing palette;
future art must respect that shared palette or use an independently validated
format/ownership plan. Do not recolor the shared player weapon by replacing it.

For a future **Corporate Punk + Ricky** bank, the installer would append both
sets and keep separate type/pose handle maps; its validator must cover their
complete combined footprint. The game would additionally need an explicitly
approved renderer/type/spawn integration. None of that art/behavior/mapping is
implemented here. Other regular-enemy combinations have the same obligations.
A **Brion-only boss bank** would require its own descriptor, renderer and validation,
with no old regular-enemy actors alive when requested. No boss behavior is implied.

A future street/bar/alley/boss section controller must reach a safe boundary,
remove all old enemy actors/corpses, request before drawing/updating the next
section, allow the integrated core gate to finish synchronization/loading, verify
READY and the expected current descriptor/generation, then publish the new spawn
plan. Do not poll the service from an interrupt or fabricate its clock; this
implementation assumes the pinned single render CPU/core callback. Do not append
new persistent resources after sealing the prefix. Background banks, new section
boundaries and world expansion require separate work.

Current suffix capacity is at most **117 definitions / 234488 bytes** after the
fixed prefix; each proposed bank must prove exact VDP1/decoder-heap/palette budgets,
frame behavior and failure paths. The 40–50KB enemy estimates are planning inputs,
not implemented guarantees. Only CP→equivalent CP replacement has been tested;
arbitrary combinations, empty banks, new bosses and returning from Level 2 to a
fresh Level 1 initialization are not implemented capabilities.

## Changed files / limits / publication

New runtime files: `src/enemy_bank_config.h`, `src/enemy_sprite_bank.h/.c`.
Reviewed integrations: `src/main.c`, `src/corporate_animation.c`,
`src/animation_preview.c`, `make/saturn.mk`. Build/audit changes:
`tools/build-source-complete.sh`, `tools/build-native.sh`,
`tools/audit-sprite-memory.py`, `Makefile`, new manifest. New validation:
`tools/validate-enemy-sprite-banks.py`, `tools/test-enemy-bank-render.py`,
`tools/test-enemy-sprite-banks.py`, optional `tools/test-enemy-bank-runtime.py`,
`tests/enemy_banks/*`, and this report. The scope lock reverses only the exact
reviewed order/lifetime/accounting hooks, then compares the remaining original
code byte for byte. AI, input, gameplay, enemy limits, natural 40-KO progression,
audio files/scheduler, Level 2 code and all artwork remain frozen.

No real Saturn or audible listening validation was performed. Natural 40-KO
emulator completion was not performed; stage-clear host regressions and unchanged
game code preserve it. Both production transition and post-swap transition use
the existing development shortcut, without bypassing loader/sound checks. Real
hardware/2P approval remains the owner's playtest step; no permanent intermittent-
startup cure or new THE ONE approval is claimed.

No dispatch tool is available; local `gh` reports an invalid GH_TOKEN. No Actions
artifact is claimed. Open **Manual Saturn playtest build** (`.github/workflows/build.yml`):

- Workflow branch: `architecture/level1-enemy-sprite-banks`.
- `profile`: `stage-default`.
- `source_ref`: the full pushed SHA in the delivery message.

After native build, `make check` and `make test` succeed, download
`mullet-force-stage-default-<resolved-full-SHA>`. Keep BIN/CUE together; retention
remains one day. Local build: setup/README prerequisites, then
`bash tools/build-stage.sh --native`, `make check`, `make test`.
Stop after Phase 5.
