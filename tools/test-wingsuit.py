#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parents[1]
subprocess.run(['python3','tools/audit-level2-audio-sdk.py'],cwd=R,check=True)
subprocess.run(['python3','tools/audit-level2-polyphony.py'],cwd=R,check=True)
subprocess.run(['python3','tools/validate-flame-tone.py'],cwd=R,check=True)
with tempfile.TemporaryDirectory(prefix='mf-wingsuit-') as tmp:
 for name,sources,includes in [
  ('aim',['tests/wingsuit_aim_test.c'],['-Isrc']),
  ('game',['tests/wingsuit_test.c','src/wingsuit.c'],['-Isrc']),
  ('flame',['tests/wingsuit_flame_test.c','src/wingsuit.c'],['-Isrc']),
  ('audio',['tests/wingsuit_audio_test.c'],['-Itests/wingsuit_audio_mock','-Itests/sound_mock','-Isrc']),
  ('weapons',['tests/wingsuit_weapon_test.c','src/wingsuit.c'],['-Isrc']),
  ('runtime-dev',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-DMF_DEV_STAGE_SKIP=1','-Itests/wingsuit_mock','-Isrc']),
  ('runtime',['tests/wingsuit_runtime_test.c','src/wingsuit.c'],['-Itests/wingsuit_mock','-Isrc'])]:
  exe=str(Path(tmp)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*includes,*sources,'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
subprocess.run(['python3','tools/test-flame-focus.py'],cwd=R,check=True)
subprocess.run(['python3','tools/validate-wingsuit.py'],cwd=R,check=True)
subprocess.run(['python3','tests/wingsuit_disc_test.py'],cwd=R,check=True)
subprocess.run(['python3','tests/hero_sprite_pass3_test.py'],cwd=R,check=True)
