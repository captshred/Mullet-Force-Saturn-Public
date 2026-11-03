# Optional parallax / long-map demonstration

Branch `vdp2-parallax-test`, based directly on the user-validated VDP2 milestone
`f653dcae9e16617b1cf5a976c78fd7a8427a4bfc`. The preserved branches `main`,
`sprite-upgrade-test` and `vdp2-background-test` are not modified or merged.
The loading fix at 8fb07eb and registration correction at f653dca are ancestors.

## Build and controls

```
MF_PARALLAX_DEMO=1 MF_SPRITE_GALLERY=1 MF_VDP2_STREET=1 make native
make check
make test
```

The same flags work with the pinned Docker `make` build. Native host tools must
be installed as described in README. Gallery PNG validation also requires Pillow
(`python3-pil` on Debian/Ubuntu); bootstrap and the gallery-enabled CI job install
this existing validator dependency. MF_PARALLAX_DEMO defaults to **0**. Enabling
it requires the VDP2 street and gallery, and rejects the intentionally broken
legacy display-check configuration. Normal VDP2 and `MF_VDP2_STREET=0` fallback
builds work as before with the preview disabled. Disabled discs contain no
preview files or entry point.

Cold-boot the matching BIN/CUE, without an old save state. In the existing gallery:

* **B:** enter the technical preview; B again restores the original gallery.
* **Left/Right:** move the camera, two pixels per VBlank.
* **Hold Up with Left/Right:** eight pixels per VBlank for faster travel.
* **A:** mirror Buck and Chuck, exactly as before.
* **C:** toggle the existing asset diagnostics.
* **Start:** restore the original map and leave the gallery for the original
  title screen. Start again begins the unchanged game.

Either physical controller may operate the preview. The original gameplay HUD,
controls, simulation, world limits, combat, music and animation code are unchanged.
The technical preview does not simulate combat or play music, like the gallery.
Its labels show camera, quarter-speed skyline position and loaded cache chunks.

## Layers and the long world

This is an **8,192-pixel** finite test strip (25.6 viewports), with camera
0..7,872 and 64 world chunks of 128 pixels. The five existing street chunks are
reused sequentially as temporary scenery. Repeated facades and intentional
artwork joins are placeholders, not final long-stage art.

NBG1 reuses the validated street cell pool and its existing two-page 1024x512
map allocation as an eight-chunk ring. It retains the original (+1,+1) street
screen registration. NBG2 displays a temporary 512x64 repeating distant skyline
at `floor(camera/4)`, using 8-bit cells and four colors from **existing palette 1**.
The skyline has 52 unique tiles. No palette is created, altered or stolen from
actors, HUD or the font.

The old street is opaque across the whole screen. In the preview only, NBG1's
screen window begins at y=56, revealing NBG2 through the upper band y=1..55.
The skyline remains behind the street: priorities are NBG2=1, NBG1=2, sprites=4,
NBG0 text=7. Windows 0 and 1 belong to these two layers while previewing.
This is simple window compositing, not a transparent-sky redesign of the source
art. NBG0/font ownership and VDP1 actor sorting are unchanged. The initial
street column zero and top row preserve the backdrop/registration convention.

The ring cache tracks the world chunk in each of its eight physical slots.
The retained range normally starts two chunks behind the camera, clamped at
world ends. A maximum six elapsed VBlanks per update limits travel to 48px;
at most one 128px chunk needs replacement: **480 halfword stores / 960 bytes**.
Both the old visible viewport and the next one are outside the overwritten slot.
Writes occur only to those offscreen map entries; this implementation does not
pretend that normal callbacks execute in VBlank. Saturn VRAM arbitrates CPU
access, and real-hardware timing still needs profiling.

There are no CD reads, allocations, cell uploads, palette writes or map-sized
copies during scrolling. Entering/exiting disables the display briefly for a
bounded map rebuild. Leaving reconstructs every original map word (including
padding) from the resident source chunk library, disables NBG2, restores the
original priorities, window and SGL cycle schedule, and performs no CD read.
SGL's zero-success return convention remains checked correctly. No SDK patch.

## Exact allocations

| VDP1 texture configuration | Allocated, including alignment/HUD | Free of 458,488 |
|---|---:|---:|
| Preview or VDP2 gallery | 302,336 | 156,152 |
| VDP2, no gallery | 291,552 | 166,936 |
| VDP1 fallback with gallery | 455,936 | 2,552 |
| VDP1 fallback, no gallery | 445,152 | 13,336 |

The preview adds **zero VDP1 bytes**. The original 150 KiB VDP1 saving remains.

| VDP2 address range, end exclusive | Bytes | Owner |
|---|---:|---|
| 0x25E00000..0x25E16080 | 90,240 | Original street cells, A0 |
| 0x25E40000..0x25E44000 | 16,384 | Original street map / preview ring, B0 |
| 0x25E44000..0x25E46000 | 8,192 | Skyline cell reservation, B0 |
| 0x25E46000..0x25E48000 | 8,192 | Skyline map, B0 |
| 0x25E20000..0x25E40000 | 131,072 | SDK-protected A1 |
| 0x25E60000..0x25E80000 | 131,072 | SDK-protected B1 |

Total layer allocations **123,008 bytes**; plus SDK whole-bank reservations:
**385,152 / 524,288 bytes reserved**, leaving **139,136** unassigned in A0/B0.
The skyline's actual tile payload is 3,328 bytes; 8,192 is reserved to preserve
map alignment and explicit bank ownership. The increment over f653dca is exactly
**16,384 bytes**. SDK reservations are not claims of actual font payload usage.

CRAM remains **8 x 512 = 4,096 bytes** with the gallery; street bank ID 1 is
shared read-only by both layers. No additional palette or color data file.
The three optional CD payloads total **21,184 bytes**: PCHUNK.BIN=4,800,
PSKY.BIN=8,192 and PSMAP.BIN=8,192. Original assets remain on disc.

New persistent work RAM is **4,868 bytes BSS**: a 4,804-byte source chunk buffer
(4,800 data plus terminator/alignment) and a 64-byte SH-2 cache/state structure.
The 16KiB ring has no work-RAM shadow. A temporary 8,193-byte file buffer uses an
exact **8,204-byte Jo heap block**, including its eight-byte header and four-byte
alignment, then is freed. JO_FAST_ALLOCATION avoids retaining a larger recycled
TGA block. No persistent preview heap allocation. Additional transient plus
persistent data peak is **13,072 bytes**, excluding small call-stack frames and
resident machine code. The existing 384KiB Jo heap reservation is unchanged.
The included link map records the complete executable layout, including code,
read-only data, pre-existing buffers and heap; data-only costs are not total RAM.
For the current target builds, the full executable/BSS end changes from
0x06094804 (preview disabled, same as f653dca) to **0x060965B4** with the preview:
**7,600 bytes** additional resident image footprint, comprising 4,868 bytes
new BSS plus 2,732 bytes code/data/alignment. There are **170,572 address bytes**
between that end and the SGL-owned region at 0x060C0000; this gap is not a claim
of free heap, safe stack space or additional low-work-RAM capacity.

The initial gallery-enabled CI check failed because Pillow was missing from
the runner, after the build and parallax asset checks passed. The dependency
is installed explicitly; no validator or gameplay behavior was relaxed.

## Validation scope and limitations

Independent asset validation checks the chunk library against every original
pattern name, skyline map/cell ranges, palette reuse, file hashes/disc contents,
all 7,873 viewport ranges, and disabled-build isolation. Actual C loader/cache
host tests exercise every forward/backward pixel offset, wraparound, reversal,
old/next viewport safety, endpoint clamps, quarter-speed coordinates, maximum
chunk writes, exact original-map restoration and load/allocation/cycle failures.
ASan/UBSan and all existing gameplay, co-op, combat, gallery, input, animation,
asset and music checks are included in the verification runs.

Runtime tests use libretro Yabause v0.9.15, commit
8926b0c6c347f8c5c755911ddb0ac695420ffbf8, software renderer, interpreter, HLE BIOS,
one thread and no expansion cartridge. Separate background-only ROMs use the
actual street/parallax modules and pinned Jo/SGL, with host-controlled camera
values. **All 15,745 full 320x240 captures matched exactly**: forward camera
0..7,872 and reverse 7,871..0, **1,209,216,000 pixels, zero mismatches**.
The machine-readable `parallax-runtime-validation.json` records the tested
module and data hashes. Reference RGB is independently reconstructed from source TGAs, skyline
pattern data and the core's RGB565 output quantization. The delivered full game
is separately tested using real emulated button input: enter, traverse forward,
reverse, return to gallery, re-enter and Start into original gameplay.

This proves a bounded **RAM-resident chunk map** and two hardware background
layers. It does not implement CD asset streaming, unique tiles for every chunk,
parallax inside combat stages, enemy encounter streaming, full animation banks,
or a finished level. The skyline repeats every 512 pixels, source street art
repeats every 640, and preview camera movement is integer pixel scrolling.
Future unique art needs cell-cache residency, palette ownership and CD prefetch
without attack-triggered reads. Real Saturn VRAM cycles, CPU access contention,
CD latency, music/effects under load and frame-time budgets need device profiling.
No physical Saturn or new WebRetro-browser test has been performed here.


The optional reproducible runtime checker is kept outside normal game builds:

```
python3 tools/test-parallax-runtime.py --core /path/to/yabause_libretro.so \
  --libretro-include /path/to/libretro-common/include \
  --nm /path/to/coff-capable/sh-elf-nm --out /tmp/mf-parallax-runtime
```

Use the native-build PATH/library configuration for your host tools. It copies
sources to a temporary test checkout and supplies `tests/runtime/parallax-main.c`
as that ROM's entry point; it never edits the game checkout. The core must already
be available. `--quick` checks ten offsets only and does not establish full-world
coverage. The normal checker runs all 15,745 positions; it generates references,
logs and selected PPM screenshots, not thousands of retained full-frame files.
