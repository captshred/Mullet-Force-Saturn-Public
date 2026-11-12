#!/usr/bin/env python3
"""Exact allocation and ID-independent rendered-command/decoded-pixel comparison.
Runs actual approved/current loaders/renderers with mocked Saturn I/O, not an emulator.
"""
from pathlib import Path
import csv,hashlib,io,json,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
m=json.loads((R/'assets/duplicate-texture-cleanup.json').read_text())
def inventory(*args):
 result=subprocess.check_output(['python3','tools/audit-sprite-memory.py',*args],cwd=R,text=True)
 return list(csv.DictReader(result.splitlines()))
current=inventory();control=inventory('--phase2')
assert len(current)==m['after']['definitions'] and sum(int(x['allocated_bytes']) for x in current)==m['after']['texture_bytes']
removed=[x for x in control if x['path'] in m['removed']]
assert len(removed)==2 and sum(int(x['allocated_bytes']) for x in removed)==2016
for pair in m['pairs']:
 duplicate=(R/'build/cd'/pair['duplicate']).read_bytes()
 canonical=(R/'build/cd'/pair['canonical']).read_bytes()
 assert duplicate==canonical, 'candidate no longer byte-identical (including palette/header)'
 assert hashlib.sha256(duplicate).hexdigest()==pair['file_sha256']
 assert duplicate[2]==1 and duplicate[16]==8 and duplicate[7]==24
 w=int.from_bytes(duplicate[12:14],'little');h=int.from_bytes(duplicate[14:16],'little')
 assert (w,h)==(pair['width'],pair['height'])
 off=18+int.from_bytes(duplicate[5:7],'little')*3
 raw=duplicate[off:off+w*h];assert len(raw)==w*h
 pixels=bytes(0 if ((v+1)&255)==1 else ((v+1)&255) for v in raw)
 if not duplicate[17]&32:pixels=b''.join(pixels[y*w:(y+1)*w] for y in reversed(range(h)))
 assert hashlib.sha256(pixels).hexdigest()==pair['decoded_sha256']
 for inv in (control,current):
  names={x['path']:x for x in inv if x['path']!='alias'}
  for name in (pair['canonical'],pair['duplicate']):
   if name not in names:continue
   row=names[name];assert row['format']=='indexed8' and row['palette_at_registration']=='7'
   start=int(row['vdp1_offset']);end=start+int(row['allocated_bytes'])
   assert not any(x['path']=='alias' and start<=int(x['vdp1_offset'])<end for x in inv), 'unexpected dependent crop/tail view'
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
assert sum(int(x['allocated_bytes'])>0 for x in current)==138
print('PASS duplicate delta: CA02 -> GB2 /960 bytes; CA30 -> GC2 /1056 bytes; 152 definitions/276864 bytes/181624 free; 138 payloads/14 views',flush=True)
# Also exercise the default historical path and counterfactual FX profile.
assert len(inventory('--legacy-fx'))==255
assert len(inventory('--legacy-fx','--without-combo'))==253
with tempfile.TemporaryDirectory(prefix='cleanup-equivalence-') as d:
 work=Path(d);baseline=work/'baseline';baseline.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',m['baseline']],cwd=R))) as t:t.extractall(baseline,filter='data')
 results=[]
 for label,source,flag in [('phase2',baseline,0),('phase3',R,1),('phase3-off',R,0),('historical-baseline',baseline,0),('historical-current',R,0)]:
  header=(R/'build/build-info.h').read_text()
  header=header.replace('#define MF_DUPLICATE_TEXTURE_CLEANUP 1','#define MF_DUPLICATE_TEXTURE_CLEANUP 0')
  if '#define MF_DUPLICATE_TEXTURE_CLEANUP' not in header:header+='\n#define MF_DUPLICATE_TEXTURE_CLEANUP 0\n'
  header=header.replace('#define MF_DUPLICATE_TEXTURE_CLEANUP 0',f'#define MF_DUPLICATE_TEXTURE_CLEANUP {flag}')
  if label.startswith('historical'):
   header=header.replace('#define MF_LEGACY_SPRITE_PHASE2 1','#define MF_LEGACY_SPRITE_PHASE2 0')
   header=header.replace('#define MF_LEGACY_SPRITE_CLEANUP 1','#define MF_LEGACY_SPRITE_CLEANUP 0')
  # This temporary copy of the real main includes all current drawing code.
  text='#include <stdio.h>\n#include <assert.h>\n#include <string.h>\nvoid audit_finish(void);\n'
  text+=(source/'src/main.c').read_text().split('static void update(void)')[0]
  scenarios=(R/'tests/sprite_cleanup/scenarios.inc').read_text()
  if flag:
   text+='\nvoid verify_mapping(void);\n'
   scenarios=scenarios.replace('load_assets();','load_assets();verify_mapping();')
  text+='\n'+scenarios

  local=work/('unit-'+label);local.mkdir();(local/'build-info.h').write_text(header);(local/'main.c').write_text(text)
  exe=local/'trace'
  animation=source/'src/animation_preview.c'
  if flag:
   animation=local/'animation_preview.c'
   animation.write_text('#include <assert.h>\n'+(source/'src/animation_preview.c').read_text()+'\nvoid verify_mapping(void){assert(ca_ids[2]==resource_ids[2]);assert(ca_ids[30]==resource_ids[23]);}\n')
  subprocess.run(['cc','-std=c99','-ffunction-sections','-fdata-sections','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(local/'build-info.h'),'-I'+str(R/'tests/sprite_cleanup'),'-I'+str(local),'-I'+str(source/'src'),str(local/'main.c'),str(R/'tests/sprite_cleanup/trace.c'),str(animation),*[str(source/'src'/n) for n in ('corporate_animation.c','gallery.c','player_animation.c','game.c')],'-Wl,--gc-sections','-o',str(exe)],cwd=R,check=True)
  p=local/'trace.txt'
  with p.open('w') as f:subprocess.run([str(exe)],cwd=R,check=True,stdout=f)
  textures={};names={};palettes={};commands=[]
  for line in p.read_text().splitlines():
   fields=line.split('|')
   if fields[0]=='TEXTURE':
    _,ident,name,w,h,mode,allocated,offset,data=fields
    names[ident]=name
    textures[ident]=(int(w),int(h),int(mode),hashlib.sha256(bytes.fromhex(data)).hexdigest())
   elif fields[0]=='PALETTE':palettes[fields[1]]=fields[2]
   else:commands.append(fields)
  canonical=[];used_palettes=set()
  for f in commands:
   if f[0]=='DRAW':
    if flag:assert names[f[2]] not in m['removed'], 'unexpected duplicate registration'
    if textures[f[2]][2]==1:used_palettes.add(f[-1])
    canonical.append(tuple(f[:2])+textures[f[2]]+tuple(f[3:]))
   else:canonical.append(tuple(f))
  assert not ({'2','3'} & used_palettes), 'retired fallback palette still has an indexed draw consumer'
  results.append((canonical,palettes))
  if label=='phase3':print('PASS explicit canonical handle mappings, complete palettes and decoded texture equivalence',flush=True)
 assert results[0]==results[1], 'optimized pixels/positions/transforms/palettes/frame sequence differ'
 assert results[0]==results[2], 'Duplicate cleanup disabled profile changed'
 assert results[3]==results[4], 'historical profile changed'
 # Historical profiles intentionally populate unused fallback palettes 2/3;
 # compare every palette within each profile, and draw content across profiles.
 assert results[0][0]==results[3][0], 'historical visual content differs'
 frames=sum(x[0]=='FRAME' for x in results[0][0]);draws=sum(x[0]=='DRAW' for x in results[0][0])
 print(f'PASS semantic visuals: {frames} cases / {draws} draw commands; exact Phase2 vs Phase3 vs disabled/historical profiles; exact decoded texture hashes/crop views, palettes, positions, flip/scales/depth, animation order, HUD/gallery/review; no emulator/hardware claim')
