#!/usr/bin/env python3
"""Historical reference regressions plus tests of the recovered transport.

Old exact-source locks describe the pre-delivery source, not the approved binary.
Run them unchanged against their last source-complete reference; current code
has its own complete v3 delta lock and golden-resource/transport checks.
"""
from pathlib import Path
import subprocess,tempfile,tarfile,io,os
R=Path(__file__).resolve().parents[1]
subprocess.run(['python3','tools/validate-source-recovery.py'],cwd=R,check=True)
# actions/checkout defaults to depth 1. Fetch only the fixed public reference
# when absent; never interpolate the user-supplied source_ref into a shell.
reference='506d5f1762d1f70bbf8975b36c616c0fa5f54472'
if subprocess.run(['git','cat-file','-e',reference+'^{commit}'],cwd=R,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode:
 subprocess.run(['git','fetch','--no-tags','--depth=1','origin',reference],cwd=R,check=True)
subprocess.run(['git','cat-file','-e',reference+'^{commit}'],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='mf-reference-') as d:
 data=subprocess.check_output(['git','archive',reference],cwd=R)
 with tarfile.open(fileobj=io.BytesIO(data)) as t:t.extractall(d,filter='data')
 # SDK audit reads the same SHA-pinned SDK installed by setup.sh.
 (Path(d)/'.deps').symlink_to(R/'.deps',target_is_directory=True)
 print('Running historical reference make test; these are NOT recovered audio tests',flush=True)
 subprocess.run(['make','test'],cwd=d,check=True)
print('Running current recovered source transport with UBSan',flush=True)
subprocess.run(['python3','tools/test-recovered-audio.py'],cwd=R,check=True)
subprocess.run(['python3','tools/validate-fire-hit.py'],cwd=R,check=True)
subprocess.run(['python3','tools/audit-fire-hit-startup.py'],cwd=R,check=True)
# Every unchanged gameplay/runtime source is also compiled directly here.
with tempfile.TemporaryDirectory() as d:
 for name,sources,inc in [
  ('camera',['tests/wingsuit_camera_test.c','src/wingsuit.c'],['-Isrc']),
  ('turrets',['tests/wingsuit_turret_test.c'],['-Isrc']),
  ('patterns',['tests/wingsuit_patterns_test.c'],['-Isrc']),
  ('flame',['tests/wingsuit_flame_test.c','src/wingsuit.c'],['-Isrc']),
  ('runtime',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-Itests/wingsuit_mock','-Isrc']),
  ('runtime-dev',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-DMF_DEV_STAGE_SKIP=1','-Itests/wingsuit_mock','-Isrc'])]:
  exe=str(Path(d)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*inc,*sources,'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)

# Current Level1 logic: exercise approved fast-bat and unaffected legacy attacks.
with tempfile.TemporaryDirectory() as d:
 for name,flags in [
  ('bat_command_buffer',['-DMF_PUNCH_COMBO=1','-DMF_FAST_RUNNING_BAT=1','-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('punch_combo',['-DMF_PUNCH_COMBO=1','-DMF_FAST_RUNNING_BAT=1','-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('jab_repeat',['-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('dash',['-DMF_DASH_ENABLED=1']),('game',[]),('combat',[]),('coop',[]),('bat',[]),('air_bat',[]),('torch',[])]:
  exe=str(Path(d)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*flags,'-Isrc','tests/'+name+'_test.c','src/game.c','-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
