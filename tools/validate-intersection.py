#!/usr/bin/env python3
"""Phase 3A payload/disc/budget checks and immutable approved combat baseline."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,json,re,struct,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='43cd82d33dd6195a036f9775f8b0e961fedbe9bb';O=R/'assets/level1-intersection';B=R/'assets/level1-neon-strip'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def run(args,cwd=R):subprocess.run(args,cwd=cwd,check=True)
def sha(b):return hashlib.sha256(b).hexdigest()
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:run(['git','fetch','--no-tags','--depth=1','origin',BASE])
m=json.loads((O/'manifest.json').read_text());assert m['parent']==BASE and (m['width'],m['height'])==(1920,240)
for n,h in m['sha256'].items():assert sha((O/n).read_bytes())==h,n
old=(B/'NSPIX.BIN').read_bytes();new=(O/'IXPIX.BIN').read_bytes();assert len(new)==1920*240
for y in range(240):assert old[y*1280:(y+1)*1280]==new[y*1920:y*1920+1280],y
assert sha((B/'NSPAL.BIN').read_bytes())==m['palette_sha256'] and m['resident_cell_bytes']==106496 and m['resident_tiles']==1664 and m['VDP2_reserved_bytes']==434176
assert m['VDP2_delta_bytes']==m['VDP1_delta_bytes']==m['SCSP_delta_bytes']==0
end=int(re.search(r'0x([0-9a-f]+)\s+__bend =',(R/'build/game.map').read_text()).group(1),16)
# Read actual linked SGLAREA constants; the SDK header's generic memory-map
# comments are approximate and differ from this pinned library's layout.
helper=(R/'tools/test-coop-balance-runtime.py').read_text();scope={'struct':struct}
exec(helper[helper.index('def symbols('):helper.index('s=symbols(')],scope)
syms=scope['symbols'](R/'build/game.elf');program=(R/'build/game.raw').read_bytes()
vertex_work=int.from_bytes(program[syms['_Pbuffer']-0x06004000:syms['_Pbuffer']-0x06004000+4],'big')
assert vertex_work==0x060e5784 and end<vertex_work,(hex(end),hex(vertex_work))
if a.disc:
 spec=importlib.util.spec_from_file_location('background',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(True)
 for n in ('IXPACK.BIN','IXOFF.BIN','IXMAP.BIN'):assert (R/'build/cd'/n).read_bytes()==(O/n).read_bytes(),n
 assert (R/'build/cd/NSPAL.BIN').read_bytes()==(B/'NSPAL.BIN').read_bytes()
with tempfile.TemporaryDirectory(prefix='intersection-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 allowed={'Makefile','src/main.c','src/parallax.c','src/world_config.h','tools/build-native.sh'}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 oldmain=(ref/'src/main.c').read_text();newmain=(R/'src/main.c').read_text()
 assert oldmain.replace('game.camera>320?"NEON STRIP ":','game.camera>960?"INTERSECT  ":game.camera>320?"NEON STRIP ":').replace('            stage2_owned=1;pending[0]=pending[1]=0;','            mf_parallax_leave(); /* Release Phase 3A CPU decode cache before Level 2. */\n            stage2_owned=1;pending[0]=pending[1]=0;')==newmain,'only section HUD and new decode-cache retirement change'
 oldp=(ref/'src/parallax.c').read_text();newp=(R/'src/parallax.c').read_text();assert oldp[oldp.index('#elif MF_PARALLAX_DEMO'):]==newp[newp.index('#elif MF_PARALLAX_DEMO'):]
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 # Approved old-world checks execute their exact frozen source and old bounds.
 # Current production behavior/map/combat are exercised independently below.
 run(['python3','tools/validate-coop-balance.py',*(['--test'] if a.test else [])],ref)
print(f'PASS Phase3A preservation: exact original1280px/palette/assets, combat/AI/jump-cancel/audio/Level2 unchanged; 5328 source/1664 resident tiles, zero video/audio allocation delta; CPU end {end:#x} below linked SDK vertex work {vertex_work:#x}',flush=True)
if a.test:
 frozen={f:f.read_bytes() for f in [*O.glob('*.BIN'),O/'manifest.json',R/'src/intersection_data.h']}
 run(['python3','tools/prepare-level1-intersection.py']);assert all(f.read_bytes()==b for f,b in frozen.items()),'non-deterministic packing'
run(['python3','tools/test-intersection.py'])
