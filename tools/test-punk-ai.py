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
  ('stage_clear',full),
  ('bat_command_buffer',full),
  ('punch_combo',['-DMF_PUNCH_COMBO=1','-DMF_FAST_RUNNING_BAT=1','-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('jab_repeat',['-DMF_JAB_COHESION=1','-DMF_RUN_BAT=1','-DMF_DASH_ENABLED=1']),
  ('dash',['-DMF_DASH_ENABLED=1']),('game',[]),('combat',[]),('coop',[]),('bat',[]),('air_bat',[]),('torch',[])]:
  exe=str(Path(d)/name)
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined','-fno-sanitize-recover=all',*flags,'-Isrc','tests/'+name+'_test.c',*(['src/game.c'] if name not in ('punk_ai','stage_clear') else []),'-o',exe],cwd=R,check=True)
  subprocess.run([exe],cwd=R,check=True)
