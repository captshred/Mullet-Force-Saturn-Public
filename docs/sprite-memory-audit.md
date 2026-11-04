# Bat input consolidation and sprite memory audit

Target: `captshred/Mullet-Force-Saturn-Public`, local branch
`fix/unify-forward-bat`, parent `a4f31e1befca753d978d096aff196cae09af8474`.
The private repository and recovery tags were not accessed or changed.
The older 253-definition figures in the brief precede jab-jab-cross.

The exact difference is the existing `MF_PUNCH_COMBO=1` feature: the cross loader
adds COMBO/XC0.TGA for Buck and COMBO/XC1.TGA for Chuck. Each is indexed8,
80 x 44 = 3,520 aligned bytes and one definition. Thus 446,304 + 7,040 =
453,344 bytes and 253 + 2 = 255 definitions. No new palette or view is added.
These allocations already exist in public main at the parent commit and are not
introduced by the bat correction. The current README/CI selects this feature;
the older 253 / 446,304 figures refer to the otherwise matching pre-combo profile.

To verify the cause independently, the allocation harness was run twice against
the same staged assets and code, with only `MF_PUNCH_COMBO` changed in a temporary
host profile header. `python3 tools/audit-sprite-memory.py --without-combo`
reported 253 / 446,304, and the normal invocation reported 255 / 453,344.
The difference is precisely the two cross uploads; all 14 views remain.


## Implemented behavior

For the selected fast-running-bat profile, dash recognition now precedes A
classification. Forward, neutral, Forward+A starts the same fast horizontal bat
as Forward, neutral, Forward, then A. The second edge must satisfy the existing
dash eligibility and release/window rules. Both fighters and both directions
use the same path. A single forward+A is still a jab; airborne gestures remain
kicks. The fast profile no longer initiates the planted bat. Historical profiles
with `MF_FAST_RUNNING_BAT=0` retain their existing behavior as regression controls.

The run pose is captured with the input, rather than depending on the renderer
having observed a previous run frame. `mf_running_bat.active` and `.pending`
encode zero or one plus the pose in the fast profile; their boolean meaning and
structure size are unchanged. No extra RAM or texture storage is allocated.
This also handles immediate input before any run rendering and catch-up updates.

Existing horizontal attack constants are unchanged: 12 advancing ticks total,
active counters 4–7, guard from counter 9, existing momentum decay, per-target
hit masks, Corporate Punk KO eligibility, barrel destruction and combat events.
Normal jab-repeat/cross, jump, torch, sounds, enemies and world assets remain
covered by the regression suite. Jump and existing eligibility guards take
priority over a requested bat. An unarmed dash after torch put-away no longer
falls back to the obsolete planted bat in the fast profile.

## Measured allocation

| Selected jab-jab-cross profile | Before | After | Reclaimed |
| --- | ---: | ---: | ---: |
| Definitions | 255 / 255 | 255 / 255 | 0 |
| Resident payloads | 241 | 241 | 0 |
| Zero-payload views | 14 | 14 | 0 |
| VDP1 texture bytes | 453,344 / 458,488 | 453,344 / 458,488 | 0 |
| Free texture bytes | 5,144 | 5,144 | 0 |

The CSV [inventory](sprite-memory-inventory.csv) lists every registration in boot
order, dimensions, indexed8 or RGB555 format, aligned payload bytes, final VDP1
offset, palette at registration and usage category. Alias offsets refer to their
source rows and are not counted as new payloads. Their palette is selected when
drawing, rather than inferred from the zero-height registration.

`python3 tools/audit-sprite-memory.py > docs/sprite-memory-inventory.csv`
executes the actual main boot loader, gallery, animation and enemy loaders with
host allocation mocks against staged `build/cd` files and `build/build-info.h`.
The mock follows Jo's previous-definition allocation cursor, including tail
aliases; it does not infer residency from all files present on disc. It asserts
255 registrations, 14 views and 453,344 bytes. VDP2 street/parallax setup and sound
upload are stubbed because they allocate no VDP1 textures in this profile.
This is a host reconstruction, not a new hardware measurement. It independently
matches the committed punch-combo manifest and earlier emulator report.

| Loader group | Definitions (including views) | Allocated bytes |
| --- | ---: | ---: |
| Root textures, generated HUD and views | 155 | 324,224 |
| COMBAT | 60 | 47,168 |
| HQTORCH | 12 | 13,088 |
| HQJUMP | 14 | 26,272 |
| HQHURT | 10 | 31,584 |
| HQDEATH | 2 | 3,968 |
| COMBO | 2 | 7,040 |

Indexed textures use one byte per texel; RGB555 uses two. Each allocation is
rounded to 32 bytes. A TGA's file length includes headers/palette and is not its
VDP1 footprint. Frame views cost definitions but no texture bytes.

## Resource dependencies and cleanup decision

No loader allocations or source assets were removed in this patch. Removing the
planted input does not by itself make every bat-named texture exclusive:

- `seq_upper[actor][1]` is the approved horizontal contact upper. Keep it.
- `seq_lower` is shared by jabs, cross and horizontal bat. Keep it. The head in
  horizontal contact also appears in other attack keys.
- Running parts are shared by dash, horizontal bat carry, and the boot movement
  review. Guard/recovery resources also serve idle/jabs. Keep these consumers.
- `BT00..06`, `CT00..06`: 14 definitions / 59,712 bytes. `LEGS.TGA`: one /
  1,696 bytes. `AL0..2`: three / 4,544 bytes. They serve the main renderer's
  legacy bat and aerial fallback branches. The fast profile does not request
  these planted/aerial bats, but historical build profiles still do. Thus these
  are selected-profile retirement candidates, not globally exclusive resources.
- The old sequence upper keys 2/3, run-prep keys 4..7 and `seq_weapon` still have
  consumers in historical sequence/momentum rendering and their bank tests.
  In particular COMBAT/DT0 and DT1 replace prep resources 51/52 and are reused by
  the HQ death upper drawing. Removing the whole old sequence bank would break
  death, jabs, cross and the new horizontal swing.
- Current boot gallery draws GB/GC pieces; movement review draws original-three
  walk and four run poses. It does not offer a planted-bat preview. Historical
  animation/render regression profiles do exercise the old attack banks.

A separate selected-profile loader retirement can remove the legacy-only roots
while preserving them in historical profiles. That requires changing the loader's
base-byte equations, ID/slot preflights, dependent manifests and bank tests as a
coherent change. This audit does not claim those 65,952 candidate bytes / 18 IDs
have been reclaimed. Some fallback arms/lowers also overlap other player states;
they must be traced individually, rather than retired by filename.

Two exact duplicate TGA pairs are resident: `GB2.TGA` with `COMBAT/CA02.TGA`, and
`GC2.TGA` with `COMBAT/CA30.TGA`. Both use the shared gallery palette. Reusing the
existing IDs would save 960 + 1,056 = **2,016 bytes and two definitions**, without
changing pixels. These are shared idle/combat lower pieces, not planted-only
allocations; consolidation is recommended for review rather than implemented
under the Part 1 exclusive-cleanup scope. Tail allocation/preflight accounting
must be updated and checked after any such reuse.

## Where the definition limit comes from

Pinned SDK revision: `556d081146211b6a1cfa6591d70f9487d406758b`.
`Compiler/COMMON/jo_engine_makefile:125–129` defaults `JO_MAX_SPRITE` to 255 and
allows an explicit make override. `jo/conf.h:67` documents the same default.
`sprites.c` allocates `__jo_sprite_def`, `__jo_sprite_pic`, and optionally the
hash table to that size. The SGL boot call receives the definition array.
IDs are 0..254 for a 255-entry build. The limit is software configuration, not a
Saturn rule of 255 unique images. Map code already conditionally changes its
sprite index storage from 8 to 16 bits above 255; animator base IDs are 16-bit.

An increased definition array can hold more IDs without increasing VDP1 texture
capacity, so it can help zero-payload views and genuinely small assets. It costs
work RAM for each enlarged table, requires rebuilding all engine users, and
requires reviewing map/layout assumptions, ID users, game preflights and tests
with fixed 255/256 arrays. `sprites.c:189` guards overflow only under `JO_DEBUG`;
the release profile has `JO_DEBUG=0`. A lone config override is therefore not a
validated safe change. Add unconditional registration bounds checks as part of a
future reviewed SDK/config change. The pinned compiler/SDK and sprite limit have
not been changed here.

Texture storage is independent: `jo/sega_saturn.h` reserves texture start
`0x10000` and end `0x7fef8`, yielding **458,488 bytes**. Expanding ID tables does
not move those addresses or create more texture memory. Do not use the SDK's
separate user-area-size constant as the texture-budget formula.

## Reuse, banks and future content

Multiple Corporate Punk instances share `cp_ids`/`cphq_ids`, loaded once in
`mf_corporate_load`. Per-enemy clocks and transforms choose among these IDs;
spawning another instance does not load another texture bank. Buck and Chuck
also share lower pieces where already authored to do so; they remain distinct
art. Hardware mirroring and palette flashes already avoid duplicate uploads.

Existing cropping and aligned strips reduce bytes but may increase definitions
and draw calls. Full-width row aliases are useful because the texture pitch is
unchanged. Arbitrary rectangular subviews cannot assume a separate source pitch
in a normal VDP1 sprite; repacking must preserve the encoded row stride. Palette
reuse saves CRAM and permits shared indexed bytes; different index meanings must
be reconciled before sharing nominally similar images.

Recommended order, preserving the current approximately 88px player art:

1. Retire selected-profile legacy fallback roots after documenting reachability
   and updating loader accounting; keep originals and historical profile support.
2. Share the two exact lower-piece duplicates above. Check seams, palette indices,
   both facings, loader tail addresses and all death/torch/jump consumers.
3. Audit COMBAT keys per profile and deduplicate exact indexed strips. Reduce
   redundant registrations before adding views; crop only where aligned savings
   exceed the additional definition/draw overhead. Keep shared heads/legs/guards.
4. If definitions remain the bottleneck, review a bounded larger Jo definition
   configuration with complete engine rebuild, overflow tests and work-RAM delta.
5. For new stages, use explicit stage/encounter banks loaded during transitions,
   with a persistent player/HUD/effects bank and shared enemy-type banks. Budget
   all simultaneously visible types and boss phases before spawning them.
6. Use stable handles/generation checks and keep textures/definitions valid until
   SGL has completed every referencing command. Do not free an in-flight bank.
   Preload during transitions; avoid per-frame CD access or speculative streaming.
7. Treat motorcycle/wingsuit sequences as separate scene profiles with dedicated
   scenery/enemy banks and retained HUD/audio where useful. Preserve player art
   quality; change residency and reuse rather than shrinking sprites.

A bank system would also need CD/RAM staging budgets, explicit load failures,
transition latency measurement and tests for returning to gameplay. None of those
structural changes is included in this patch.

## Command capacity and performance

A definition is a resident image/view, not a per-frame draw command. Every visible
piece, shadow, effect and HUD rectangle emits commands independently of ID reuse.
Multipart sprites can save texture bytes while increasing SH-2 submission cost,
SGL sorting work and VDP1 fill/overdraw. Enemy-instance sharing saves storage but
not those draw costs. VDP2 street/parallax avoids spending VDP1 draws/textures on
that scenery, but does not make characters free to render.

The texture start leaves the lower 64 KiB of VDP1 RAM for the existing command
layout. A 32-byte VDP1 command yields a coarse 2,048-slot upper bound before
control/reserved commands, not a promised available sprite budget. The pinned
SDK's `jo/sega_saturn.h` documents an SGL command buffer of `0xe100` bytes
(`MAX_POLYGON*32`, 1,800 entries) and separate sort/sprite buffers; SGL also exports
`MaxPolygons` and `MaxVertices`. These are separate constraints from 255 IDs.
Do not increase command capacity by moving the texture base without redesigning
and validating the memory map.

No new frame-time or worst-case command measurement was made. Before adding
crowds, instrument actual per-frame submissions and SGL limits, measure SH-2
update/submission and VDP1 completion, and test overlapping sprites/flames on
physical Saturn. Inventory counts and successful host tests cannot establish
60 Hz performance or physical-hardware compatibility.

## Verification and remaining playable-build work

- `make test`: passed, including immediate/delayed equivalence, both fighters and
  facings, all carried run phases, single-forward jab, airborne kick/landing,
  simultaneous jump priority, barrel/Punk hits, sound events and shared bank tests.
- New `unified_bat_test.c` runs actual simulation and rendering together with
  host Saturn-I/O mocks. It compares texture IDs/mirroring each attack tick,
  stale-pose protection, collision outcomes and movement at equalized world roots.
- Public runtime lock: all 520 exported payloads match baseline; preserved audio
  check passed. Street and parallax validators passed independently.
- Actual boot-loader inventory reproduced 255 IDs / 453,344 bytes / 14 views.
- Complete selected native SH-2 build, raw executable, ISO, BIN/CUE generation
  and full `make check` passed. The environment has no sudo/root package-install
  access, so official Debian package `genisoimage_1.1.11-3.4_amd64.deb` was
  extracted to `/workspace/work/mullet-bat-final/genisoimage-local` and its
  `usr/bin` directory added to PATH for builds. `genisoimage --version` reports
  1.1.11. No SDK, Jo Engine, compiler or Docker pin was changed.
- The matching CUE uses MODE1/2048. Full checks verify the actual ISO executable,
  build identity, package checksums, public runtime payloads and VDP2 layout.
- No new emulator or physical-Saturn playtest was performed. The playable package
  is a locally built validation candidate; host tests do not establish hardware
  performance or visual approval. No merge, tag change or Actions run is required.

Reproduce in this environment with:

```sh
export PATH=/workspace/work/mullet-bat-final/genisoimage-local/usr/bin:$PATH
bash tools/build-punch-combo.sh --native
make check
make test
python3 tools/audit-sprite-memory.py
python3 tools/audit-sprite-memory.py --without-combo
```

On a standard provisioned machine, install `genisoimage` using the documented
bootstrap prerequisites instead. Build outputs and environment-local packages
are excluded from the source commit. The exported package includes matching
BIN/CUE, BUILD-INFO, checksums, validation logs, audit/inventory and third-party
notices. It is rebuilt after the source commit so its embedded commit matches.

Before visual baseline approval: perform controller-driven emulator captures of
immediate/delayed inputs and existing combat for both directions/players, then
verify physical Saturn separately. The resource-retirement and engine/bank
roadmap items require review before implementation; none is part of this patch.
