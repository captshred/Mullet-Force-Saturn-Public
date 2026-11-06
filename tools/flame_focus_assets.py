"""Stage-local flame frames and one canonical barrel voice, no Level 1 edits."""
from pathlib import Path
import struct,hashlib,json,math
R=Path(__file__).resolve().parents[1]
def build(out):
 files={}
 def save(n,b):
  (out/n).write_bytes(b);files[n]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
 # Reference palette from FL0..3: orange/red shell, yellow, hot cream core.
 palette=[(0,0,0),(216,72,32),(255,128,40),(255,216,104),(255,240,192)]
 for frame in range(4):
  b=bytearray()
  for y in range(32):
   # Periodic 32-row body: translate upward eight rows per frame. It has
   # no tip/taper, and the same frame tiles seamlessly from end to end.
   angle=2*math.pi*(y+frame*8)/32
   center=16+round(math.sin(angle*2));width=12+round(1.2*math.sin(angle)+.4*math.sin(3*angle+.5))
   for x in range(32):
    d=abs(x-center);edge=width
    index=0 if d>=edge else 1 if d>width-3 else 2 if d>width*.6 else 3 if d>width*.25 else 4
    r,g,bl=palette[index];v=0 if not index else 0x8000|(r>>3)|((g>>3)<<5)|((bl>>3)<<10)
    b+=struct.pack('>H',v)
  save(f'WFL{frame}.BIN',b)
  # A stable three-pixel ignition core blooms into this exact body phase.
  first=struct.unpack('>32H',b[:64]);radius=sum(bool(v) for v in first)//2+1
  cap=bytearray()
  for y in range(16):
   if y==0:cap+=b[:64];continue
   t=1-y/15;ease=t*t*(3-2*t)
   width=round(2+(radius-2)*ease)
   center=16+round(.7*math.sin(frame*math.pi/2+y*.4)*math.sin(math.pi*y/15))
   for x in range(32):
    d=abs(x-center)
    index=0 if d>=width else 1 if d>max(1,width-3) else 2 if d>width*.6 else 3 if d>width*.25 else 4
    r,g,bl=palette[index];v=0 if not index else 0x8000|(r>>3)|((g>>3)<<5)|((bl>>3)<<10)
    cap+=struct.pack('>H',v)
  save(f'WFO{frame}.BIN',cap)
 for name in ('WDEATH.MAP','WDEATH.SEQ','WDEATH.TON'):
  save(name,(out/name).read_bytes())
 report=json.loads((out/'audio.json').read_text());report['files']=files
 (out/'flame-audio.json').write_text(json.dumps(report,indent=2)+'\n')
 return files
