#!/usr/bin/env python3
"""Diagnostic-only scope gate; retain baseline locks without rewriting them."""
from pathlib import Path
import subprocess,tempfile,tarfile,io,sys
R=Path(__file__).resolve().parents[1]
BASE='bb7b6b61af79ccddd9994a9623456d3f10ad6613'
allowed={'Makefile','src/main.c','src/wingsuit_audio.c','src/wingsuit_audio.h','src/wingsuit_runtime.c'}
if subprocess.run(['git','cat-file','-e',BASE+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',BASE],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='e008-baseline-') as d:
 ref=Path(d)
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',BASE],cwd=R))) as t:t.extractall(ref,filter='data')
 for p in ref.rglob('*'):
  if p.is_file() and str(p.relative_to(ref)) not in allowed:
   assert (R/p.relative_to(ref)).read_bytes()==p.read_bytes(),str(p.relative_to(ref))
 (ref/'.git').symlink_to(R/'.git',target_is_directory=True)
 (ref/'.deps').symlink_to(R/'.deps',target_is_directory=True)
 if '--disc' in sys.argv:(ref/'build').symlink_to(R/'build',target_is_directory=True)
 subprocess.run(['python3','tools/validate-source-recovery.py',*(['--disc'] if '--disc' in sys.argv else [])],cwd=ref,check=True)
 if '--test' in sys.argv:subprocess.run(['make','test'],cwd=ref,check=True)
print('PASS diagnostic scope: all baseline files outside five explicitly reviewed integrations unchanged')
if '--test' in sys.argv:
 subprocess.run(['python3','tools/test-recovered-audio.py'],cwd=R,check=True)
 with tempfile.TemporaryDirectory() as d:
  exe=str(Path(d)/'startup')
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all','-Itests/wingsuit_audio_mock','-Itests/sound_mock','-Isrc','tests/e008_startup_test.c','-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
  s=(R/'tests/wingsuit_runtime_test.c').read_text().replace('"../src/wingsuit_runtime.c"','"'+str(R/'src/wingsuit_runtime.c')+'"')
  s=s.replace('unsigned short ws_vdp1','mf_ws_startup_trace mf_ws_startup_capture;\nunsigned short ws_vdp1')
  p=Path(d)/'runtime.c';p.write_text(s)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-Itests/wingsuit_mock','-Isrc',str(p),'src/wingsuit.c','-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
