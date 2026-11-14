#!/usr/bin/env python3
"""Local index-zero repair, exact approved-art scope, native payload and budgets."""
from pathlib import Path
import argparse,hashlib,io,json,re,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='e270d2dd8461475185be6eac503ce0c0f874974b';A=R/'art/intersection-window-opacity';O=R/'assets/level1-intersection'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def run(cmd,cwd=R):subprocess.run(cmd,cwd=cwd,check=True)
def sha(b):return hashlib.sha256(b).hexdigest()
spec=json.loads((A/'openings.json').read_text());proof=json.loads((A/'proof.json').read_text());old=(A/'before.bin').read_bytes();new=(O/'EXTPIX.BIN').read_bytes();mask=(A/'mask.bin').read_bytes();expected=bytearray(len(old))
assert spec['baseline']==proof['baseline']==BASE and len(old)==len(new)==len(mask)==640*240
for opening in spec['openings']:
 x0,y0,x1,y1=opening['box'];assert 241<=x0<x1<=416 and 0<=y0<y1<=56
 for y in range(y0,y1):
  for x in range(x0,x1):
   i=y*640+x
   if old[i]==0:expected[i]=1
assert mask==expected and sum(mask)==proof['changed_pixels']>0
for b,key in [(old,'before_sha256'),(new,'after_sha256'),(mask,'mask_sha256')]:assert sha(b)==proof[key]
for i,(b,n,m) in enumerate(zip(old,new,mask)):
 assert n==(spec['opaque_index'] if m else b),('unapproved pixel',i%640,i//640)
assert spec['opaque_index']==224 and not 240<=224<=247
palette=struct.unpack('>255H',(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())
assert palette[223]==0x8400 # Existing darkest opaque ink: RGB555 (0,0,1).
assert all(sum(((c>>s)&31)**2 for s in (0,5,10))>=1 for c in palette)
m=json.loads((O/'manifest.json').read_text())
for n,h in m['sha256'].items():assert sha((O/n).read_bytes())==h,n
assert m['extension_sha256']==sha(new) and m['palette_sha256']==sha((R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes())
pixels=(O/'IXPIX.BIN').read_bytes();original=(R/'assets/level1-neon-strip/NSPIX.BIN').read_bytes()
for y in range(240):
 assert pixels[y*1920:y*1920+1280]==original[y*1280:(y+1)*1280]
 assert pixels[y*1920+1280:(y+1)*1920]==new[y*640:(y+1)*640]
assert m['background_heap_bytes']==((m['packed_source_bytes']+7)&~3)+m['decode_cache_heap_bytes']
assert m['background_heap_bytes']+16384<393216 and m['VDP2_reserved_bytes']==434176 and m['resident_cell_bytes']==106496
assert m['VDP1_delta_bytes']==m['VDP2_delta_bytes']==m['SCSP_delta_bytes']==0
helper=(R/'tools/test-coop-balance-runtime.py').read_text();scope={'struct':struct};exec(helper[helper.index('def symbols('):helper.index('s=symbols(')],scope);sy=scope['symbols'](R/'build/game.elf');raw=(R/'build/game.raw').read_bytes();vertex=int.from_bytes(raw[sy['_Pbuffer']-0x06004000:sy['_Pbuffer']-0x06004000+4],'big');end=int(re.search(r'0x([0-9a-f]+)\s+__bend =',(R/'build/game.map').read_text()).group(1),16)
heap=[v for k,v in sy.items() if k.startswith('_global_memory.')];assert len(heap)==1 and heap[0]+393216<=0x060c0000 and end<vertex==0x060e5784
if a.disc:
 for n in ('IXPACK.BIN','IXOFF.BIN','IXMAP.BIN'):assert (R/'build/cd'/n).read_bytes()==(O/n).read_bytes()
 assert (R/'build/cd/NSPAL.BIN').read_bytes()==(R/'assets/level1-neon-strip/NSPAL.BIN').read_bytes()
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:run(['git','fetch','--no-tags','--depth=1','origin',BASE])
with tempfile.TemporaryDirectory(prefix='opaque-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 allowed={'Makefile','src/intersection_data.h',*[f'assets/level1-intersection/{n}' for n in ('EXTPIX.BIN','IXPIX.BIN','IXPACK.BIN','IXOFF.BIN','IXMAP.BIN','manifest.json')]}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 assert old==(ref/'assets/level1-intersection/EXTPIX.BIN').read_bytes()
 prior=json.loads((ref/'assets/level1-intersection/manifest.json').read_text())
 for k in ('width','height','codec','resident_tiles','resident_cell_bytes','map_bytes','chunk_bytes','VDP2_reserved_bytes','palette_sha256'):assert m[k]==prior[k],k
 # Run frozen historical art proofs on their exact approved assets, never weaken them.
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 run(['python3','tools/validate-intersection-detail-complete.py',*(['--test'] if a.test else [])],ref)
if a.test:
 frozen={f:f.read_bytes() for f in [*O.glob('*.BIN'),O/'manifest.json',R/'src/intersection_data.h',*A.glob('*')]}
 run(['python3','tools/apply-intersection-window-opacity.py']);run(['python3','tools/prepare-intersection-window-opacity.py']);assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic opacity repair/pack'
run(['python3','tools/test-intersection.py'])
with tempfile.TemporaryDirectory(prefix='opaque-heap-') as d:
 exe=str(Path(d)/'heap');run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-I'+str(R/'tests/parallax_mock'),str(R/'tests/intersection/heap.c'),'-Wl,--gc-sections','-o',exe]);run([exe])
print(f'PASS window-only repair: {sum(mask)} zero-index pixels; all nonzero artwork/palette/runtime exact; {m["tile_count"]} source tiles; owner {m["background_heap_bytes"]}/393216 B; VDP2 {m["VDP2_reserved_bytes"]} B; linked end {end:#x} < SDK {vertex:#x}')
