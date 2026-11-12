#!/usr/bin/env python3
"""Exact allocation and ID-independent rendered-command/decoded-pixel comparison.
Runs actual approved/current loaders/renderers with mocked Saturn I/O, not an emulator.
"""
from pathlib import Path
import csv,hashlib,io,json,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'assets/legacy-sprite-cleanup.json').read_text())
def inventory(*args):
 result=subprocess.check_output(['python3','tools/audit-sprite-memory.py',*args],cwd=R,text=True)
 return list(csv.DictReader(result.splitlines()))
current=inventory();control=inventory('--legacy-bat')
assert len(current)==m['after']['definitions'] and sum(int(x['allocated_bytes']) for x in current)==m['after']['texture_bytes']
removed=[x for x in control if x['path'] in m['removed']]
assert len(removed)==18 and sum(int(x['allocated_bytes']) for x in removed)==65952
retained=[x for x in control if x not in removed]
assert len(retained)==len(current)
for old,new in zip(retained,current):
 for field in ('path','width','height','format','allocated_bytes','palette_at_registration'):
  assert old[field]==new[field],(field,old,new)
ranges=sorted((int(x['vdp1_offset']),int(x['vdp1_offset'])+int(x['allocated_bytes'])) for x in current if int(x['allocated_bytes']))
assert all(0x10000<=a<b<=0x7fef8 for a,b in ranges)
assert all(left[1]<=right[0] for left,right in zip(ranges,ranges[1:])), 'overlapping payloads'
assert ranges[-1][1]==0x10000+m['after']['texture_bytes']
assert all((R/'build/cd'/name).is_file() for name in m['removed']), 'source/runtime asset deleted'
assert sum(x['path']=='alias' for x in current)==14
assert sum(int(x['allocated_bytes'])>0 for x in current)==223
print('PASS exact registration-only delta: 18 named TGAs/65952 bytes; 237 definitions/386848 bytes/71640 free; 223 payloads/14 views; every other registration retained',flush=True)
# Also exercise the default historical path and counterfactual FX profile.
assert len(inventory('--legacy-fx'))==255
assert len(inventory('--legacy-fx','--without-combo'))==253
with tempfile.TemporaryDirectory(prefix='cleanup-equivalence-') as d:
 work=Path(d);baseline=work/'baseline';baseline.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',m['baseline']],cwd=R))) as t:t.extractall(baseline,filter='data')
 results=[]
 for label,source,flag in [('baseline',baseline,0),('optimized',R,1),('historical',R,0)]:
  header=(R/'build/build-info.h').read_text()
  header=header.replace('#define MF_LEGACY_SPRITE_CLEANUP 1','#define MF_LEGACY_SPRITE_CLEANUP 0')
  if '#define MF_LEGACY_SPRITE_CLEANUP' not in header:header+='\n#define MF_LEGACY_SPRITE_CLEANUP 0\n'
  header=header.replace('#define MF_LEGACY_SPRITE_CLEANUP 0',f'#define MF_LEGACY_SPRITE_CLEANUP {flag}')
  # This temporary copy of the real main includes all current drawing code.
  text='#include <stdio.h>\n#include <assert.h>\n#include <string.h>\nvoid audit_finish(void);\n'
  text+=(source/'src/main.c').read_text().split('static void update(void)')[0]
  text+='\n#include "'+str(R/'tests/sprite_cleanup/scenarios.inc')+'"\n'
  local=work/('unit-'+label);local.mkdir();(local/'build-info.h').write_text(header);(local/'main.c').write_text(text)
  exe=local/'trace'
  subprocess.run(['cc','-std=c99','-ffunction-sections','-fdata-sections','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(local/'build-info.h'),'-I'+str(R/'tests/sprite_cleanup'),'-I'+str(local),'-I'+str(source/'src'),str(local/'main.c'),str(R/'tests/sprite_cleanup/trace.c'),*[str(source/'src'/n) for n in ('animation_preview.c','corporate_animation.c','gallery.c','player_animation.c','game.c')],'-Wl,--gc-sections','-o',str(exe)],cwd=R,check=True)
  p=local/'trace.txt'
  with p.open('w') as f:subprocess.run([str(exe)],cwd=R,check=True,stdout=f)
  textures={};palettes={};commands=[]
  for line in p.read_text().splitlines():
   fields=line.split('|')
   if fields[0]=='TEXTURE':
    _,ident,name,w,h,mode,allocated,offset,data=fields
    textures[ident]=(int(w),int(h),int(mode),hashlib.sha256(bytes.fromhex(data)).hexdigest())
   elif fields[0]=='PALETTE':palettes[fields[1]]=fields[2]
   else:commands.append(fields)
  canonical=[]
  for f in commands:
   if f[0]=='DRAW':canonical.append(tuple(f[:2])+textures[f[2]]+tuple(f[3:]))
   else:canonical.append(tuple(f))
  results.append((canonical,palettes))
 assert results[0]==results[1], 'optimized pixels/positions/transforms/palettes/frame sequence differ'
 assert results[0]==results[2], 'historical profile changed'
 frames=sum(x[0]=='FRAME' for x in results[0][0]);draws=sum(x[0]=='DRAW' for x in results[0][0])
 print(f'PASS semantic visuals: {frames} cases / {draws} draw commands; actual baseline vs optimized vs historical; exact decoded texture hashes/crop views, palettes, positions, flip/scales/depth, animation order, HUD/gallery/review; no emulator/hardware claim')
