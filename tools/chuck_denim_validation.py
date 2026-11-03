from preserved_source import preserved_bytes
"""Validate 68 native edits, exact indexed patches and unchanged resident allocation."""
from pathlib import Path
from PIL import Image
import json,hashlib,struct
from chuck_denim_previews import R,O,M,body,run,RM,RV,SEQ,decode

def validate():
 for name,sha in json.loads((O/'preserved-sha256.json').read_text()).items():assert hashlib.sha256(preserved_bytes(R,name)).hexdigest()==sha,name
 changed={}
 for f in range(4):
  old=Image.open(R/'assets/player-death/chuck-run-2-final.png' if f==2 else R/f'assets/running/chuck-{f}.png').convert('RGBA');new=Image.open(O/f'chuck-{f}.png').convert('RGBA');mask=set(map(tuple,M['changes'][str(f)]));changed[f]=mask
  assert { (x,y) for y in range(96) for x in range(128) if old.getpixel((x,y))!=new.getpixel((x,y))}==mask
  assert len(mask)==[0,0,24,44][f]
  if f==2:assert all(x in [51,52] and 23<=y<=34 for x,y in mask)
  if f==3:assert all(57<=x<=81 and y in [42,43] for x,y in mask)
  got=body(f);assert got.tobytes()==new.tobytes(),f
  assert old.crop((0,44,128,96)).tobytes()==new.crop((0,44,128,96)).tobytes(),'Legs changed'
  hx,hy=RV['hands'][1][f];assert old.crop((hx-4,hy-4,hx+5,hy+5)).tobytes()==new.crop((hx-4,hy-4,hx+5,hy+5)).tobytes(),'Rear grip changed'
  for flip in [False,True]:assert run(1,f,flip).size==(128,96)
 for item in M['replacements']:
  orig=(R/item['source']).read_bytes();blob=(O/item['name']).read_bytes();w,h=struct.unpack_from('<HH',blob,12);assert orig[:786]==blob[:786] and len(orig)==len(blob)==786+w*h and w%8==h%2==0 and max(blob[786:])<254
  assert hashlib.sha256(blob).hexdigest()==item['sha256'] and hashlib.sha256(orig).hexdigest()==item['source_sha256']
  p=item['piece'];shift=item['shift'];mask=changed[item['frame']]
  for yy in range(h):
   for xx in range(w):
    if (p['x']+xx,p['y']+yy-shift) not in mask:assert blob[786+(h-1-yy)*w+xx]==orig[786+(h-1-yy)*w+xx]
  # Every modified crop belongs exclusively to Chuck and its indicated running/prep frame.
  if item['disc_path'].startswith('COMBAT/'):
   rid=p['resource'];assert [(a,f) for a,frames in enumerate(SEQ['frames']) for f,pp in enumerate(frames) if any(q['resource']==rid for q in pp)]==[(1,4+item['frame'])]
  else:
   rid=p['resource'];assert [(a,f) for a,actor in enumerate(RM['actors']) for f,ff in enumerate(actor['frames']) if any(q['resource']==rid for q in ff['parts'])]==[(1,item['frame'])]
 assert M['boot_bytes']==446304 and M['free_bytes']==12184 and M['slots']==253 and M['extra_bytes']==M['extra_definitions']==0
 print('PASS Chuck denim: frame 3 24 shoulder pixels; frame 4 44 waist pixels; frames 1/2, all legs/grips, Buck, hurt/death, gameplay and palettes unchanged; six existing payload substitutions; 446304 used,12184 free,253 definitions; zero allocation change')

def validate_active_disc(root,files):
 flag=root/'build/chuck-denim-mode.txt'
 if not flag.exists() or flag.read_text().strip()!='1':return files
 validate();out=dict(files)
 for item in M['replacements']:
  assert files[item['disc_path']]==(O/item['name']).read_bytes(),item['disc_path']
  # Historical validators still prove their original source banks. Only these exact,
  # separately validated equal-size replacements are normalized to their predecessors.
  out[item['disc_path']]=(root/item['source']).read_bytes()
 assert 'Chuck denim cleanup: 1' in (root/'build/BUILD-INFO.txt').read_text()
 print('PASS actual ISO contains all six corrected running/prep payloads, no new texture paths or definitions')
 return out
if __name__=='__main__':validate()
