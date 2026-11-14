#!/usr/bin/env python3
from pathlib import Path
import argparse,hashlib,io,json,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];BASE='7312ce1a2c21ab7881ad9e617b60524bf5736cb6'
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
def run(args,cwd=R):subprocess.run(args,cwd=cwd,check=True)
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:run(['git','fetch','--depth=1','origin',BASE])
old=(R/'assets/intersection-scale-fix/before.bin').read_bytes();new=(R/'assets/level1-intersection/EXTPIX.BIN').read_bytes();mask=(R/'assets/intersection-scale-fix/mask.bin').read_bytes()
assert len(old)==len(new)==len(mask)==640*240
assert all(o==n for o,n,m in zip(old,new,mask) if not m),'approved perspective/road/sky changed'
assert all(n!=0 for n,m in zip(new,mask) if m),'transparent foreground facade'
with tempfile.TemporaryDirectory(prefix='scale-approved-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 allowed={'Makefile','src/intersection_data.h',*[f'assets/level1-intersection/{n}' for n in ('EXTPIX.BIN','IXPIX.BIN','IXPACK.BIN','IXOFF.BIN','IXMAP.BIN','manifest.json')]}
 for f in ref.rglob('*'):
  if f.is_file() and str(f.relative_to(ref)) not in allowed:assert (R/f.relative_to(ref)).read_bytes()==f.read_bytes(),f.relative_to(ref)
 assert old==(ref/'assets/level1-intersection/EXTPIX.BIN').read_bytes()
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 run(['python3','tools/validate-intersection.py',*(['--test'] if a.test else [])],ref)
if a.disc:
 import importlib.util
 spec=importlib.util.spec_from_file_location('bg',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(True)
 m=json.loads((R/'assets/level1-intersection/manifest.json').read_text())
 for n in ('IXPACK.BIN','IXOFF.BIN','IXMAP.BIN'):assert (R/'build/cd'/n).read_bytes()==(R/'assets/level1-intersection'/n).read_bytes()
print('PASS art-only scope: all runtime code/camera/AI/input/audio/Level2/palette and approved receding street unchanged; all foreground facade pixels opaque',flush=True)
run(['python3','tools/test-intersection.py'])
