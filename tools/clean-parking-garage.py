#!/usr/bin/env python3
"""Paint the garage threshold in native palette indices."""
from pathlib import Path
import subprocess

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
BASE = "ceeee2e996a86de6c403dbfde82cce4fab99c97e"
ART = "assets/level1-intersection/IXPIX.BIN"
WIDTH, HEIGHT = 3200, 368


def baseline():
    return subprocess.check_output(["git", "show", f"{BASE}:{ART}"], cwd=ROOT)


def paint(data):
    original = np.frombuffer(data, dtype=np.uint8).reshape(HEIGHT, WIDTH)
    result = original.copy()
    # Trace the upper contour of the two cans, rail, and end posts. The
    # bottom contour includes the cast shadow, keeping the road below it.
    mask_img = Image.new("1", (WIDTH, HEIGHT))
    ImageDraw.Draw(mask_img).polygon([
        (2561, 290), (2600, 286), (2616, 285), (2618, 278), (2622, 275),
        (2633, 275), (2637, 277), (2641, 279), (2644, 282), (2653, 282),
        (2656, 281), (2666, 281), (2675, 280), (2687, 279),
        (2688, 292), (2687, 312), (2686, 317), (2669, 319), (2650, 319),
        (2631, 322), (2616, 320), (2604, 320), (2589, 319), (2573, 318),
        (2561, 317),
    ], fill=1)
    removed = np.array(mask_img)
    for x in range(2561, 2689):
        # Continue the existing sloped plinth into the clean right-hand wall.
        ground = 297 - (x - 2561) // 12
        for y in np.flatnonzero(removed[:, x]):
            if y < ground - 4:
                # Keep vertical facade bands aligned by sampling the same
                # column above the obstruction. Below the cans, avoid any
                # source pixels inside the original silhouettes.
                y0 = 266 + (y - 266) % 8
                result[y, x] = original[y0, x] if x >= 2610 else original[272 + y % 9, min(x, 2578)]
            elif y < ground:
                # A mottled bevel, curb and dark contact line. The hues
                # come from the garage wall, avoiding the rail's warm glints.
                tone = original[271 + (y % 4), 2693 + x % 17]
                row = y - (ground - 4)
                result[y, x] = ((37 if tone in (12, 22, 37) else 41),
                                (22 if tone in (12, 22) else 37),
                                (12 if tone in (12, 22) else 22),
                                (221 if tone in (12, 22) else 209))[row]
            else:
                # Continue the parking apron with small adjacent, same-height
                # asphalt fragments. Ease toward the two surviving shoulders.
                left = 2559 - (2562 - x) % 8
                if x < 2569 and (x - 2561) * 2 < (y * 3) % 11:
                    result[y, x] = original[y, min(left, 2559)]
                else:
                    phase = (2688 - x) % 31
                    result[y, x] = original[max(y, 296), 2688 + phase]

    # Extend the two painted faces of the striped support. Their slopes and
    # periods differ slightly in the original perspective.
    for x in range(2579, 2609):
        period = 12 if x < 2595 else 9
        y0 = 288 - (x - 2579) // 16
        for y in range(y0, 296):
            result[y, x] = original[y - period, x]
    result[296, 2579:2609] = 220
    result[297, 2580:2609] = original[299, 2696:2725]

    # Lay a few irregular dirt chips onto the smoother concrete at the seam.
    # Use existing indexed weathering marks and leave the downhill roadway intact.
    chips = [
        (2562, 265, 2572, 267, 2545, 266), (2561, 270, 2570, 272, 2540, 268),
        (2564, 273, 2574, 274, 2548, 269), (2562, 277, 2572, 279, 2544, 270),
        (2568, 280, 2577, 281, 2546, 273), (2561, 283, 2568, 284, 2550, 272),
        (2564, 287, 2570, 288, 2548, 268),
    ]
    for left, top, right, bottom, sx, sy in chips:
        for y in range(top, bottom):
            for x in range(left, right):
                source = original[sy+y-top, sx+x-left]
                if source in (12, 22, 37, 39, 41, 65, 69, 70):
                    result[y, x] = source

    assert np.array_equal(result == 0, original == 0)
    return result.tobytes()


if __name__ == "__main__":
    import sys
    Path(sys.argv[1]).write_bytes(paint(baseline()))
