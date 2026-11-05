"""Native asset checks for the approved red/purple identity and roll direction."""
from pathlib import Path
import struct,sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from hero_sprite_pass3_data import HERO_RGB555
assert len(HERO_RGB555)==6
all_bytes=[]
for name,rows in HERO_RGB555.items():
    b=(R/'assets/wingsuit'/name).read_bytes()
    assert b==bytes.fromhex(''.join(rows)) and len(b)==2048,name
    words=struct.unpack('>1024H',b);assert all(v==0 or v&0x8000 for v in words)
    colors=[((v&31)*8,((v>>5)&31)*8,((v>>10)&31)*8) for v in words if v]
    red=sum(r>120 and r>2.5*g and r>2.5*bl for r,g,bl in colors)
    purple=sum(bl>100 and bl>1.15*r and bl>2*g for r,g,bl in colors)
    assert (red>=12 and purple==0) if name.startswith('WBUCK') else (purple>=12 and red==0),name
    tips=[[i//32 for i,v in enumerate(words) if v and i//32<24 and (i%32<5 if side==0 else i%32>=27)] for side in (0,1)]
    assert all(tips),name
    means=[sum(v)/len(v) for v in tips]
    if name.endswith('L.BIN'):assert means[0]>means[1]+4,name
    elif name.endswith('R.BIN'):assert means[1]>means[0]+4,name
    else:assert abs(means[0]-means[1])<1,name
    all_bytes.append(b)
assert len(set(all_bytes))==6
for actor in ('WBUCK','WCHUCK'):
    left=struct.unpack('>1024H',(R/'assets/wingsuit'/(actor+'L.BIN')).read_bytes())
    right=struct.unpack('>1024H',(R/'assets/wingsuit'/(actor+'R.BIN')).read_bytes())
    assert tuple(v for y in range(32) for v in left[y*32:(y+1)*32][::-1])!=right
print('PASS canonical hero assets: six exact 32x32 RGB555 grids, silver/red versus black/purple membranes, center symmetry and both roll attitudes; no mirrored bank substitution')
