#!/usr/bin/env python3
"""Restore structural edges at the garage joint in the existing indexed panorama."""
from pathlib import Path
import subprocess

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BASE = "0ed5c2d17af578d3bee253dd224ff620cc2c4e4d"
ATLAS = "assets/level1-intersection/IXPIX.BIN"
WIDTH, HEIGHT = 3200, 368


def baseline():
    return subprocess.check_output(["git", "show", f"{BASE}:{ATLAS}"], cwd=ROOT)


def curb_top(x):
    # Approach at the existing 1:5 grade. Ease onto the apron in two
    # smaller steps without altering the lane artwork below the curb.
    if x < 2573:
        return 284 + (x - 2552) // 5
    return 288 - (x - 2573) // 48


def paint(data):
    src = np.frombuffer(data, np.uint8).reshape(HEIGHT, WIDTH)
    pixels = src.copy()

    # A masonry end pier takes up the dissolve between two facades. Retain
    # the original light and parking sign on the main garage column.
    for y in range(136, 284):
        for x in range(2555, 2568):
            donor_x = 2540 + (x - 2555)
            donor_y = 223 + (y - 136) % 29
            pixels[y, x] = src[donor_y, donor_x]
        pixels[y, 2555] = 41 if y % 9 < 6 else 37
        pixels[y, 2567] = 12 if y % 11 < 8 else 22
    # Reveal a solid recessed left jamb, leaving the clear right-hand car
    # pixels, original rails, and the horizontal floor lips in place.
    for top, bottom, lip in ((154, 201, 197), (219, 263, 258)):
        for y in range(top, bottom):
            for x in range(2568, 2579):
                if top + 2 <= y < lip and (x <= 2570 or y >= lip-7) and not (top == 154 and 186 <= y <= 195):
                    pixels[y, x] = (4, 12, 22)[min(2, x-2568)]
                elif lip <= y < lip+2:
                    pixels[y, x] = src[y, 2578] if x >= 2573 else (41, 37)[y-lip]
    # Continue the two deck fascia bands over the pier. Their lower edges
    # meet the existing garage side at world column 2579.
    for top, depth in ((199, 3), (217, 3), (261, 3)):
        for x in range(2555, 2579):
            for row in range(depth):
                pixels[top+row, x] = src[top+row, 2574+x%5] if x >= 2568 else (37, 41, 12)[row]

    # Join the incoming curb to a shallow garage footing. Its face is
    # three pixels tall and the original roadway begins immediately below.
    for x in range(2552, 2689):
        y = curb_top(x)
        if x < 2579:
            # Rectify the smeared lower edge of the broad concrete cheek.
            first = 278 + max(0, x-2567)//4
            for row in range(first, y):
                pixels[row, x] = src[267+(row+x)%8, 2541+x%12]
        elif x >= 2609:
            # Keep the existing facade, replacing its lowest texture row
            # only where the higher curb exposes an old bevel.
            for row in range(y-2, y):
                pixels[row, x] = src[row-9, x]
        tone = src[265+x%5, 2690+x%17]
        pixels[y:y+3, x] = (41 if tone in (37, 39, 41) else 37, 22, 209)
        if x < 2560:
            # Limit the left adjustment to the curb. Keep the original
            # asphalt and lane markings intact from row 292 onward.
            end = 292
        else:
            end = 298 - (x - 2560)//13
            if 2579 <= x < 2609:
                end = 298
        for row in range(y+3, end):
            pixels[row, x] = src[max(row, 295), 2691+x%29]

    assert np.array_equal(pixels == 0, src == 0)
    return pixels.tobytes()


if __name__ == "__main__":
    import sys
    Path(sys.argv[1]).write_bytes(paint(baseline()))
