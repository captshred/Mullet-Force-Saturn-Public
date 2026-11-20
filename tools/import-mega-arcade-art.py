#!/usr/bin/env python3
"""Adapt the approved MEGA ARCADE concept to Level 1's indexed panorama."""
import argparse
import struct
from pathlib import Path

import numpy as np
from PIL import Image

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('reference', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
art = root / 'assets/level1-intersection'
palette = np.array([[0, 0, 0]] + [
    [(value >> shift & 31) * 255 // 31 for shift in (0, 5, 10)]
    for value in struct.unpack('>255H', (root / 'assets/level1-neon-strip/NSPAL.BIN').read_bytes())
])
old = np.fromfile(art / 'IXPIX.BIN', np.uint8).reshape(368, -1)[:, :2560]
ref = Image.open(args.reference).convert('RGB')
if ref.size != (2172, 724):
    parser.error('expected the approved 2172 × 724 concept plate')

# The existing Level 1 sky is the sole moon in the scene. Replace the
# reference moon and its halo with the nearby clear sky ramp.
source = np.array(ref)
yy, xx = np.ogrid[:108, 725:854]
mask = np.clip((1.12 - (((xx-785)/62)**2 + ((yy-46)/51)**2)**.5) * 5, 0, 1)[..., None]
sky = np.median(source[:108, 712:728], axis=1)[:, None, :]
source[:108,725:854] = np.rint(source[:108,725:854]*(1-mask)+sky*mask).astype(np.uint8)

# Fit the garage, tree-lined lot and arcade separately in world space.
# The arcade spans the final viewport; the doors align with the right end of the playable lot.
# Local arcade depth and true vertical support columns are left in the art.
world_x = [0, 30, 198, 362, 483, 556, 672, 727, 768]
plate_x = [62, 132, 642, 1040, 1285, 1450, 1650, 1790, 2080]
world_y = [127, 249, 285, 368]
plate_y = [0, 342, 470, 724]
samples = 4
u = np.interp((np.arange(768*samples)+0.5)/samples, world_x, plate_x)
v = np.interp(127+(np.arange(241*samples)+0.5)/samples, world_y, plate_y)
sampled = source[np.minimum(v.astype(int),723)[:,None], np.minimum(u.astype(int),2171)[None,:]]
rgb = sampled.reshape(241,samples,768,samples,3).mean(axis=(1,3))

# Preserve chromatic neon detail at the façade. Use a tighter shade range
# on asphalt; bright reflections fade forward before the bottom walk lane.
pavement = rgb[158:]
if len(pavement):
    base = np.array([26., 25., 43.])
    fade = np.linspace(.17,.58,len(pavement))[:,None,None]
    pavement[:] = pavement*(1-fade)+base*fade
rgb = np.clip(np.rint(rgb),0,255).astype(np.int16)

def quantize(image, choices):
    weights = np.array([.95,1.24,1.03])
    values, inverse = np.unique(image.reshape(-1,3),axis=0,return_inverse=True)
    mapped = np.concatenate([
        choices[np.argmin(np.sum(((batch[:,None]-palette[choices])*weights)**2,axis=2),axis=1)]
        for batch in np.array_split(values,max(1,(len(values)+255)//256))
    ])
    return mapped[inverse].reshape(image.shape[:2]).astype(np.uint8)

usable = np.array([*range(1,240),*range(248,256)])
native = quantize(rgb,usable)
# The old last column registers the visible apron join without overwriting
# any old background. Dissolve only within the first few new columns.
for x in range(12):
    w = (x+1)/13
    native[:,x:x+1] = quantize(np.rint(palette[old[127:,-1:]]*(1-w)+rgb[:,x:x+1]*w).astype(np.int16),usable)
native[:,0] = np.where(old[127:,-1] != 0,old[127:,-1],native[:,0])
hidden = np.repeat(native[:1],127,axis=0)
extension = np.concatenate((hidden,native))
assert np.all(extension)
args.output.write_bytes(np.concatenate((old,extension),axis=1).tobytes())
Image.fromarray(palette[native].astype(np.uint8)).save(args.output.with_suffix('.png'))
