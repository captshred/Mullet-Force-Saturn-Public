# Phase 3A facade opacity and duplicate moon repair

Starting branch: `art/level1-intersection-detail-pass`.
Starting HEAD: `5363539d048062af7e862d75dd232db4bb310aad` (clean).

## Diagnosis

The prior 233-pixel window-only edit was insufficient. There were broad missing
facade regions, not just window holes. Native NBG1 contains the indexed extension
and has priority 2. NBG2 contains the unchanged quarter-speed skyline at priority
1, visible through index zero in the upper 56 rows. The original 1280-pixel
region's upper rows are deliberately blanked; the extension is not blanket
blanked. Tilemap selection, palette upload and scrolling were functioning as
written. Native disc payload checks confirm the actual IXPACK/IXOFF/IXMAP and
palette files match the source outputs.

Three source defects remained:

1. The upper garage-side patch (extension x0–61, y0–55) contained a baked skyline
   fragment. It was not an independent redundant hardware overlay. Its opaque
   skyline pixels and transparent sky created the apparent open architectural
   section in the first screenshot.
2. Both road-facing upper facades contained extensive index-zero areas beneath
   their cornices. The previous narrow window mask left those wall gaps open.
3. A separate orange crescent, including its faint edge pixel, was baked into
   extension x324–337, y27–40. The white crescent belongs to the original skyline.

## Repair and preservation

The garage-side patch now uses the adjoining facade's existing native brick
pixels. Road-side holes beneath the existing cornice contours use that same
masonry texture mapped to existing dark side-wall inks. Every existing nonzero
pixel on these road-side facades remains unchanged, including the earlier sealed
windows, lit panes, frames, highlights and cornice details. The right repair
continues down the receding roofline without a vertical cutoff. The orange
crescent's 46 source pixels become transparent sky, revealing the unchanged
original skyline and its single white moon at the correct parallax offset.

[Exact source proof](../../art/intersection-facade-seal/proof.json) records 5,865
changed pixels: 3,472 garage-side patch pixels, 2,347 road-side missing material
pixels and 46 crescent pixels. No new overlay or runtime rendering rule exists.
The indexed source is fixed before the existing lossless conversion/packing.

All pixels outside that mask are exact, including hotel, record store, other
residential detail, streetlights, road, sidewalk and between-building cityscape.
The original 1280px panorama, palette/animated neon entries, skyline assets,
all native runtime code, camera logic, gameplay, character art, audio and Level 2
are byte-identical. Historical asset proofs remain unchanged and execute against
their exact archived sources; the new validator adds a separate scope proof.

## Native visual review

Both screenshot framings are reproduced using production-disc Yabause traversal
with physical controller input. The comparison tool matches the rendered scenery
against unchanged static facade pixels because video callbacks precede some
end-of-frame camera telemetry. Each pair shares its rendered origin; actor and
HUD states may differ. [Camera measurements](matched-cameras.json).

- [First building before/after](first-building-before-after.png).
- [Receding street before/after](receding-street-before-after.png).
- [Garage wall close-up](wall-detail-before-after.png).
- [Left facade close-up](left-walls-before-after.png).
- [Right facade close-up](right-walls-before-after.png).
- [Moon close-up](one-moon-before-after.png).
- [Full native intersection](receding-street-after.png).

These are native emulator frames, not gameplay screenshot paint-overs. The source
panorama is supplemental evidence only. Visual and hardware acceptance remains
pending user review.

## Validation / memory

Native `stage-default`, `make check` and `make test`; exact art/palette/runtime
scope, deterministic source repair and packing; actual decoder/ring scrolling at
every camera in both directions and wrap/reload guards; UBSan combat/render
regressions and combined heap failures/eight reloads/Level 2 retirement.

[Native traversal](native-traversal.json) covers the complete old-to-new transition,
three-enemy combat, endpoint 1600 and checkpoint/backstop 1280, with no asset or
parallax errors. [Independent cold starts](cold-starts.json) also verify normal
developer-skip settling/clear/loading and retirement of both background pointers.
No RAM writes, teleporting, forced health or save-state loading.

[Measured comparison](memory-comparison.json): 5,366 source tiles (4 fewer),
227,628 B packed source (+1,620 B), combined background owner 295,936 B (+1,616 B)
inside the same 393,216 B fixed heap. Its 16,384 B load-time map transfer still
fits with 80,896 B spare. Static source/table estimate falls by 25 B. VDP2 remains
434,176 B, including 1,664 resident tiles / 106,496 B cells. VDP1 remains
177 definitions / 371,072 B; protected Buck/Chuck 49,152 B reserve, palette and
SCSP allocations remain unchanged. The validator checks the actual linked SDK
sort/vertex addresses and the entire fixed allocator.

## Reproduction and manual build

```
python3 tools/apply-intersection-facade-seal.py
python3 tools/prepare-intersection-facade-seal.py
PATH="$PWD/.deps/iso-tools/usr/bin:$PATH" bash tools/build-stage.sh --native
make check
make test
```

Native review runner: `tools/test-facade-seal-runtime.py`, with `--core`,
`--include`, and a fresh `--out` directory. Compare its output using
`tools/preview-intersection-facade-seal.py --before work/window-opacity/runtime
--after work/facade-seal/review-runtime`. The before capture is the preserved
production traversal of the previous build; committed native images retain that
evidence. Repeated cold boots use `tools/test-full-detail-cold-starts.py`.

GitHub Actions: **Manual Saturn playtest build**; workflow branch
**art/level1-intersection-detail-pass**; `profile` **stage-default**;
`source_ref` **the full final SHA supplied with delivery**. Artifact
`mullet-force-stage-default-<SHA>`, one-day retention. No merge or THE ONE tag move.
