"""Lossless native enemy assembly, immutable baseline, palette and budget checks."""
from preserved_source import preserved_bytes
from pathlib import Path
from PIL import Image
import hashlib,json,struct
from corporate_hq_previews import render,M,O,B
R=Path(__file__).resolve().parents[1]
def validate():
 pal=(B/'palette.bgr24').read_bytes();total=0;keys=set()
 for r in M['resources']:
  data=(O/r['name']).read_bytes();w,h=struct.unpack_from('<HH',data,12)
  assert data[:3]==b'\0\1\1' and data[18:786]==pal and len(data)==786+w*h and w%8==h%2==0
  assert max(data[786:])<254 and hashlib.sha256(data).hexdigest()==r['sha256'];assert r['bytes']==(w*h+31)&~31
  k=(w,h,data[786:]);assert k not in keys;keys.add(k);total+=r['bytes']
 for i,n in enumerate(['idle-0','idle-1','idle-2','walk-0','walk-1','walk-2']):
  old=Image.open(B/f'{n}.png').convert('RGBA');expected=Image.new('RGBA',(144,112));expected.alpha_composite(old,(16,16));assert render(i).tobytes()==expected.tobytes(),n
 for key,name in [(7,'strike'),(8,'hurt'),(9,'fall'),(10,'ground')]:
  new=render(key);source=Image.open(O/f'{name}.png').convert('RGBA');assert new.getchannel('A').tobytes()==source.getchannel('A').tobytes(),name
  assert all(new.getpixel((x,y))==source.getpixel((x,y)) for y in range(112) for x in range(144) if new.getpixel((x,y))[3]),name
  assert set(new.getchannel('A').getdata())=={0,255}
  if name in ['hurt','ground']:assert new.getbbox()[3]==108,(name,new.getbbox())
  for flip in [False,True]:
   q=render(key,flip);assert q.getbbox() is not None
 assert total==M['texture_bytes'] and M['boot_bytes']==457888-56960+total and M['free_bytes']==458488-M['boot_bytes']>0 and M['slots']==254-12+len(M['resources'])<=255
 lock=json.loads((O/'source/preserved-sha256.json').read_text())
 for n,h in lock.items():assert hashlib.sha256(preserved_bytes(R,n)).hexdigest()==h,n
 print(f"PASS HQ Corporate Punk: exact idle/walk/head/legs and palette; native new poses; immutable gameplay/SFX/music/player art; {M['boot_bytes']} VDP1 bytes, {M['free_bytes']} free, {M['slots']} definitions; 12 obsolete uploads replaced by 4 shared payloads")
 return M
if __name__=='__main__':validate()
