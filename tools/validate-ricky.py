#!/usr/bin/env python3
"""Phase 6 preservation lock, original Phase 5 suite, then Ricky checks."""
from pathlib import Path
import csv,hashlib,io,json,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='1dd66746f37333914408234fc14d520858ac59fd'
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
allowed={'Makefile','make/saturn.mk','src/main.c','src/game.c','src/game.h','src/arcade_fx_config.h','tools/build-native.sh','tools/build-source-complete.sh','tools/audit-sprite-memory.py'}
with tempfile.TemporaryDirectory(prefix='ricky-phase5-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:
   assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 (ref/'build').mkdir()
 for p in (R/'build').iterdir():
  if p.suffix not in ('.h','.c'):(ref/'build'/p.name).symlink_to(p,target_is_directory=p.is_dir())
 (ref/'build/build-info.h').write_text((R/'build/build-info.h').read_text().replace('#define MF_RICKY_ENEMY 1','#define MF_RICKY_ENEMY 0'))
 subprocess.run(['python3','tools/validate-enemy-sprite-banks.py',*[x for x in sys.argv[1:] if x in ('--test','--disc')]],cwd=ref,check=True)
print('PASS Phase 5 frozen assets/audio/Level2/CP/players/input/bank manager; original suite unchanged',flush=True)
subprocess.run(['python3','tools/test-ricky-rose-art.py'],cwd=R,check=True)
m=json.loads((R/'assets/ricky/manifest.json').read_text());assert hashlib.sha256((R/m['source']).read_bytes()).hexdigest()==m['source_sha256']==json.loads((R/'art/ricky/provenance.json').read_text())['source_sha256']
assert len(m['frames'])==m['definitions']==25
for i,f in enumerate(m['frames']):
 b=(R/f'assets/ricky/RK{i:02}.TGA').read_bytes();assert len(b)==786+f['width']*f['height']
 assert b[2]==1 and b[16:18]==bytes([8,32]);assert max(b[786:])<255
 assert hashlib.sha256(bytes(0 if v==0 else v+1 for v in b[786:])).hexdigest()==f['decoded_sha256']
 assert f['width']%8==0 and f['bytes']==(f['width']*f['height']+31)&~31
assert sum(f['bytes'] for f in m['frames'])==114048 and 458488-257024-114048>=49152
rows=list(csv.DictReader(subprocess.check_output(['python3','tools/audit-sprite-memory.py'],cwd=R,text=True).splitlines()))
assert len(rows)==177 and sum(int(r['allocated_bytes']) for r in rows)==371072
print('PASS source/25 indexed frames/key range/padding/decoded payloads; 177 definitions, 371072 bytes, 87416 free, reserve 49152',flush=True)
subprocess.run(['python3','tools/test-ricky.py'],cwd=R,check=True)

subprocess.run(['python3','tools/test-ricky-preservation.py'],cwd=R,check=True)
