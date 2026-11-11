#!/usr/bin/env python3
from pathlib import Path
import json,subprocess,tempfile
R=Path(__file__).resolve().parents[1]
profile=json.loads((R/'assets/full-gameplay-sfx2/preservation.json').read_text())['profile_flags']
full=[f'-D{k}={17 if v=="B" else v}' for k,v in profile.items()]+['-DMF_LEVEL1_STAGE_CLEAR=1']
# Current Level1 logic: exercise approved fast-bat and unaffected legacy attacks.
with tempfile.TemporaryDirectory() as d:
 for name,flags in [
  ('punk_ai',full),
  ('punk_ai_v3',full),
  ('stage_clear',full),
  ('bat_command_buffer',full),
  ('punch_combo',['-DMF_PUNCH_COMBO=1','-DMF_FAST_RUNNING_BAT=1','-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('jab_repeat',['-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('dash',['-DMF_DASH_ENABLED=1']),('game',[]),('combat',[]),('coop',[]),('bat',[]),('air_bat',[]),('torch',[])]:
  exe=str(Path(d)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*flags,'-Isrc','tests/'+name+'_test.c',*(['src/game.c'] if name not in ('punk_ai','punk_ai_v3','stage_clear') else []),'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)

# Presentation uses the same approved poses with compressed enemy recovery.
with tempfile.TemporaryDirectory() as d:
 exe=str(Path(d)/'corporate')
 subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-DMF_CORPORATE_PUNK=1','-DMF_CORPORATE_REFINED=1','-DMF_CP_HQ_COMBAT=1','-Itests/animation_mock','-Isrc','tests/corporate_hq_test.c','src/corporate_animation.c','-o',exe],cwd=R,check=True)
 subprocess.run([exe],cwd=R,check=True)
