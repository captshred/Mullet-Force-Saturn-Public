# Corporate Punk: one-pose artwork review

Branch: `corporate-punk-sprite-test`. Parent: `c3edb05bb3f65c8cb8c9b3c013f86752dddc6cbc`, the latest `walk-knee-lift-test` head checked against GitHub before branching. It retains Timing B (10/10/10 ticks at 60 Hz) and the approved frame-1 knee adjustment.

## Review files and provenance

`assets/corporate-punk/corporate-punk-84.png` is the indexed native master; `corporate-punk-84-rgba.png` is its transparent RGBA equivalent. Both have binary transparency. `corporate-punk-tight.png` is the unpadded 47×84 visible sprite. `corporate-punk-84-8x.png`, `lineup-native.png`, `lineup-6x.png`, and `legacy-compare-{native,6x}.png` support visual review. All enlargement uses nearest neighbor.

The primary reference was the large fighting illustration at the far left of the supplied sheet, not the turnaround or small game-sprite panels. `source/isolated-reference-edit.png` is a tool-assisted extraction/reconstruction of that illustration, not a claim of a pixel-exact crop of the attachment. The binary-alpha isolated reference removes the surrounding glow. A scaled positional intermediate was followed by a dedicated pixel-cluster reconstruction (`native-cleanup-edit.png`), nearest sampling to the native grid, and a registered local face cleanup (`face-cleanup-edit.png`). Only existing skin pixels within a small facial region receive that cleanup. These source guides are retained, and the final indexed raster is the review authority. No low-resolution screenshot was used as the artwork source.

This remains an artistically interpreted native candidate requiring approval. At 84px, individual fingers, facial creases, lapel stitching, earring, and tiny buttons must be simplified. Strong cyan/magenta edge accents from the approved illustration remain; their strength may merit visual review. The face occupies only a few pixels, limiting literal high-resolution likeness. The silhouette stays wiry and right-facing, with raised fists, pointed shoes, red tie, charcoal suit, and green crest. No animation has been generated.

## Native geometry

Canvas: 96×96. Root: (48,92), one pixel below the soles. Opaque bounds are [25,8,72,92), hence 47×84. The approved heroes are unchanged 128×96 images from `assets/animation-polish/{buck,chuck}-00.png`, with root (64,92), opaque height 88 and widths 79/82. The lineup places their native pixels directly on the same sole row 91; it never scales characters independently.

The actual old EN00 is 56×90 padded, opaque 49×90, not the 84px shown in the reference sheet. The comparison decodes that real TGA without resizing and aligns its visible soles with the new master. The legacy cropped anchor (20,89) is not changed.

## Palette and texture costs

42 opaque RGB555 colors plus raw index 0 transparency. The export retains a 256-entry BGR24 file palette (768 bytes), as expected by the existing indexed Jo TGA loader. Hardware color RAM uses 512 bytes per existing palette bank. Across all current EN*.TGA, raw indices 0–14 are occupied; every such entry is preserved byte-for-byte. The new colors occupy raw slots 15–56, previously unused. No duplicate allocated RGB555 shades occur. There are 239 eligible unused slots before this extension and 197 afterward.

The intended future strategy is to extend existing enemy palette handle/bank 4, not allocate another bank. Raw index 0 becomes Jo's transparent key 1 after the pinned loader's +1 remap; indices stay below reserved high values. `palette-delta.json` records the precise additions. This milestone does not install the palette into the game. Future integration must also extend the derived burn palette in its existing bank if the new enemy is rendered burnt; that work is not authorized here.

| Layout | 8-bit VDP1 texture bytes (32-byte aligned) | Draw commands per instance |
|---|---:|---:|
| One 48×84 rectangle | 4,032 | 1 |
| Two bands | 3,488 | 2 |
| Selected three bands | 3,200 | 3 |
| Four bands | 3,104 | 4 |

Three bands save 832 bytes against the whole rectangle. Four saves only another 96 bytes, so three is the practical choice. Search considers 1–4 horizontal bands, even heights, minimum 8px bands, width multiples of eight, and picks the fewest pieces within 5% of the minimum. Selected pieces are 16×12 at (50,8), 40×56 at (30,20), and 48×16 at (25,76). Coordinates refer to the original 96×96 canvas. No pixels are rescaled, omitted, or blended across seams.

`CP0.TGA`, `CP1.TGA`, `CP2.TGA` are the preferred set. `CPWHOLE.TGA` is an alternative, never an additional resident texture. The three files total 5,558 bytes on disk (including three headers/palettes); texture payload is 3,200 bytes. Multiple identical enemies reference the same three texture handles: 1/2/4/8 instances still use 3,200 bytes, with 3/6/12/24 drawing commands. Per-instance gameplay records and drawing-list capacity are separate future runtime costs, not duplicated texture storage.

Future right-facing placement is `world_x-camera-48+piece.x`; left-facing placement is `world_x-camera+48-piece.x-piece.width` with hardware horizontal flip. Y is `ground-92+piece.y`. This matches established unit-scale rendering conventions; the existing SGL raster registration must remain consistent. Native assembly and mirrored assembly are checked offline, not claimed as hardware-tested.

## Runtime isolation and validation

Nothing under `src/`, `assets/cd/`, or the approved player asset directories changes. No current texture is uploaded, replaced, or removed. Current validated playable allocation remains **351,104 bytes allocated / 107,384 bytes free** within the engine's **458,488-byte** VDP1 texture budget, with **125 texture slots**. Active VDP1 and CRAM deltas are both **zero**. If later added resident without replacing anything, this pose alone would leave 104,184 bytes free and require three more texture slots; this is an estimate, not an active allocation.

Eight existing 512-byte CRAM banks remain unchanged (4,096 bytes). Source PNGs and TGA file palette copies are offline files, not resident texture or color RAM allocations. No new CD reads, streaming, cache, or animation states exist.

Rebuild artwork explicitly with `python3 tools/build-corporate-punk.py`; normal game builds do not invoke it. Pillow quantizer versions can affect a rebuild, so committed indexed files and hashes are authoritative. Validate with `python3 tools/validate-corporate-punk.py`. It independently decodes the TGA exports, checks exact assembly and mirroring, binary alpha, dimensions, RGB555 uniqueness, preservation of all legacy enemy palette entries, source hashes, native hero pixels and enlarged previews. Existing CI build/check/gameplay jobs also remain enabled. The new artwork has not been integrated or tested in an emulator or on hardware. Review the native artwork before authorizing either integration or animations.

Local verification completed: the pinned native SH-2 build of the approved knee-lift/Timing B + parallax/gallery configuration passed; `make check` passed (disc image, existing assets, player artwork constraints, music); `make test` passed (animation, street/parallax/fallback, gallery, combat, two-player, weapons, inputs and audio transport). The new offline Corporate Punk validator passed. No emulator or physical hardware test was performed for this artwork-only change. A diff against the parent confirms runtime code, shipped CD assets, approved player art, and the native build script are unchanged.
