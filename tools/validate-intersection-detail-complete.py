#!/usr/bin/env python3
"""Complete foreground art, exact protected planes, bounded heap and old decoder."""
from pathlib import Path
import argparse,hashlib,io,json,re,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='89b0332de1bd2c4e84e9f086cd0e078169bd8103';A=R/'art/intersection-detail-complete';O=R/'assets/level1-intersection'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def run(cmd,cwd=R):subprocess.run(cmd,cwd=cwd,check=True)
def span(s,name):
 m=re.search(r'^(?:static )?(?:void|int|unsigned) '+name+r'\([^\n]*\)\s*\{',s,re.M);assert m,name
 start=s.index('{',m.start());i=start+1;depth=1
 while depth:depth+=(s[i]=='{')-(s[i]=='}');i+=1
 return m.start(),start,i
proof=json.loads((A/'proof.json').read_text());old=(A/'before.bin').read_bytes();new=(O/'EXTPIX.BIN').read_bytes();mask=(A/'mask.bin').read_bytes()
assert proof['baseline']==BASE and len(old)==len(new)==len(mask)==640*240
for value,key in [(old,'before_sha256'),(new,'after_sha256'),(mask,'mask_sha256')]:assert hashlib.sha256(value).hexdigest()==proof[key]
for name,h in proof['source_sha256'].items():assert hashlib.sha256((A/name).read_bytes()).hexdigest()==h
for i,(b,n,m) in enumerate(zip(old,new,mask)):
 x=i%640;y=i//640;edit=y<151 and ((2<=x<240 and not(y<56 and x<64)) or x>=538)
 assert m==int(edit)
 assert b==n or m,('protected pixel',x,y)
 if m:assert n and not 240<=n<=247
assert proof['hotel_changes']==proof['outside_mask_changes']==0
m=json.loads((O/'manifest.json').read_text())
for n,h in m['sha256'].items():assert hashlib.sha256((O/n).read_bytes()).hexdigest()==h,n
assert m['packed_source_storage']=='existing-fixed-Jo-heap' and m['background_heap_bytes']==((m['packed_source_bytes']+7)&~3)+m['decode_cache_heap_bytes']
assert m['background_heap_bytes']+16384<393216 and m['resident_cell_bytes']==106496 and m['VDP2_reserved_bytes']==434176
# Check actual linked SDK addresses and the full fixed allocator, not a relaxed
# guessed WRAM guard. The released static source now places the entire Jo heap
# below sort work; the load-time owner also validates its exact run-time range.
scope={'struct':struct};helper=(R/'tools/test-coop-balance-runtime.py').read_text();exec(helper[helper.index('def symbols('):helper.index('s=symbols(')],scope)
sy=scope['symbols'](R/'build/game.elf');raw=(R/'build/game.raw').read_bytes();vertex=int.from_bytes(raw[sy['_Pbuffer']-0x06004000:sy['_Pbuffer']-0x06004000+4],'big');end=int(re.search(r'0x([0-9a-f]+)\s+__bend =',(R/'build/game.map').read_text()).group(1),16)
heapbase=[v for k,v in sy.items() if k.startswith('_global_memory.')];assert len(heapbase)==1
assert vertex==0x060e5784 and end<vertex and heapbase[0]+393216<=0x060c0000,(hex(end),heapbase)
if a.disc:
 import importlib.util
 spec=importlib.util.spec_from_file_location('bg',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(True)
 for n in ('IXPACK.BIN','IXOFF.BIN','IXMAP.BIN'):assert (R/'build/cd'/n).read_bytes()==(O/n).read_bytes()
 print(f'PASS complete detail: {m["tile_count"]} source tiles, hotel/protected planes exact; fixed heap {m["background_heap_bytes"]}/393216 B; linked end {end:#x} < actual SDK {vertex:#x}',flush=True)
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:run(['git','fetch','--no-tags','--depth=1','origin',BASE])
with tempfile.TemporaryDirectory(prefix='complete-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 allowed={'Makefile','src/parallax.c','src/intersection_data.h','tests/intersection/cache.c',*[f'assets/level1-intersection/{n}' for n in ('EXTPIX.BIN','IXPIX.BIN','IXMAP.BIN','IXPACK.BIN','IXOFF.BIN','manifest.json')]}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 assert old==(ref/'assets/level1-intersection/EXTPIX.BIN').read_bytes()
 for y in range(152):assert old[y*640+416:y*640+536]==new[y*640+416:y*640+536]
 oldp=(ref/'src/parallax.c').read_text();newp=(R/'src/parallax.c').read_text()
 # Every decoder/cache/prefetch/render function body stays exact. The only
 # native code changes are compressed storage ownership and boot/retire hooks.
 for name in re.findall(r'^(?:static )?(?:void|int|unsigned) (\w+)\([^\n]*\)\s*\{',oldp,re.M):
  if name not in ('mf_parallax_load','mf_parallax_leave'):
   _,a0,b0=span(oldp,name);_,a1,b1=span(newp,name);assert oldp[a0:b0]==newp[a1:b1],name
 assert oldp[oldp.index('#elif MF_PARALLAX_DEMO'):]==newp[newp.index('#elif MF_PARALLAX_DEMO'):]
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 run(['python3','tools/validate-hotel-detail.py',*(['--test'] if a.test else [])],ref)
if a.test:
 frozen={f:f.read_bytes() for f in [*O.glob('*.BIN'),O/'manifest.json',R/'src/intersection_data.h']}
 run(['python3','tools/apply-intersection-detail-complete.py']);run(['python3','tools/prepare-intersection-detail-complete.py']);assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic full art packing'
run(['python3','tools/test-intersection.py'])
with tempfile.TemporaryDirectory(prefix='full-heap-test-') as d:
 exe=str(Path(d)/'heap');run(['cc','-std=c99','-fsanitize=undefined','-fno-sanitize-recover=all','-ffunction-sections','-fdata-sections','-include',str(R/'build/build-info.h'),'-I'+str(R/'src'),'-I'+str(R/'build'),'-I'+str(R/'tests/parallax_mock'),str(R/'tests/intersection/heap.c'),'-Wl,--gc-sections','-o',exe]);run([exe])
print('PASS complete foreground scope, byte-identical gameplay/hotel/older art/palette/audio/Level2, unchanged decode/cache algorithm, owner failures/reloads/retirement and protected memory')
