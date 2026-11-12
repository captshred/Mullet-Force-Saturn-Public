#!/usr/bin/env python3
"""Phase 2 preservation: only 83 additional production registrations and their accounting."""
from pathlib import Path
import io,json,subprocess,sys,tarfile,tempfile
R=Path(__file__).resolve().parents[1]
BASE='ea6e3e8bc59340226218366573bb9337e9dd0cff'
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
 assert (ref/'src/animation_preview.c').read_text().split('unsigned mf_animation_texture_bytes',1)[1]==(R/'src/animation_preview.c').read_text().replace('-MF_LEGACY_PLAYER_SAVED_BYTES','').replace('-MF_LEGACY_RBV_SAVED_BYTES','').replace('-MF_LEGACY_CA_SAVED_BYTES','').split('unsigned mf_animation_texture_bytes',1)[1],'animation renderer/update changed'
 for n in ('.git','.deps'):(ref/n).symlink_to(R/n,target_is_directory=True)
 # Native staging contains copies of current src headers. Never let those
 # shadow the archived profile's own config headers during its host tests.
 (ref/'build').mkdir()
 for p in (R/'build').iterdir():
  if p.suffix not in ('.h','.c'):(ref/'build'/p.name).symlink_to(p,target_is_directory=p.is_dir())
 (ref/'build/build-info.h').write_text((R/'build/build-info.h').read_text().replace('#define MF_LEGACY_SPRITE_PHASE2 1','#define MF_LEGACY_SPRITE_PHASE2 0'))
 subprocess.run(['python3','tools/validate-legacy-sprite-cleanup.py',*[x for x in sys.argv[1:] if x in ('--test','--disc')]],cwd=ref,check=True)
print('PASS Phase2 scope: baseline assets/AI/input/audio/Level2 frozen; renderer/update unchanged; animation renderer unchanged; only loader/profile/accounting changed',flush=True)
if '--disc' in sys.argv or '--test' in sys.argv:
 subprocess.run(['python3','tools/test-legacy-sprite-phase2.py'],cwd=R,check=True)
