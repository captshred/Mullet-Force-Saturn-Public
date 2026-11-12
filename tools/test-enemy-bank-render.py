#!/usr/bin/env python3
"""Exact allocation and ID-independent rendered-command/decoded-pixel comparison.
Runs actual approved/current loaders/renderers with mocked Saturn I/O, not an emulator.
"""
from pathlib import Path
import csv,hashlib,io,json,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'assets/enemy-sprite-banks.json').read_text())
def inventory(*args):
 return list(csv.DictReader(subprocess.check_output(['python3','tools/audit-sprite-memory.py',*args],cwd=R,text=True).splitlines()))
current=inventory();control=inventory('--phase4')
assert len(current)==len(control)==152
assert sum(int(r['allocated_bytes']) for r in current)==257024
for name in {r['path'] for r in current if r['path']!='alias'}:
 a=next(r for r in current if r['path']==name);b=next(r for r in control if r['path']==name)
 for field in ('width','height','format','allocated_bytes','palette_at_registration'):assert a[field]==b[field],(name,field,a,b)
assert sum(int(r['allocated_bytes']) for r in current[:138])==224000
assert sum(int(r['allocated_bytes']) for r in current[138:])==33024
assert [r['path'] for r in current[138:]]==m['corporate']['resources']
assert sum(r['path']=='alias' for r in current[:138])==14
for view in (r for r in current if r['path']=='alias'):
 start=int(view['vdp1_offset']);end=start+int(view['width'])*int(view['height'])
 assert end<=0x10000+224000
 owners=[r for r in current[:138] if int(r['allocated_bytes']) and int(r['vdp1_offset'])<=start and end<=int(r['vdp1_offset'])+int(r['width'])*int(r['height'])*(1 if r['format']=='indexed8' else 2)]
 assert len(owners)==1,'view does not own retained persistent storage'
print('PASS ownership: 138/224000 persistent, 14/33024 enemy suffix; 152/257024 total; 201464 free; every resource retained',flush=True)
with tempfile.TemporaryDirectory(prefix='cleanup-equivalence-') as d:
 work=Path(d);baseline=work/'baseline';baseline.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',m['baseline']],cwd=R))) as t:t.extractall(baseline,filter='data')
 results=[]
 for label,source,flag in [('phase4',baseline,0),('banked',R,1),('disabled',R,0)]:
  header=(R/'build/build-info.h').read_text()
  header=header.replace('#define MF_ENEMY_SPRITE_BANKS 1','#define MF_ENEMY_SPRITE_BANKS 0')
  if '#define MF_ENEMY_SPRITE_BANKS' not in header:header+='\n#define MF_ENEMY_SPRITE_BANKS 0\n'
  header=header.replace('#define MF_ENEMY_SPRITE_BANKS 0',f'#define MF_ENEMY_SPRITE_BANKS {flag}')
  # This temporary copy of the real main includes all current drawing code.
  text='#include <stdio.h>\n#include <assert.h>\n#include <string.h>\nvoid audit_finish(void);\n'
  text+=(source/'src/main.c').read_text().split('static void update(void)')[0]
  scenarios=(R/'tests/sprite_cleanup/scenarios.inc').read_text()
  text+='\nstatic void hud_scenarios(void);\n'+scenarios.replace('audit_finish();','hud_scenarios();audit_finish();')+'\n'+(R/'tests/hud_panel/scenarios.inc').read_text()
  local=work/('unit-'+label);local.mkdir();(local/'build-info.h').write_text(header);(local/'main.c').write_text(text)
  exe=local/'trace';animation=source/'src/animation_preview.c'
  subprocess.run(['cc','-std=c99','-ffunction-sections','-fdata-sections','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(local/'build-info.h'),'-I'+str(R/'tests/enemy_banks'),'-I'+str(local),'-I'+str(source/'src'),str(local/'main.c'),str(R/'tests/enemy_banks/trace.c'),str(animation),*[str(source/'src'/n) for n in ('corporate_animation.c','gallery.c','player_animation.c','game.c')],*([str(source/'src/enemy_sprite_bank.c')] if (source/'src/enemy_sprite_bank.c').exists() else []),'-Wl,--gc-sections','-o',str(exe)],cwd=R,check=True)
  p=local/'trace.txt'
  with p.open('w') as f:subprocess.run([str(exe)],cwd=R,check=True,stdout=f)
  textures={};names={};palettes={};commands=[];raw={}
  for line in p.read_text().splitlines():
   fields=line.split('|')
   if fields[0]=='TEXTURE':
    _,ident,name,w,h,mode,allocated,offset,data=fields
    names[ident]=name;raw[ident]=bytes.fromhex(data)
    textures[ident]=(int(w),int(h),int(mode),hashlib.sha256(bytes.fromhex(data)).hexdigest())
   elif fields[0]=='PALETTE':palettes[fields[1]]=fields[2]
   else:commands.append(fields)
  canonical=[];panel_draws=0
  for f in commands:
   if f[0]=='QUAD':
    _,frame,ident,z,flip,palette,*points=f
    assert names[ident]=='generated:panel'
    q=list(map(int,points));assert q==[-127*65536,45*65536,128*65536,45*65536,128*65536,84*65536,-127*65536,84*65536]
    w,h,mode,_=textures[ident];assert h==40 and mode==0
    rows=[raw[ident][j*w*2:(j+1)*w*2] for j in range(h)]
    assert all(row==row[:2]*w for row in rows)
    canonical.append(('PANEL',frame,1,65,str(int(z)//65536),flip,256*65536,40*65536,palette,b''.join(row[:2] for row in rows)))
    panel_draws+=1
   elif f[0]=='DRAW' and names[f[2]]=='generated:panel':
    _,frame,ident,kind,x,y,z,flip,sx,sy,palette=f
    w,h,mode,_=textures[ident];assert h==40 and mode==0
    pixels=raw[ident];rows=[pixels[j*w*2:(j+1)*w*2] for j in range(h)]
    assert all(row==row[:2]*w for row in rows), 'panel row not horizontally uniform'
    center_x,center_y=int(x),int(y)
    if int(kind)==2:center_x+=w//2-160;center_y+=h//2-120
    if int(kind)==2 and int(sx)==int(sy)==65536:
     # Actual SGL center-zoom CMD B=(width-1,height-1): even dimensions
     # place the inclusive raster center one pixel past the input center.
     center_x+=1;center_y+=1
    # Preserve exact fixed-point destination geometry, all row colors,
    # depth, flip and palette. Only source width/sampling rate may differ.
    canonical.append(('PANEL',frame,center_x,center_y,z,flip,w*int(sx),h*int(sy),palette,b''.join(row[:2] for row in rows)))
    panel_draws+=1
   elif f[0]=='DRAW':canonical.append(tuple(f[:2])+textures[f[2]]+tuple(f[3:]))
   elif f[0]=='TEXT':
    # Diagnostic memory counters must report the real profile's allocation.
    text=f[4]
    if text.startswith('VDP1 '):
     expected=257024
     assert text.startswith('VDP1 '+str(expected)),(label,text)
     f[4]=text.replace(str(expected),'<actual-budget>',1)
    canonical.append(tuple(f))
   else:canonical.append(tuple(f))
  results.append((canonical,palettes))
  print(label,'panel draws',panel_draws,flush=True)
 assert results[0]==results[1], 'panel geometry/row colors or other pixels/transforms/text/palettes differ'
 assert results[0]==results[2], 'disabled profile changed'
 frames=sum(x[0]=='FRAME' for x in results[0][0]);draws=sum(x[0] in ('DRAW','PANEL') for x in results[0][0])
 print(f'PASS HUD semantic comparison: {frames} cases / {draws} draws; complete palettes/text/clears; exact fixed-point panel geometry and every row color; all non-panel texture hashes/positions/transform/order unchanged; exact Phase4 vs enemy suffix vs disabled profile')
