"""Prove this variant changes only audited suit-rim colors, never geometry."""
from pathlib import Path
from PIL import Image
import json,hashlib,struct

def validate_corporate_lighting(root,files=None):
 a=root/'assets/corporate-punk-lighting';b=root/'assets/corporate-punk-refined';m=json.loads((a/'manifest.json').read_text());base=json.loads((b/'manifest.json').read_text());pal=(a/'palette.bgr24').read_bytes();oldpal=(b/'palette.bgr24').read_bytes();roles={r['source_raw_index']:r for r in m['lighting_roles']}
 def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
 def protected(x,y):return y<22 or (49<=x<61 and 22<=y<52)
 def same(q,r):assert q.size==r.size and q.tobytes()==r.tobytes()
 assert m['base_manifest_sha256']==sha(b/'manifest.json') and m['poses']==base['poses'] and len(roles)==12
 for key in ['canvas','root','selected_height','texture_bytes','texture_slots','pieces_per_pose','boot_bytes','boot_free','boot_slots','full_bytes','full_free','full_slots','idle_holds','walk_holds']:assert m[key]==base[key]
 assert m['palette_clone_slots']==[235,236] and m['vdp1_delta']==m['cram_delta']==0
 allowed={r['target_raw_index'] for r in roles.values()};assert pal[:45]==oldpal[:45]
 for i in range(256):
  if i not in allowed:assert pal[3*i:3*i+3]==oldpal[3*i:3*i+3]
 for i,r in roles.items():
  before=tuple(v>>3 for v in oldpal[3*i:3*i+3]);after=tuple(v>>3 for v in pal[3*r['target_raw_index']:3*r['target_raw_index']+3]);assert before==tuple(r['source_bgr5']) and after==tuple((v+1)//2 for v in before)==tuple(r['target_bgr5'])
  if r['cloned']:assert oldpal[3*i:3*i+3]==pal[3*i:3*i+3]
 for r,old in zip(m['resources'],base['resources']):
  new=(a/r['name']).read_bytes();prev=(b/old['name']).read_bytes();assert new[:18]==prev[:18] and len(new)==len(prev) and new[18:786]==pal and sha(a/r['name'])==r['sha256']
  assert all(r[k]==old[k] for k in ['name','width','height','bytes'])
  if files is not None:assert files[r['name']]==new
 for pose in m['poses']:
  name=pose['name'];before=Image.open(b/(name+'.png'));after=Image.open(a/(name+'.png'));rgba=before.convert('RGBA');newrgba=after.convert('RGBA');assert sha(b/(name+'.png'))==m['source_frames_sha256'][name]
  assert before.size==after.size==(96,96);same(rgba.getchannel('A'),newrgba.getchannel('A'));assert rgba.getbbox()==newrgba.getbbox()
  count=0
  for y in range(96):
   for x in range(96):
    i=before.getpixel((x,y));j=after.getpixel((x,y));target=i in roles and not protected(x,y)
    if target:
     assert j==roles[i]['target_raw_index'];assert newrgba.getpixel((x,y))!=rgba.getpixel((x,y));count+=1
    else:assert i==j and newrgba.getpixel((x,y))==rgba.getpixel((x,y))
  assert count==m['changed_pixels_per_frame'][name]
  # Reassemble actual exported pieces, independently, in both facings.
  for flip in [False,True]:
   out=Image.new('RGBA',(96,96))
   for p in pose['parts']:
    r=m['resources'][p['resource']];data=(a/r['name']).read_bytes();w,h=struct.unpack_from('<HH',data,12);q=Image.new('P',(w,h));q.putpalette(after.getpalette());q.putdata([v for y in range(h-1,-1,-1) for v in data[786+y*w:786+(y+1)*w]]);q.info['transparency']=0;q=q.convert('RGBA')
    if flip:q=q.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    out.alpha_composite(q,(96-p['x']-w if flip else p['x'],p['y']))
   ref=newrgba.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else newrgba
   same(out.getchannel('A'),ref.getchannel('A'))
   for p,q in zip(out.getdata(),ref.getdata()):
    if q[3]:assert p==q
 for label,names in [('idle',['idle-0','idle-1','idle-2']),('walk',['walk-0','walk-1','walk-2'])]:
  gif=Image.open(a/f'{label}-4x.gif');assert gif.n_frames==3
  for i,name in enumerate(names):
   gif.seek(i);q=Image.open(a/(name+'.png')).convert('RGBA').resize((384,384),Image.Resampling.NEAREST);r=gif.convert('RGBA');same(q.getchannel('A'),r.getchannel('A'))
   for x,y in zip(q.getdata(),r.getdata()):
    if x[3]:assert x==y
 for label in ['comparison','contact']:
  q=Image.open(a/f'{label}-native.png');same(Image.open(a/f'{label}-4x.png'),q.resize((q.width*4,q.height*4),Image.Resampling.NEAREST))
 assert m['texture_bytes']==11744 and m['boot_bytes']==362848 and m['boot_free']==95640 and m['boot_slots']==135
 print('PASS lighting-only:12 audited rim shades at rounded50%,2 isolated slots, exact alpha/geometry/timing/dedup/mirrors; head/tie and every untargeted pixel unchanged; legacy palette preserved; zero VDP1/CRAM allocation delta')
 return m
if __name__=='__main__':validate_corporate_lighting(Path(__file__).resolve().parents[1])
