#!/usr/bin/env python3
"""Phase 1 scope, current combat/map tests and immutable approved-parent suites."""
from pathlib import Path
import argparse,hashlib,importlib.util,io,re,subprocess,tarfile,tempfile
R=Path(__file__).resolve().parents[1];PARENT='30996986f76d17863f0fe6c5a87f2a5c17cf6c68'
ALLOWED={'Makefile','src/game.c','src/game.h','src/main.c','src/parallax.c'}
def function(text,name):
 m=re.search(r'^(?:static )?[^\n]+\b'+name+r'\([^\n]*\)\s*\{',text,re.M);assert m,name
 start=text.index('{',m.start());depth=1;end=start+1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 return text[start:end]
def normalized(text):
 for a,b in [('MF_ENEMY_WORLD_LEFT','26'),('MF_ENEMY_WORLD_RIGHT','614'),('MF_WORLD_LEFT','26'),('MF_WORLD_RIGHT','614')]:text=text.replace(a,b)
 return text
p=argparse.ArgumentParser();p.add_argument('--disc',action='store_true');p.add_argument('--test',action='store_true');a=p.parse_args()
# Current production disc still uses the exact approved background payloads.
spec=importlib.util.spec_from_file_location('background',R/'tools/validate-level1-background-touchups.py');bg=importlib.util.module_from_spec(spec);spec.loader.exec_module(bg);bg.validate(a.disc)
subprocess.run(['python3','tools/test-world-flow-phase1.py'],cwd=R,check=True)
if subprocess.run(['git','cat-file','-e',PARENT+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:subprocess.run(['git','fetch','--no-tags','--depth=1','origin',PARENT],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='world-approved-parent-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',PARENT],cwd=R))) as t:t.extractall(ref,filter='data')
 for path in ref.rglob('*'):
  if path.is_file() and str(path.relative_to(ref)) not in ALLOWED:assert (R/path.relative_to(ref)).read_bytes()==path.read_bytes(),str(path.relative_to(ref))
 old=(ref/'src/game.c').read_text();new=(R/'src/game.c').read_text()
 for name in ('torch_cancel','torch_interrupt','mf_torch_active','mf_boxes_overlap','fire_damage','choose_target','punk_attack','punk_pursue','ricky_step','torch_input','torch_events','mf_torch_hits','torch_hits','player_hits'):
  assert normalized(function(new,name))==function(old,name),'unreviewed combat/AI change: '+name
 for n in ('.git','.deps','build'):(ref/n).symlink_to(R/n,target_is_directory=True)
 subprocess.run(['python3','tools/validate-level1-background-touchups.py',*(['--test'] if a.test else [])],cwd=ref,check=True)
print('PASS world scope: exact approved 3099698 art/audio/Level2/budgets and original suites; damage/charge/flame/AI controller bodies preserved except world bounds; new flow tested with production flags')
