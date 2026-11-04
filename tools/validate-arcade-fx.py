#!/usr/bin/env python3
"""Validate exact approved FX pixels, scoped baseline preservation and disc assets."""
from pathlib import Path
import argparse, hashlib, json, struct
from stage_preservation import stage_digest

R=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--disc',action='store_true')
a=p.parse_args()
m=json.loads((R/'assets/arcade-fx/manifest.json').read_text())
sha=lambda b:hashlib.sha256(b).hexdigest()
assert m['runtime_bytes']==453344-2592+2048==452800 and m['definitions']==255
assert m['vdp2_bytes']==434176 and m['scsp_bytes']==432308
for label,t in m['textures'].items():
    b=(R/t['path']).read_bytes()
    assert len(b)==18+32*32*3 and b[2]==2 and b[16:18]==bytes([24,32])
    assert struct.unpack_from('<HH',b,12)==(32,32)
    assert sha(b)==t['sha256'],label
    rgba=bytearray();native=bytearray()
    for offset in range(18,len(b),3):
        blue,green,red=b[offset:offset+3]
        alpha=0 if (red,green,blue)==(255,0,255) else 255
        rgba.extend((red,green,blue,alpha))
        native.extend(struct.pack('>H',0x8000|(red>>3)|((green>>3)<<5)|((blue>>3)<<10)) if alpha else b'\0\0')
    assert sha(rgba)==t['approved_rgba_sha256'],(label,'approved pixels changed')
    assert sha(native)==t['rgb555_be_sha256'],(label,'hardware pixels changed')
legacy=m['legacy_slot'];assert sha((R/legacy['path']).read_bytes())==legacy['sha256']
assert legacy['vram_bytes']==2592
# Immutable gameplay, audio, characters, city and skyline remain pinned to the
# approved foundation. Only the explicit source/build integration files differ.
lock=json.loads((R/'assets/arcade-fx/preservation.json').read_text())
for name,digest in lock['preserved_sha256'].items():
    assert sha((R/name).read_bytes())==stage_digest(name,digest,'sha256'),(name,'protected foundation changed')
if a.disc:
    assert (R/'build/arcade-fx-mode.txt').read_text().strip()=='1'
    image=(R/'build/mullet-force.bin').read_bytes();files={}
    def scan(directory,prefix=''):
        pos=0
        while pos<len(directory):
            n=directory[pos]
            if not n:pos=(pos//2048+1)*2048;continue
            rec=directory[pos:pos+n];pos+=n;name=rec[33:33+rec[32]]
            if name in (b'\0',b'\1'):continue
            name=name.decode().split(';')[0]
            start=struct.unpack_from('<I',rec,2)[0]*2048
            size=struct.unpack_from('<I',rec,10)[0];data=image[start:start+size]
            if rec[25]&2:scan(data,prefix+name+'/')
            else:files[prefix+name]=data
    rec=image[16*2048+156:16*2048+190]
    start=struct.unpack_from('<I',rec,2)[0]*2048;size=struct.unpack_from('<I',rec,10)[0]
    scan(image[start:start+size])
    assert files['HIT.TGA']==(R/m['textures']['impact']['path']).read_bytes()
    assert files['EXPLODE.TGA']==(R/m['textures']['explosion']['path']).read_bytes()
    assert files['BU01.TGA']==(R/legacy['path']).read_bytes()
print('PASS exact approved 32x32 LEFT/RIGHT pixels, original BU01, protected gameplay/graphics/SFX2/music; projected 255 definitions / 452800 VDP1 / 434176 VDP2 / 432308 SCSP bytes')
