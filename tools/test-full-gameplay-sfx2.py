#!/usr/bin/env python3
"""Compare all gameplay state with the exact approved base, clearing only audio events."""
from pathlib import Path
import hashlib,subprocess,tempfile
r=Path(__file__).resolve().parents[1]
flags=['MF_PUNCH_COMBO','MF_FAST_RUNNING_BAT','MF_JAB_COHESION','MF_ATTACK_SEQUENCE','MF_BAT_MOMENTUM','MF_RUN_BAT','MF_DASH_ENABLED','MF_PLAYER_DEATH','MF_PLAYER_HURT','MF_HQ_JUMP','MF_HQ_TORCH','MF_COMBAT_ANIMATION','MF_PLAYABLE_ANIMATION','MF_RUNNING_BAT_VISUALS','MF_ORIGINAL_THREE_WALK']
with tempfile.TemporaryDirectory(prefix='mf-full-sfx2-') as d:
 p=Path(d);hashes=[]
 for label,source in [('base','tests/full_gameplay_sfx2_baseline/game.c'),('integrated','src/game.c')]:
  exe=p/label
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror',*[f'-D{f}=1' for f in flags],'-Isrc','tests/full_gameplay_sfx2_trace.c',source,'-o',str(exe)],cwd=r,check=True)
  with (p/(label+'.trace')).open('wb') as output:subprocess.run([str(exe)],cwd=r,stdout=output,check=True)
  hashes.append(hashlib.sha256((p/(label+'.trace')).read_bytes()).hexdigest())
 assert hashes[0]==hashes[1],hashes
 print('PASS full-gameplay SFX2: 16000 ticks of full-profile gameplay state match approved 60b7916 exactly after clearing audio events:',hashes[0])
