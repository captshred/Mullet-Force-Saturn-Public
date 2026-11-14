#!/usr/bin/env python3
"""Local index-zero repair, exact approved-art scope, native payload and budgets."""
from pathlib import Path
import argparse,hashlib,io,json,re,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='5363539d048062af7e862d75dd232db4bb310aad';A=R/'art/intersection-facade-seal';O=R/'assets/level1-intersection'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def run(cmd,cwd=R):subprocess.run(cmd,cwd=cwd,check=True)
def sha(b):return hashlib.sha256(b).hexdigest()
proof=json.loads((A/'proof.json').read_text());old=(A/'before.bin').read_bytes();new=(O/'EXTPIX.BIN').read_bytes();mask=(A/'mask.bin').read_bytes()
assert proof['baseline']==BASE and len(old)==len(new)==len(mask)==640*240
for b,key in [(old,'before_sha256'),(new,'after_sha256'),(mask,'mask_sha256')]:assert sha(b)==proof[key]
assert sum(b!=n for b,n in zip(old,new))==proof['changed_pixels']
for i,(b,n,m) in enumerate(zip(old,new,mask)):
 x=i%640;y=i//640
 if m==0:assert n==b,('outside scope',x,y)
 elif m==1:assert x<62 and y<56 and n!=0 and not 240<=n<=247
 elif m==2:assert y<56 and (241<=x<291 or 366<=x<416) and b==0 and n!=0 and not 240<=n<=247
 elif m==3:assert 325<=x<338 and 27<=y<41 and n==0
 else:assert False
assert proof['side_nonzero_changes']==0
for y in range(240):assert old[y*640+416:y*640+640]==new[y*640+416:y*640+640], 'hotel/records changed'
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
 run(['python3','tools/validate-intersection-window-opacity.py',*(['--test'] if a.test else [])],ref)
if a.test:
 frozen={f:f.read_bytes() for f in [*O.glob('*.BIN'),O/'manifest.json',R/'src/intersection_data.h',*A.glob('*')]}
 run(['python3','tools/apply-intersection-facade-seal.py']);run(['python3','tools/prepare-intersection-facade-seal.py']);assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic opacity repair/pack'
run(['python3','tools/test-intersection.py'])
with tempfile.TemporaryDirectory(prefix='opaque-heap-') as d:
 exe=str(Path(d)/'heap');run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-I'+str(R/'tests/parallax_mock'),str(R/'tests/intersection/heap.c'),'-Wl,--gc-sections','-o',exe]);run([exe])
print(f'PASS window-only repair: {proof['changed_pixels']} targeted pixels; protected artwork/palette/runtime exact; {m["tile_count"]} source tiles; owner {m["background_heap_bytes"]}/393216 B; VDP2 {m["VDP2_reserved_bytes"]} B; linked end {end:#x} < SDK {vertex:#x}')
