#!/usr/bin/env python3
"""Phase 1 preservation: only 18 production registrations and their accounting."""
from pathlib import Path
import io,json,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
BASE='15387a314a51bffbe3e65152e45958ed5f3416c5'
allowed={'Makefile','src/main.c','src/animation_preview.c','src/arcade_fx_config.h',
         'tools/build-native.sh','tools/build-source-complete.sh','tools/audit-sprite-memory.py'}
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='sprite-cleanup-baseline-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:
   assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 marker='static int depth_key'
 assert (ref/'src/main.c').read_text().split(marker,1)[1]==(R/'src/main.c').read_text().split(marker,1)[1],'approved renderer/update changed'
 assert (R/'src/animation_preview.c').read_text().replace('-MF_FX_SAVED_BYTES-MF_LEGACY_SAVED_BYTES','-MF_FX_SAVED_BYTES')==(ref/'src/animation_preview.c').read_text(),'animation change outside accounting'
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 if '--disc' in sys.argv:(ref/'build').symlink_to(R/'build',target_is_directory=True)
 subprocess.run(['python3','tools/validate-e108-request.py',*[x for x in sys.argv[1:] if x in ('--test','--disc')]],cwd=ref,check=True)
print('PASS Phase1 scope: baseline assets/AI/input/audio/Level2 frozen; renderer/update unchanged; animation changes only subtract retired bytes',flush=True)
if '--disc' in sys.argv or '--test' in sys.argv:
 subprocess.run(['python3','tools/test-legacy-sprite-cleanup.py'],cwd=R,check=True)
