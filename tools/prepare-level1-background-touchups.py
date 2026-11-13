#!/usr/bin/env python3
"""Apply only three localized repairs to the existing indexed 640x240 source.
No background regeneration or new colors: use the original RGB555 palette.
"""
from pathlib import Path
import struct,json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];A=R/'art/level1-background-touchups/original';O=R/'assets/city-cleanup'
old=(A/'CIPIX.BIN').read_bytes();pixels=bytearray(old);mask=bytearray(len(old))
words=[0]+list(struct.unpack('>255H',(A/'CIPAL.BIN').read_bytes()))
colors=[tuple((v>>s)&31 for s in (0,5,10)) for v in words]
def nearest(rgb):return min(range(1,248),key=lambda i:sum((colors[i][k]-rgb[k])**2 for k in range(3)))
# Continue the sign surface from its original blue toward its purple right edge.
# The font rectangle, border/corners and every existing animated index are locked.
for y in range(80,96):
 for x in range(464,502):
  at=y*640+x
  if old[at]>=240 or (402<=x<470 and 82<=y<91):continue
  t=(x-464)/37;shade=(y-88)/20
  rgb=[3*(1-t)+4*t,9*(1-t)+3*t+shade,17*(1-t)+10*t+shade]
  pixels[at]=nearest(rgb);mask[at]=1
# Matching masonry between untouched wall samples on both sides of each strip.
# Preserve the local mortar rows and lamp lighting; borrow only subtle brick
# grain from the existing blank masonry at x=376..383 on the same source row.
for x0 in (152,520):
 for y in range(64,104):
  left=colors[old[y*640+x0-1]];right=colors[old[y*640+x0+8]]
  mean=[sum(colors[old[y*640+376+x]][c] for x in range(8))/8 for c in range(3)]
  for x in range(x0,x0+8):
   at=y*640+x
   if old[at]>=240:continue
   t=(x-x0+1)/9;grain=colors[old[y*640+376+(x-x0)]]
   rgb=[left[c]*(1-t)+right[c]*t+(grain[c]-mean[c])*.35 for c in range(3)]
   pixels[at]=nearest(rgb);mask[at]=1
(O/'CIPIX.BIN').write_bytes(pixels);(O/'TOUCHUPMASK.BIN').write_bytes(mask)
legacy=(A/'PATCHMASK.BIN').read_bytes();(O/'PATCHMASK.BIN').write_bytes(bytes(a or b for a,b in zip(legacy,mask)))
subprocess.run(['python3','tools/build-city-cleanup.py'],cwd=R,check=True)
print('Localized changed pixels:',sum(a!=b for a,b in zip(old,pixels)))
