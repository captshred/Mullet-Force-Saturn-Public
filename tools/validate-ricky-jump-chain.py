#!/usr/bin/env python3
"""Current jump candidate checks plus immutable approved world-flow suites."""
from pathlib import Path
from PIL import Image
import argparse,hashlib,importlib.util,io,json,re,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='cc10880983bbb761461d7e13cb2cd06a36c55ee1'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
spec=importlib.util.spec_from_file_location('bg',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(a.disc)
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
allowed={'Makefile','tools/bootstrap.sh','Ricky_HQ_Animation_Sheet.png','tools/prepare-ricky-art.py','assets/ricky/RK16.TGA','assets/ricky/RK17.TGA','assets/ricky/atlas.png','assets/ricky/jump-0.png','assets/ricky/jump-1.png','assets/ricky/manifest.json','src/game.c','src/game.h','src/ricky_config.h','src/ricky_animation.c','src/main.c'}
def body(text,name):
 m=re.search(r'^(?:static )?(?:void|int|unsigned|mf_hitbox) \**'+name+r'\([^\n]*\)\s*\{',text,re.M);assert m,name
 start=text.index('{',m.start());end=start+1;depth=1
 while depth:depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
with tempfile.TemporaryDirectory(prefix='jump-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 assert (ref/'tools/bootstrap.sh').read_text().replace('ffmpeg python3-pil','ffmpeg python3-pil python3-numpy python3-scipy')==(R/'tools/bootstrap.sh').read_text(),'unrelated bootstrap change'
 old=(ref/'src/game.c').read_text();new=(R/'src/game.c').read_text()
 names=re.findall(r'^(?:static )?(?:void|int|unsigned|mf_hitbox) \**(\w+)\([^\n]*\)\s*\{',old,re.M)
 for name in names:
  if name not in ('ricky_step','enemy_step','enemy_spawn'):assert body(old,name)==body(new,name),'unreviewed gameplay change: '+name
 # These shared functions must remain exact after removing the Ricky-only additions.
 for name in ('enemy_spawn','enemy_step'):
  current=body(new,name)
  if name=='enemy_spawn':current=current.replace('g->ricky_punch[index]=0;g->ricky_jump[index]=(mf_ricky_jump){0};','g->ricky_punch[index]=0;')
  else:
   begin=current.index('#if MF_RICKY_ENEMY\n    if(g->enemy_class[index]==MF_ENEMY_RICKY)')
   end=current.index('#endif',begin)+len('#endif\n');current=current[:begin]+current[end:]
   current=current.replace('g->ricky_punch[index]=0;g->ricky_jump[index].active=g->ricky_jump[index].height=0;','g->ricky_punch[index]=0;')
  assert current==body(old,name),'shared/CP processing changed: '+name
 # CPU prefix and world state offsets are retained; only append the new state.
 oldim=Image.open(ref/'Ricky_HQ_Animation_Sheet.png').convert('RGB');newim=Image.open(R/'Ricky_HQ_Animation_Sheet.png').convert('RGB')
 assert oldim.size==newim.size==(1536,1024)
 proof=json.loads((R/'art/ricky/jump-chain/provenance.json').read_text());assert proof['parent']==BASE
 assert hashlib.sha256((R/'Ricky_HQ_Animation_Sheet.png').read_bytes()).hexdigest()==proof['source_sha256']
 regions=proof['regions'];ob=oldim.tobytes();nb=newim.tobytes()
 for i in range(1536*1024):
  if ob[3*i:3*i+3]!=nb[3*i:3*i+3]:assert any(x0<=i%1536<x1 and y0<=i//1536<y1 for x0,y0,x1,y1 in regions),'authoring change outside jumps'
 oldm=json.loads((ref/'assets/ricky/manifest.json').read_text());m=json.loads((R/'assets/ricky/manifest.json').read_text())
 assert m['source_sha256']==proof['source_sha256']
 assert m['definitions']==oldm['definitions']==25 and m['texture_bytes']==oldm['texture_bytes']==114048 and m['reserve']==49152
 for i,(before,after) in enumerate(zip(oldm['frames'],m['frames'])):
  for k in before:
   if i not in (16,17) or k!='decoded_sha256':assert before[k]==after[k],(i,k)
  b=(R/f'assets/ricky/RK{i:02}.TGA').read_bytes();assert b[18:786]==(ref/f'assets/ricky/RK{i:02}.TGA').read_bytes()[18:786]
  if i in (16,17):
   assert b!=(ref/f'assets/ricky/RK{i:02}.TGA').read_bytes()
   assert (R/f'art/ricky/jump-chain/RK{i:02}.before.TGA').read_bytes()==(ref/f'assets/ricky/RK{i:02}.TGA').read_bytes()
   assert len(b)==786+after['width']*after['height']
  else:assert b==(ref/f'assets/ricky/RK{i:02}.TGA').read_bytes()
 print('PASS art/source: only two jump regions, all 23 other poses and palettes byte-exact, dimensions/anchors/IDs fixed; Ricky 114048 bytes, protected reserve 49152; world/CP/audio/Level2 assets frozen',flush=True)
 subprocess.run(['python3','tools/test-world-flow-phase1.py'],cwd=R,check=True)
 with tempfile.TemporaryDirectory(prefix='jump-host-') as h:
  exe=Path(h)/'jump';subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),str(R/'tests/ricky/jump-chain.c'),'-o',str(exe)],check=True);subprocess.run([str(exe)],cwd=R,check=True)
 if a.test:
  subprocess.run(['python3','tools/test-ricky-jump-render.py'],cwd=R,check=True)
  # Conversion must reproduce committed payloads exactly, not merely fit budgets.
  generated=[*sorted((R/'assets/ricky').glob('*.TGA')),R/'assets/ricky/palette.bgr24',R/'assets/ricky/manifest.json',R/'src/ricky_data.h',R/'src/ricky_budget.h']
  frozen={f:f.read_bytes() for f in generated if f.is_file()}
  subprocess.run(['python3','tools/prepare-ricky-art.py'],cwd=R,check=True)
  assert all(f.read_bytes()==data for f,data in frozen.items()),'non-deterministic sprite conversion'
  with tempfile.TemporaryDirectory(prefix='jump-frequency-') as h:
   exe=Path(h)/'frequency';subprocess.run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),str(R/'tests/ricky/jump-chain-frequency.c'),'-o',str(exe)],check=True)
   result=json.loads(subprocess.check_output([str(exe)],cwd=R,text=True));assert all(result[k]>0 for k in ('punch','standing_chain','jump_chain'));print('PASS normal-input attack frequency: '+json.dumps(result),flush=True)
  # Run the existing bank lifecycle/failure/reload and palette/render checks on
  # current source; combat is covered above with the Phase 1 handoff fixture.
  s=(R/'tools/test-ricky.py').read_text();start=s.index(" exe=w/'combat';");end=s.index(' main=',start);s=s[:start]+s[end:]
  exec(compile(s,str(R/'tools/test-ricky.py'),'exec'),{'__file__':str(R/'tools/test-ricky.py'),'__name__':'__main__'})
 for name in ('.git','.deps','build'):(ref/name).symlink_to(R/name,target_is_directory=True)
 subprocess.run(['python3','tools/validate-world-flow-phase1.py',*(['--test'] if a.test else [])],cwd=ref,check=True)
print('PASS jump candidate plus exact approved Phase 1 world-flow preservation suites')
