#!/usr/bin/env python3
"""Recompose only the Phase 4A annex from its indexed build and concept plate."""
import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = 2560
TOP = 127
HEIGHT = 368
ANNEX = 640
FRONT_X = 338
FRONT_SCALE = .265
THRESHOLD = 285


def quantize(image, palette):
    values, inverse = np.unique(np.clip(np.rint(image), 0, 255)
                                .astype(np.int16).reshape(-1, 3), axis=0, return_inverse=True)
    choices = np.array([*range(1, 240), *range(248, 256)])
    weights = np.array([.95, 1.24, 1.03])
    mapped = np.concatenate([
        choices[np.argmin(np.sum(((part[:, None] - palette[choices]) * weights) ** 2, axis=2), axis=1)]
        for part in np.array_split(values, max(1, (len(values) + 255) // 256))
    ])
    return mapped[inverse].reshape(image.shape[:2]).astype(np.uint8)


def silhouette(plate, bounds, outline, scale):
    """Return a uniformly reduced color crop and a hard indexed silhouette."""
    left, top, right, bottom = bounds
    size = (round((right - left) * scale), round((bottom - top) * scale))
    layer = np.array(plate.crop(bounds).resize(size, Image.Resampling.BOX))
    mask = Image.new('1', (right - left, bottom - top))
    ImageDraw.Draw(mask).polygon([(x - left, y - top) for x, y in outline], fill=1)
    return layer, np.array(mask.resize(size, Image.Resampling.NEAREST))


def composite(canvas, layer, mask, x, y):
    h, w = mask.shape
    canvas[y:y+h, x:x+w][mask] = layer[mask]


def clear_car(canvas, x0, x1, y0, y1):
    # The original cars cover a continuous retaining wall and a thin curb.
    # Recover just that backing from immediately alongside each body.
    for x in range(x0, x1):
        side = x0 - 1 - (x - x0) % 4 if x < (x0 + x1) // 2 else x1 + (x - x0) % 4
        canvas[y0:y1, x] = canvas[y0:y1, side]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('concept', type=Path)
    parser.add_argument('previous_panorama', type=Path, help='indexed 3328 × 368 panorama from Phase 4A')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    previous = np.fromfile(args.previous_panorama, np.uint8).reshape(HEIGHT, 3328)
    palette = np.array([[0, 0, 0]] + [
        [(value >> shift & 31) * 255 // 31 for shift in (0, 5, 10)]
        for value in struct.unpack('>255H', (ROOT / 'assets/level1-neon-strip/NSPAL.BIN').read_bytes())
    ])
    plate = Image.open(args.concept).convert('RGB')
    if plate.size != (2172, 724):
        parser.error('expected the approved 2172 × 724 concept')

    prior = previous[TOP:, ORIGINAL:]
    # Remove an empty interval between the two parked cars; keep the garage
    # and its joint, and use the old dark sky and pavement behind the marquee.
    old_columns = np.r_[0:230, 254:392, 496:768]
    assert len(old_columns) == ANNEX
    kept = prior[:, old_columns]
    canvas = palette[kept].astype(float)

    # Remove all previous facade and marquee pixels behind the new
    # silhouette. Take the upper backdrop from the concept's clear sky
    # to the right of the moon and carry the existing wall behind it.
    backdrop_start = 332
    sky_height = 263-TOP
    backdrop = np.array(plate.crop((855, 0, 1068, 280)).resize(
        (ANNEX-backdrop_start, sky_height), Image.Resampling.BOX)).astype(float)
    amount = np.minimum(1, np.arange(1, ANNEX-backdrop_start+1)/10)[None,:,None]
    edge = canvas[:sky_height, backdrop_start-1:backdrop_start].copy()
    canvas[:sky_height, backdrop_start:] = edge*(1-amount)+backdrop*amount
    wall = np.arange(ANNEX-backdrop_start)%8+320
    canvas[sky_height:THRESHOLD-TOP, backdrop_start:] = canvas[sky_height:THRESHOLD-TOP, wall]

    # The composition uses one uniform scale for the sign, doors, cars and
    # building. Cut around the silhouette so the existing lot and sky show.
    front_bounds = (1036, 0, 2172, 478)
    outline = [(1036,478),(1036,404),(1085,385),(1085,314),(1146,292),
               (1158,243),(1235,208),(1270,109),(1366,92),(1433,31),
               (1576,39),(1595,16),(2012,1),(2041,18),(2171,12),(2171,477)]
    front, face_mask = silhouette(plate, front_bounds, outline, FRONT_SCALE)
    front_y = THRESHOLD - front.shape[0] - TOP
    composite(canvas, front, face_mask, FRONT_X, front_y)

    # Remove the old stretched cars and restore each from its own crop.
    # Garage-deck vehicles remain untouched. The red car ships in the uniform
    # facade crop along with its curb and shadow.
    for x0, x1, bounds, mask, x, scale in (
        (173, 229, (553,397,720,471), [(553,464),(556,443),(572,436),(588,412),(607,402),
          (667,400),(692,409),(708,426),(717,448),(714,468),(698,470),(566,470)], 179, .255),
        (258, 317, (841,382,991,474), [(843,463),(845,439),(858,422),(878,391),(894,389),
          (942,389),(958,399),(973,420),(985,438),(989,462),(980,473),(851,473)], 269, .265),
    ):
        clear_car(canvas, x0, x1, 265-TOP, 286-TOP)
        car, car_mask = silhouette(plate, bounds, mask, scale)
        composite(canvas, car, car_mask, x, THRESHOLD-TOP-car.shape[0])

    # Register wet reflections with the frontage. Fade the sample at its
    # sides and bottom so the retained cracks and parking markings carry on.
    reflection = np.array(plate.crop((1036,478,2172,724)).resize(
        (front.shape[1],round(246*FRONT_SCALE)),Image.Resampling.BOX))
    h,w = reflection.shape[:2]
    blend_x = np.minimum(1, np.arange(w)/9)[None,:,None]
    blend_y = np.minimum(1, (h-1-np.arange(h))/14)[:,None,None]
    dest = canvas[THRESHOLD-TOP:THRESHOLD-TOP+h, FRONT_X:FRONT_X+w]
    dest[:] = dest*(1-blend_x*blend_y)+reflection*(blend_x*blend_y)

    # Use the approved road's dominant dark index as the asphalt base.
    # Preserve differences from the base as cracks, stripe paint and
    # reflections. Garage columns, curbs and trash cans keep their colors.
    old_road = previous[293:326,2530:2560].ravel()
    road_index = np.bincount(old_road,minlength=256).argmax()
    road_base = palette[road_index]
    rows, cols = np.ogrid[TOP:HEIGHT, :ANNEX]
    strength = np.clip((rows-285)/7,0,1)*np.ones((1,ANNEX))
    strength[(cols<124)&(rows<316)] = 0
    lot_base = np.array([33,30,55])
    darkened = road_base + (canvas-lot_base)*.77
    canvas[:] = canvas*(1-strength[...,None])+darkened*strength[...,None]

    native = quantize(canvas, palette)
    # RGB555 values with equal colors can choose a different index during
    # quantization. Keep original garage indices on every untouched pixel.
    unchanged = np.all(canvas==palette[kept],axis=2)
    native[unchanged] = kept[unchanged]
    native[:,0] = prior[:,0]
    extension = np.concatenate([np.repeat(native[:1],TOP,axis=0),native])
    assert np.all(extension)
    args.output.write_bytes(np.concatenate([previous[:,:ORIGINAL],extension],axis=1).tobytes())
    Image.fromarray(palette[native].astype(np.uint8)).save(args.output.with_suffix('.png'))


if __name__ == '__main__':
    main()
