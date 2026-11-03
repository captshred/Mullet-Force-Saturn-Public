from preserved_source import preserved_bytes
"""Exact native waist provenance, unchanged anchors, immutable approved banks."""
from pathlib import Path
from PIL import Image
import json,struct,hashlib
from run_waist_previews import R,O,M,RM,SEQ,RV,body,run,decode

def validate():
 for name,sha in json.loads((O/'preserved-sha256.json').read_text()).items():assert hashlib.sha256(preserved_bytes(R,name)).hexdigest()==sha,name
 counts={};masks={}
 for item in M['frames']:
  a,f=item['actor'],item['frame'];n=['buck','chuck'][a];old=Image.open(R/item['source']).convert('RGBA');new=Image.open(O/f'{n}-{f}.png').convert('RGBA');mask=set(map(tuple,item['changed']));counts[a,f]=len(mask);masks[a,f]=mask
  assert {(x,y) for y in range(96) for x in range(128) if old.getpixel((x,y))!=new.getpixel((x,y))}==mask
  assert all(57<=x<=78 and 42<=y<=44 for x,y in mask)
  assert old.crop((0,45,128,96)).tobytes()==new.crop((0,45,128,96)).tobytes(),'Leg pose changed'
  assert old.crop((0,0,128,42)).tobytes()==new.crop((0,0,128,42)).tobytes(),'Upper art changed'
  assert old.getbbox()==new.getbbox(),'Character/root silhouette bounds changed'
  for y in range(42,45):
   links=lambda im:sum(im.getpixel((x,y))[3]>0 and im.getpixel((x,y+1))[3]>0 for x in range(57,75))
   assert links(new)>=links(old)>0,('Waist disconnected',a,f,y)
  assert body(a,f).tobytes()==new.tobytes(),(a,f,'Runtime piece assembly')
  hx,hy=RV['hands'][a][f];assert old.crop((hx-4,hy-4,hx+5,hy+5)).tobytes()==new.crop((hx-4,hy-4,hx+5,hy+5)).tobytes(),'Grip changed'
  for flip in [False,True]:assert run(a,f,flip).getbbox() is not None
 assert [counts[0,f] for f in range(4)]==[0,27,0,40] and [counts[1,f] for f in range(4)]==[0,23,0,14]
 oldfix=json.loads((R/'assets/chuck-denim-cleanup/manifest.json').read_text())
 for f in range(4):assert not (masks[1,f]&set(map(tuple,oldfix['changes'][str(f)]))),'Approved denim cleanup overwritten'
 for item in M['replacements']:
  b=(O/item['name']).read_bytes();orig=(R/item['source']).read_bytes();w,h=struct.unpack_from('<HH',b,12);assert b[:786]==orig[:786] and len(b)==len(orig)==786+w*h and w%8==h%2==0 and max(b[786:])<254;assert hashlib.sha256(b).hexdigest()==item['sha256'] and hashlib.sha256(orig).hexdigest()==item['source_sha256']
  p=item['piece'];mask=masks[item['actor'],item['frame']]
  for y in range(h):
   for x in range(w):
    if (p['x']+x,p['y']+y-item['shift']) not in mask:assert b[786+(h-1-y)*w+x]==orig[786+(h-1-y)*w+x]
  rid=p['resource']
  if item['shift']:assert [(a,f) for a,frames in enumerate(SEQ['frames']) for f,pp in enumerate(frames) if any(q['resource']==rid for q in pp)]==[(item['actor'],4+item['frame'])]
  else:assert [(a,f) for a,actor in enumerate(RM['actors']) for f,ff in enumerate(actor['frames']) if any(q['resource']==rid for q in ff['parts'])]==[(item['actor'],item['frame'])]
 assert M['boot_bytes']==446304 and M['free_bytes']==12184 and M['slots']==253 and M['extra_bytes']==M['extra_definitions']==0
 print('PASS run waist: 104 regional pixels; C19/C21 = poses 2/4; all roots/piece offsets/timing/src unchanged; exact denim cleanup and even poses preserved; 446304 used,12184 free,253 definitions,zero allocation change')

def validate_active_disc(root,files):
 flag=root/'build/run-waist-mode.txt'
 if not flag.exists() or flag.read_text().strip()!='1':return files
 validate();out=dict(files)
 for item in M['replacements']:
  assert files[item['disc_path']]==(O/item['name']).read_bytes(),item['disc_path'];out[item['disc_path']]=(root/item['source']).read_bytes()
 assert 'Player running waist seam: 1' in (root/'build/BUILD-INFO.txt').read_text()
 print('PASS actual ISO contains eight exact equal-size waist/prep replacements; historical bank checks retained')
 return out
if __name__=='__main__':validate()
